import requests
import json
import time
from bs4 import BeautifulSoup
from pathlib import Path
from datetime import datetime
import re

try:
    from langdetect import detect
except ImportError:
    pass

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "vi-VN,vi;q=0.9",
}

def clean_old_data():
    old_file = Path("code/tuan/data/befood/raw/befood_final_100.json")
    if old_file.exists():
        old_file.unlink()

def save_data(data):
    output_dir = Path("code/tuan/data/befood/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    out_name = f"befood_final_{len(data)}_{datetime.now().strftime('%Y%m%d')}.json"
    file_path = output_dir / out_name
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"\n[LƯU TRỮ] Đã ghi nhận {len(data)} records vào {file_path}")

def get_real_store_urls():
    print("[1/3] Bỏ qua quét tự động, sử dụng danh sách 3 URL nhập tay để vượt tường lửa...")
    
    urls_list = [
        "https://food.be.com.vn/ho-chi-minh/co-huong-bun-rieu-canh-bun-phan-boi-chau-88224",
        "https://food.be.com.vn/ho-chi-minh/ga-ran-va-my-y-jollibee-pasteur-9965",
        "https://food.be.com.vn/ho-chi-minh/ga-ran-popeyes-khanh-hoi-30467",
        "https://food.be.com.vn/ho-chi-minh/lotteria-tran-hung-dao-11634",
        "https://food.be.com.vn/ho-chi-minh/taka-cha-tra-sua-che-sau-rieng-huynh-thuc-khang-20385",
        "https://food.be.com.vn/ho-chi-minh/com-xa-xiu-thuong-hang-icom-duong-so-41-9204"

    ]
    
    print(f"[THÀNH CÔNG] Đã nạp sẵn {len(urls_list)} URL quán chất lượng để chuẩn bị bóc tách.")
    return urls_list

def crawl_store_reviews(url):
    try:
        res = requests.get(url, headers=HEADERS, timeout=8)
        # Ép chuẩn bảng mã UTF-8 để khắc phục dứt điểm lỗi font tiếng Việt
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
            # SỬA LỖI FONT (MOJIBAKE) DỨT ĐIỂM TẠI ĐÂY
            try:
                # 1. Ép chuỗi văn bản rác về dạng byte gốc bằng latin-1
                # 2. Giải mã ngược lại bằng utf-8 để trả về tiếng Việt chuẩn
                text = feedback_text.encode('latin-1').decode('utf-8').strip()
                
                # Dọn dẹp thêm các ký tự unicode escape lác đác (nếu có)
                text = text.encode('utf-8').decode('unicode_escape')
            except Exception:
                text = feedback_text.strip()
                
            if not text or text == "null":
                continue
                
            rating_val = float(rating_str)
            text_lower = text.lower()

            item = {
                "source": "beFood",
                "restaurant_id": store_id,
                "restaurant_name": store_name,
                "restaurant_url": url,
                "review_text": text,
                "rating": rating_val,
                "sentiment_label": "Positive" if rating_val >= 4 else ("Negative" if rating_val <= 2 else "Neutral"),
                "text_length": len(text),
                "word_count": len(text.split()),
                "exclamation_count": text.count('!'),
                "question_count": text.count('?'),
                "contains_emoji": bool(re.search(r'[^\w\s,.\-!?]', text)),
                "mention_delivery": bool(re.search(r'(shipper|giao|nhanh|chậm|tài xế|đợi)', text_lower)),
                "mention_price": bool(re.search(r'(giá|đắt|mắc|rẻ|tiền|kèm)', text_lower)),
                "mention_packaging": bool(re.search(r'(hộp|bao|bọc|đổ|tràn|nilon)', text_lower)),
                "crawled_at": datetime.now().isoformat()
            }
            records.append(item)
            
        return records
    except Exception as e:
        print(f"  -> [LỖI] {e}")
        return []
def main():
    clean_old_data()
    final_data = []
    target = 100
    
    store_urls = get_real_store_urls()
    if not store_urls:
        print("Không có URL nào để quét!")
        return

    print(f"\n[2/3] Bắt đầu bóc tách review tuần tự từ {len(store_urls)} URL (Mục tiêu: {target} records)...")
    
    for index, url in enumerate(store_urls):
        if len(final_data) >= target:
            break
            
        print(f"[*] Đang cào quán {index+1}/{len(store_urls)}... | Đã gom: {len(final_data)}/{target}", end='\r')
        reviews = crawl_store_reviews(url)
        
        if reviews:
            final_data.extend(reviews)
            print(f"\n  -> [THÀNH CÔNG] Thu được {len(reviews)} review từ quán này. Tổng: {len(final_data)}/{target}")
            
        time.sleep(2) 
        
    final_data = final_data[:target]
    save_data(final_data)
    print(f"🏆 Hoàn tất! Đã lưu thành công dữ liệu sạch theo đúng cấu trúc của dự án.")

if __name__ == "__main__":
    main()