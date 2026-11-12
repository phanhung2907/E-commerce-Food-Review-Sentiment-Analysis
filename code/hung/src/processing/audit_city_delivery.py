import sys,json,argparse
from pathlib import Path
root=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(root/'code/hung/src'))
from dotenv import load_dotenv
load_dotenv(root/'.env')
from storage.minio_client import create_minio_client,MINIO_BUCKET
from storage.raw_snapshots import freeze_object
from processing.foody_transform import transform_foody_object
from storage.postgres_client import create_postgres_connection
a=argparse.ArgumentParser();a.add_argument('--city',default='ho-chi-minh');args=a.parse_args()
client=create_minio_client();totals=dict(restaurants=0,raw_reviews=0,transformed_reviews=0,missing_minio=0,missing_restaurants=0,missing_reviews=0,content_mismatch=0)
files=list((root/'code/hung/data/foody_shoppefood/raw'/args.city).glob('*/restaurant.json'))
with create_postgres_connection() as c:
    c.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
    for p in files:
        raw=json.loads(p.read_text(encoding='utf-8'));rid=p.parent.name
        key=f'foody/raw/{args.city}/{rid}/restaurant.json'
        local=transform_foody_object(raw,key);totals['restaurants']+=1
        totals['raw_reviews']+=len(raw.get('reviews') or [])
        totals['transformed_reviews']+=len(local['reviews'])
        try:remote,prov=freeze_object('foody',key,client=client,persist=False)
        except Exception as e:
            if getattr(e,'code',None) in ('NoSuchKey','NoSuchObject'):totals['missing_minio']+=1;continue
            raise
        if remote!=raw:totals['content_mismatch']+=1
        dbrest=c.execute('SELECT city FROM restaurants WHERE source_code=%s AND source_restaurant_id=%s',('foody',rid)).fetchone()
        if not dbrest or dbrest[0]!=args.city:totals['missing_restaurants']+=1
        ids={x[0] for x in c.execute('SELECT source_review_id FROM reviews WHERE source_code=%s AND source_restaurant_id=%s',('foody',rid))}
        expected={x['source_review_id'] for x in local['reviews']}
        totals['missing_reviews']+=len(expected-ids)
print(json.dumps(totals))
if not files or any(totals[k] for k in ('missing_minio','missing_restaurants','missing_reviews','content_mismatch')):raise SystemExit(1)
