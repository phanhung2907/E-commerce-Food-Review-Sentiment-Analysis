import json
from pathlib import Path
import time
import requests

def fetch_product_tags(product_id: str, headers: dict) -> dict:
    """Lấy dữ liệu thống kê review-tags-count cho sản phẩm"""
    tags_url = f"https://eatigo.com/v2/eatigo/product/{product_id}/review-tags-count"
    try:
        res = requests.get(tags_url, headers=headers, timeout=5)
        if res.status_code == 200:
            return res.json().get("data", {})
    except Exception:
        pass
    return {}

def crawl_eatigo_100k(product_ids: list, total_target: int = 100000):
    all_records = []
    
    output_dir = Path("code/sang/data/raw/eatigo")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "eatigo_raw_100k_final.json"
    
    print(f"🚀 [Eatigo 100k Scale Crawler] Bắt đầu chiến dịch thu thập mục tiêu: {total_target} records")
    print(f"📂 Tổng số lượng product_id cần quét: {len(product_ids)}\n")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest"
    }
    
    for idx, product_id in enumerate(product_ids):
        if len(all_records) >= total_target:
            print(f"🎯 Đã hoàn thành mục tiêu đạt {len(all_records)} records!")
            break
            
        # Lấy thêm thông tin thống kê tags của nhà hàng này
        product_tags_summary = fetch_product_tags(product_id, headers)
        
        comments_url = f"https://eatigo.com/v2/eatigo/product/{product_id}/comments"
        start = 0
        size = 50  
        
        print(f"📍 [{idx+1}/{len(product_ids)}] Đang crawl product_id: {product_id}")
        
        while len(all_records) < total_target:
            params = {
                "start": start,
                "size": size,
                "sortby": "default"
            }
            
            try:
                response = requests.get(comments_url, params=params, headers=headers, timeout=10)
                if response.status_code != 200:
                    print(f"   ⚠️ Không thể truy cập comments (Status: {response.status_code}). Chuyển ID tiếp theo.")
                    break
                    
                response_data = response.json()
                inner_data = response_data.get("data", {})
                comments = inner_data.get("comments", [])
                
                if not comments:
                    print(f"   ✅ Đã lấy hết review của product_id {product_id}.")
                    break
                    
                for item in comments:
                    if len(all_records) >= total_target:
                        break
                        
                    standardized_record = {
                        "review_id": item.get("id"),
                        "review_text": item.get("description"),
                        "rating_star": item.get("rating"),
                        "timestamp": item.get("comment_time"),
                        "reviewer_metadata": item.get("rated_by"),
                        "reaction_likes": {
                            "is_like": item.get("is_like"),
                            "like_count": item.get("like_count")
                        },
                        "tags": item.get("tags", []),
                        "image_metadata": item.get("images", []),
                        "source_platform": item.get("source", "eatigo"),

                        "restaurant_info": {
                            "product_id": product_id,
                            "location": inner_data.get("location", "N/A"),          # Thêm trường location
                            "category_cuisine": inner_data.get("cuisine", "N/A"),   # Thêm trường category/cuisine
                            "avg_rating": inner_data.get("avg_rating"),
                            "total_count": inner_data.get("total_count"),
                            "review_tags_summary": product_tags_summary
                        },
                        "raw_original_fields": item 
                    }
                    all_records.append(standardized_record)
                
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
            
    print(f"\n✨ Hoàn tất toàn bộ chiến dịch! Đã lưu tổng cộng {len(all_records)} records vào: {output_file}")

if __name__ == "__main__":
    sample_product_ids = [
        "3644620907182",
        "3647373326207", # Quán thứ hai 
        "3647373326207",
        # Thêm các product_id khác vào đây để tích lũy đủ 100k data
    ]
    
    crawl_eatigo_100k(product_ids=sample_product_ids, total_target=100000)