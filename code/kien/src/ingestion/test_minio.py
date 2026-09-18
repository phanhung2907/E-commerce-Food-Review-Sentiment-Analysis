import os
import json
from io import BytesIO

from dotenv import load_dotenv
from minio import Minio

load_dotenv()

client = Minio(
    os.getenv("MINIO_ENDPOINT"),
    access_key=os.getenv("MINIO_ACCESS_KEY"),
    secret_key=os.getenv("MINIO_SECRET_KEY"),
    secure=False,
)

data = {
    "source": "test",
    "restaurant_id": 1,
    "rating": 5,
    "review_text": "MinIO connection test",
}

json_bytes = json.dumps(
    data,
    ensure_ascii=False,
    indent=2,
).encode("utf-8")

client.put_object(
    bucket_name=os.getenv("MINIO_BUCKET"),
    object_name="raw/test/test_env.json",
    data=BytesIO(json_bytes),
    length=len(json_bytes),
    content_type="application/json",
)

print("Upload successful")