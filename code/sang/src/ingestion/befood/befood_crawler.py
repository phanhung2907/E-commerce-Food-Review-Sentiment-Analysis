import json
import re
import time
import logging
import requests
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

CURRENT_FILE = Path(__file__).resolve()
SANG_DIR = CURRENT_FILE.parents[3]
CRAWL_DATE = datetime.now().strftime("%Y-%m-%d")
RAW_DATA_DIR = SANG_DIR / "data" / "befood" / "raw" / "ho-chi-minh"
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = RAW_DATA_DIR / f"{CRAWL_DATE}.json"

# Danh sách một số quán lớn để cào nhanh đúng 100 sample records
TARGET_STORES = [
    ("the-pizza-company-le-van-sy-2849", "The Pizza Company - Lê Văn Sỹ"),
    ("pizza-paolo-nguyen-trai-10216", "Pizza Paolo - Nguyễn Trãi"),
    ("kfc-lay-huong-2850", "KFC - Lũy Bán Bích"),
    ("lotteria-nguyen-nguyen-2851", "Lotteria - Nguyễn Thị Thập")
]

def decode_unicode(text):
    try:
        return text.encode('utf-8').decode('unicode-escape').encode('latin1').decode('utf-8')
    except Exception:
        return text

def run_befood_crawler_100_records():
    logging.info("🚀 Đang cào đúng 100 records mẫu THẬT 100%...")
    
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'RSC': '1'
    }
    
    data = []
    record_count = 1
    TARGET_LIMIT = 100

    for store_id, store_name in TARGET_STORES:
        if len(data) >= TARGET_LIMIT:
            break
            
        url = f"https://food.be.com.vn/ho-chi-minh/{store_id}?_rsc=3t0"
        
        try:
            res = session.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                raw_text = res.text
                
                comments = (
                    re.findall(r'"comment"\s*:\s*"([^"]+)"', raw_text) or 
                    re.findall(r'"review"\s*:\s*"([^"]+)"', raw_text) or
                    re.findall(r'"content"\s*:\s*"([^"]+)"', raw_text)
                )
                ratings = re.findall(r'"rating"\s*:\s*(\d+(?:\.\d+)?)', raw_text)

                for i, c in enumerate(comments):
                    if len(data) >= TARGET_LIMIT:
                        break
                        
                    if c.startswith("http") or "Đặt món" in c or "Xem menu" in c or len(c.strip()) < 2:
                        continue
                    
                    clean_comment = decode_unicode(c)
                    rating_val = float(ratings[i]) if i < len(ratings) else None

                    data.append({
                        "id": f"befood_rec_{record_count:06d}",
                        "platform": "beFood",
                        "endpoint_source": url,
                        "store_id": store_id,
                        "store_name": store_name,
                        "user_name": None,          # 100% Không fake tên
                        "rating": rating_val,        # Rating thật hoặc null
                        "comment": clean_comment,   # Comment tiếng Việt thật
                        "sentiment": None,
                        "created_at": None,         # 100% Không fake ngày
                        "crawl_timestamp": datetime.now().isoformat(),
                        "location": "Ho Chi Minh City",
                        "city": "ho-chi-minh"
                    })
                    record_count += 1

        except Exception as e:
            logging.error(f"❌ Lỗi: {e}")
        
        time.sleep(0.5)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    logging.info(f"🎉 Đã xong! Lấy thành công {len(data)} records chuẩn sạch tại: {OUTPUT_FILE}")

if __name__ == '__main__':
    run_befood_crawler_100_records()