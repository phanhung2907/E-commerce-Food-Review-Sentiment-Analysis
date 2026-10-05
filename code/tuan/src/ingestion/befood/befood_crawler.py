import requests
import json
import time
import random
import hashlib
import concurrent.futures
from pathlib import Path
from datetime import datetime
import re
import unicodedata

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "vi-VN,vi;q=0.9",
    "Content-Type": "application/json",
    "Origin": "https://food.be.com.vn",
    "Referer": "https://food.be.com.vn/",
    "Connection": "keep-alive",
    "Cookie": "bfv2_did=web-542bcb1c39434c46; _tt_enable_cookie=1; _ttp=01M3981EJ6708S9CJ66E0X3RJY_.tt.2.1790238046790; _ga=GA1.1.1930718224.1790238048; _ga_6BN02F6R47=GS2.1.s1791127574$o10$g1$t1791127579$j55$l0$h0; ttcsid_D9VESVRC77U9J4MAPLO0=1791127578816::Zax31vSLTKrZYFzypd5k.8.1791127589932.1; ttcsid=1791127572483::qZSLqp7CEGx27nOqQR6D.9.1791127589929.0::1.1452.6335::307103.4.259.476::23342.126.22"
}

def load_existing_reviews():
    """Đọc TẤT CẢ các file JSON cũ trong thư mục raw để lập màng lọc chống trùng lặp tuyệt đối"""
    existing_signatures = set()
    raw_dir = Path("code/tuan/data/befood/raw")
    
    if raw_dir.exists():
        for old_file in raw_dir.glob("*.json"):
            try:
                with open(old_file, 'r', encoding='utf-8') as f:
                    old_data = json.load(f)
                    for item in old_data:
                        # Dựa vào review_id hoặc kết hợp restaurant_id và review_text để lọc trùng sạch sẽ
                        review_id = item.get("review_id")
                        if review_id:
                            existing_signatures.add(review_id)
                        else:
                            signature = f"{item.get('restaurant_id')}_{str(item.get('review_text', '')).strip().lower()}"
                            existing_signatures.add(signature)
            except Exception:
                pass
                
    print(f"[HỆ THỐNG MÀNG LỌC] Đã nạp thành công các bản ghi cũ để chống trùng lặp dữ liệu.")
    return existing_signatures

def save_data(data):
    if not data:
        print("\n[THÔNG BÁO] Không có bình luận mới nào phát sinh sau khi lọc trùng.")
        return
        
    output_dir = Path("code/tuan/data/befood/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    out_name = f"befood_final_{len(data)}_new_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    file_path = output_dir / out_name
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"\n[LƯU TRỮ THÀNH CÔNG] Đã ghi nhận thêm {len(data)} records THẬT vào {file_path}")

def get_automated_store_urls(session):
    """HÀM MASTER: Phân trang API POST có tích hợp Debug JSON Thô để bắt chính xác key từ server"""
    print("[1/3] HÀM MASTER: Đang kết nối API POST để vét cạn toàn bộ nhà hàng thật...")
    urls_list = []
    
    collection_ids = ["230", "231", "232"]
    
    for coll_id in collection_ids:
        page = 1
        print(f" -> Đang quét bộ sưu tập ID: {coll_id}...")
        
        while True:
            api_url = f"https://food.be.com.vn/api/v1/collections/{coll_id}/restaurants"
            payload = {
                "page": page,
                "limit": 12,
                "filters": []
            }
            
            try:
                response = session.post(api_url, headers=HEADERS, json=payload, timeout=10)
                
                if response.status_code != 200:
                    break
                    
                json_data = response.json()
                
                # TÍCH HỢP CƠ CHẾ DEBUG JSON THÔ (In cấu trúc khóa mẫu ở trang đầu tiên)
                if page == 1:
                    print(f"\n[DEBUG JSON THÔ] Cấu trúc phản hồi gốc từ Collection {coll_id}:")
                    if isinstance(json_data, dict):
                        print(f" - Các khóa cấp 1 (Keys): {list(json_data.keys())}")
                        if 'data' in json_data:
                            print(f" - Kiểu dữ liệu của khóa 'data': {type(json_data['data'])}, Nội dung sơ bộ: {str(json_data['data'])[:150]}...")
                    elif isinstance(json_data, list):
                        print(f" - Phản hồi là danh sách (List) với tổng số phần tử: {len(json_data)}")
                        if len(json_data) > 0:
                            print(f" - Cấu trúc phần tử đầu tiên: {list(json_data[0].keys()) if isinstance(json_data[0], dict) else type(json_data[0])}")
                    print("-" * 50)

                restaurants = []
                if isinstance(json_data, list):
                    restaurants = json_data
                elif isinstance(json_data, dict):
                    # Quét vét cạn mọi nhánh chứa danh sách quán
                    for key in ['data', 'items', 'restaurants', 'list', 'result']:
                        val = json_data.get(key)
                        if isinstance(val, list):
                            restaurants = val
                            break
                        elif isinstance(val, dict):
                            for sub_key in ['items', 'restaurants', 'list', 'data']:
                                sub_val = val.get(sub_key)
                                if isinstance(sub_val, list):
                                    restaurants = sub_val
                                    break
                            if restaurants:
                                break
                
                if not restaurants:
                    break 
                    
                for item in restaurants:
                    if not isinstance(item, dict):
                        continue
                        
                    # Lấy ID quán chuẩn xác
                    store_id = None
                    for k in ['id', 'restaurant_id', 'restaurantId', 'store_id', 'storeId', '_id', 'uuid']:
                        if k in item and item[k]:
                            store_id = str(item[k])
                            break
                    
                    # Lấy Slug hoặc tự sinh chuẩn từ tên quán
                    slug = None
                    for k in ['alias', 'slug', 'code', 'restaurant_slug', 'restaurantSlug']:
                        if k in item and item[k]:
                            slug = str(item[k])
                            break
                            
                    if not slug and (item.get('name') or item.get('restaurant_name') or item.get('title')):
                        raw_name = str(item.get('name') or item.get('restaurant_name') or item.get('title'))
                        slug = re.sub(r'[^a-zA-Z0-9]+', '-', unicodedata.normalize('NFD', raw_name).encode('ascii', 'ignore').decode('utf-8')).lower().strip('-')
                    
                    if store_id and slug:
                        full_url = f"https://food.be.com.vn/ho-chi-minh/{slug}-{store_id}"
                        if full_url not in urls_list:
                            urls_list.append(full_url)
                
                print(f"    + Quét trang {page} | Tổng link quán thật gom được: {len(urls_list)}...", end='\r')
                
                if len(restaurants) < 12:
                    break
                    
                page += 1
                time.sleep(random.uniform(0.3, 0.7))
                
            except Exception as e:
                break
                
    print(f"\n[THÀNH CÔNG] Master đã vét cạn và gom được tổng cộng {len(urls_list)} đường dẫn nhà hàng thật.")
    return urls_list

