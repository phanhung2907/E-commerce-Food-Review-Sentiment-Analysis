import requests
from bs4 import BeautifulSoup
import time
import json
import os
from datetime import datetime
from pathlib import Path

def auto_collect_urls(category_url):
    print(f"Đang đi gom link tự động từ: {category_url}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(category_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        a_tags = soup.find_all('a', href=True)
        collected_urls = []
        
        for tag in a_tags:
            href = tag['href']
            # Bắt các link thuộc khu vực HCM và không lấy trùng
            if '/ho-chi-minh/' in href and href not in collected_urls:
                full_link = f"https://food.be.com.vn{href}" if href.startswith('/') else href
                collected_urls.append(full_link)
                
        print(f" -> Thu hoạch được {len(collected_urls)} link quán ăn!")
        return collected_urls
    except Exception as e:
        print(f"Lỗi khi gom link: {e}")
        return []

def crawl_befood_reviews(url_list):
    all_reviews = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    for url in url_list:
        print(f"Đang cào dữ liệu từ: {url}")
        try:
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Bóc tách nhanh một số thông tin từ URL của beFood
            # Ví dụ: https://food.be.com.vn/ho-chi-minh/bun-thit-nuong-22752
            city_str = url.split('.com.vn/')[1].split('/')[0] if '.com.vn/' in url else "Unknown"
            rest_id_str = url.split('-')[-1]
            rest_id = int(rest_id_str) if rest_id_str.isdigit() else None
            
            # Lấy tên nhà hàng từ thẻ h1 (thường nằm trên cùng của trang)
            h1_tag = soup.find('h1')
            restaurant_name = h1_tag.get_text(strip=True) if h1_tag else None

            # Quét danh sách các bình luận
            text_elements = soup.find_all('div', class_='text-gray-800 text-sm leading-snug')
            
            for el in text_elements:
                text = el.get_text(strip=True)
                if text:
                    # Tạo cấu trúc từ điển chuẩn 14 trường theo schema của nhóm
                    all_reviews.append({
                        "source": "beFood",
                        "restaurant_id": rest_id,
                        "restaurant_name": restaurant_name,
                        "restaurant_url": url,
                        "city": city_str,
                        "category": None, 
                        "total_reviews": None,
                        "restaurant_rating": None,
                        "review_id": None,
                        "reviewer_id": None,
                        "review_text": text,
                        "rating": None, 
                        "review_date": None,
                        "crawl_timestamp": datetime.now().isoformat()
                    })
                    
            print(f" -> Thu được {len(text_elements)} đánh giá (chuẩn 14 trường).")
            time.sleep(2)
            
        except Exception as e:
            print(f" Lỗi khi cào {url}: {e}")

    return all_reviews

def save_data(data):
    if not data:
        print("Không có dữ liệu để lưu.")
        return
        
    output_dir = Path("code/tuan/data/befood/raw/ho-chi-minh")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    file_path = output_dir / f"{date_str}.json"
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        
    print(f"\n Đã lưu đè thành công {len(data)} records tại: {file_path}")

if __name__ == "__main__":
    print("Bắt đầu tiến trình cào beFood...")
    
    # 1. Khai báo nhiều danh mục để vơ vét được lượng lớn quán ăn
    CATEGORY_LINKS = [
        "https://food.be.com.vn/collection/do-uong-228",
        "https://food.be.com.vn/collection/thuc-an-nhanh-230",
        "https://food.be.com.vn/collection/mon-a-au-231",
        "https://food.be.com.vn/collection/com-232",
        "https://food.be.com.vn/search?keyword=B%C3%A1nh+m%C3%AC",
        "https://food.be.com.vn/search?keyword=%C4%90%E1%BA%B7c+s%E1%BA%A3n",
        "https://food.be.com.vn/search?keyword=B%C3%A1nh+bao",
        "https://food.be.com.vn/search?keyword=G%C3%A0+r%C3%A1n",
        "https://food.be.com.vn/search?keyword=Pizza"
    ]
    
    urls_to_crawl = []
    # Đi quét từng danh mục và gom link lại
    for cat_link in CATEGORY_LINKS:
        urls = auto_collect_urls(cat_link)
        urls_to_crawl.extend(urls)
        time.sleep(2) # Nghỉ xíu giữa các trang danh mục
        
    # Lọc bỏ các link quán bị trùng lặp (nếu quán vừa bán cơm vừa bán trà sữa)
    urls_to_crawl = list(set(urls_to_crawl))
    print(f"\n=> TỔNG CỘNG ĐÃ GOM ĐƯỢC {len(urls_to_crawl)} QUÁN ĂN DUY NHẤT!\n")
    
    # 2. Cào đánh giá dựa trên danh sách URL khổng lồ vừa quét
    if urls_to_crawl:
        scraped_data = crawl_befood_reviews(urls_to_crawl)
        save_data(scraped_data)
    else:
        print("Không tìm thấy link quán ăn nào.")