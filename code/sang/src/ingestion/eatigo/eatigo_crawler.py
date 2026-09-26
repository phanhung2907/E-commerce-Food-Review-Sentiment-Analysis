import json
from pathlib import Path
import time
import requests

def fetch_product_tags(product_id: str, headers: dict) -> dict:
    tags_url = f"https://eatigo.com/v2/eatigo/product/{product_id}/review-tags-count"
    try:
        res = requests.get(tags_url, headers=headers, timeout=5)
        if res.status_code == 200:
            return res.json().get("data", {})
    except Exception:
        pass
    return {}

def crawl_eatigo_raw_dict(product_ids: list, total_target: int = 100000):
    all_records = []
    
    output_dir = Path("code/sang/data/raw/eatigo")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "eatigo_raw_objects_final.json"
    
    print(f"🚀 Bắt đầu crawl dữ liệu dưới dạng Python Dict Object nguyên bản...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest"
    }
    
    for idx, product_id in enumerate(product_ids):
        if len(all_records) >= total_target:
            break
            
        product_tags_summary = fetch_product_tags(product_id, headers)
        comments_url = f"https://eatigo.com/v2/eatigo/product/{product_id}/comments"
        start = 0
        size = 50  
        
        print(f"📍 [{idx+1}/{len(product_ids)}] Đang crawl product_id: {product_id}")
        
        while len(all_records) < total_target:
            params = {"start": start, "size": size, "sortby": "default"}
            
            try:
                response = requests.get(comments_url, params=params, headers=headers, timeout=10)
                if response.status_code != 200:
                    break
                    
                response_data = response.json()
                inner_data = response_data.get("data", {})
                comments = inner_data.get("comments", [])
                
                if not comments:
                    print(f"   ✅ Đã lấy hết review của product_id {product_id}.")
                    break
                
                # YÊU CẦU: Không bóc tách key-value lẻ tẻ, giữ nguyên bản object dict từ API
                for item in comments:
                    if len(all_records) >= total_target:
                        break
                        
                    raw_object_record = {
                        "product_id": product_id,
                        "restaurant_tags_raw": product_tags_summary, # Giữ nguyên dict tags
                        "comment_container_raw": inner_data,       # Giữ nguyên toàn bộ dict chứa thông tin chung
                        "review_item_raw": item                    # Giữ nguyên toàn bộ dict nguyên bản của từng bình luận
                    }
                    all_records.append(raw_object_record)
                
                print(f"   📥 Tổng tích lũy hệ thống: {len(all_records)} / {total_target}")
                
                start += size
                time.sleep(0.5) 
                
                if len(comments) < size:
                    break
                    
            except Exception as e:
                print(f"   ❌ Lỗi kết nối tại product_id {product_id}: {e}")
                break
        
        # Lưu checkpoint sau mỗi nhà hàng
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_records, f, ensure_ascii=False, indent=4)
            
    print(f"\n✨ Hoàn tất! Đã lưu {len(all_records)} records dạng raw object vào: {output_file}")

if __name__ == "__main__":
    sample_product_ids = [
        "3644620907182",
        "3647373326207"
    ]
    crawl_eatigo_raw_dict(product_ids=sample_product_ids, total_target=1000)