def crawl_store_reviews(url, existing_signatures, session):
    """HÀM WORKER: Bóc tách đánh giá thực tế từ trang HTML của từng quán"""
    html_headers = HEADERS.copy()
    html_headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    
    try:
        res = session.get(url, headers=html_headers, timeout=12)
        res.encoding = 'utf-8' 
        
        if res.status_code != 200:
            return []
            
        clean_html = res.text.replace('\\"', '"')
        pattern = r'"rating":([0-9.]+),"feedback":"(.*?)"'
        matches = re.findall(pattern, clean_html)
        
        unique_reviews = list(set(matches))
        
        url_slug = url.split('/')[-1]
        store_id = url_slug.split('-')[-1] 
        store_name = url_slug.rsplit('-', 1)[0].replace('-', ' ').title()
        
        records = []
        for rating_str, feedback_text in unique_reviews:
            try:
                text = feedback_text.encode('latin-1').decode('utf-8').strip()
                text = text.encode('utf-8').decode('unicode_escape')
            except Exception:
                text = feedback_text.strip()
                
            if not text or text == "null":
                continue
                
            review_id = hashlib.md5(f"{store_id}_{text.strip().lower()}".encode('utf-8')).hexdigest()
            
            # Kiểm tra chống trùng lặp tuyệt đối với dữ liệu từ các file trước
            if review_id in existing_signatures or f"{store_id}_{text.strip().lower()}" in existing_signatures:
                continue 
                
            rating_val = float(rating_str)
            text_lower = text.lower()

            item = {
                "source": "BeFood",
                "restaurant_id": store_id,
                "restaurant_name": store_name,
                "restaurant_url": url,
                "city": "Ho Chi Minh",
                "category": "Thức Ăn Nhanh",
                "review_id": review_id,
                "reviewer_id": "Ẩn danh",
                "review_text": text,
                "language": "vi",
                "rating": rating_val,
                "sentiment_label": "Positive" if rating_val >= 4 else ("Negative" if rating_val <= 2 else "Neutral"),
                "review_date": None,
                "crawl_timestamp": datetime.now().isoformat(),
                "is_detailed_review": bool(len(text) >= 30),
                "contains_emoji": bool(re.search(r'[^\w\s,.\-!?]', text)),
                "aspect_price": bool(re.search(r'(giá|đắt|mắc|rẻ|tiền|kèm|hợp lý)', text_lower)),
                "aspect_delivery": bool(re.search(r'(shipper|giao|nhanh|chậm|tài xế|đợi)', text_lower)),
                "aspect_packaging": bool(re.search(r'(hộp|bao|bọc|đổ|tràn|nilon|sạch|dơ)', text_lower))
            }
            records.append(item)
            
        time.sleep(random.uniform(0.4, 0.8))
        return records
    except Exception:
        return []

def main():
    existing_signatures = load_existing_reviews()
    final_data = []
    
    with requests.Session() as session:
        store_urls = get_automated_store_urls(session)
        if not store_urls:
            print("\n[THÔNG BÁO] Không thu thập được đường link nhà hàng nào.")
            return

        print(f"\n[2/3] WORKER: Bắt đầu bóc tách đánh giá thực tế từ {len(store_urls)} quán (Chạy đa luồng siêu tốc)...")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_url = {executor.submit(crawl_store_reviews, url, existing_signatures, session): url for url in store_urls}
            
            completed = 0
            for future in concurrent.futures.as_completed(future_to_url):
                completed += 1
                reviews = future.result()
                if reviews:
                    final_data.extend(reviews)
                print(f"[*] Đã xử lý {completed}/{len(store_urls)} quán... | Thu thập mới: {len(final_data)} records", end='\r')

    print(f"\n\n[3/3] Tiến hành lưu trữ dữ liệu...")
    save_data(final_data)
    print(f"🏆 Hoàn tất! Hệ thống đã tự động vét cạn toàn bộ nhà hàng 100% từ server thật.")

if __name__ == "__main__":
    main()