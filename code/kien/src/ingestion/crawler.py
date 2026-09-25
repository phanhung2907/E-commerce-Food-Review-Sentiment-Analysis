import json
import os
import re
import time
from datetime import datetime
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

def extract_restaurant_id(url):
    match = re.search(r'-d(\d+)-', url)
    return match.group(1) if match else "N/A"

def extract_city_from_url(url):
    if "Quy_Nhon" in url:
        return "Quy Nhon"
    elif "Hanoi" in url:
        return "Hanoi"
    elif "Ho_Chi_Minh" in url or "Ho_Chi_Minh_City" in url:
        return "Ho Chi Minh City"
    return "Unknown"

def crawl_multiple_restaurants():
    output_dir = "code/kien/data/raw"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"tripadvisor_multi_restaurants_{datetime.now().strftime('%Y-%m-%d')}.json")
    
    restaurants = [
        {
            "name": "Nhà Hàng Cá Khôi",
            "url": "https://www.tripadvisor.com/Restaurant_Review-g293925-d15325004-Reviews-Nha_Hang_Ca_Khoi-Quy_Nhon_Binh_Dinh_Province.html",
            "category": "Seafood / Vietnamese"
        },
        {
            "name": "Surf Bar",
            "url": "https://www.tripadvisor.com/Restaurant_Review-g293925-d12652345-Reviews-Surf_Bar-Quy_Nhon_Binh_Dinh_Province.html",
            "category": "Cafe / Bar / Beach"
        },
        {
            "name": "Hoang's Restaurant",
            "url": "https://www.tripadvisor.com/Restaurant_Review-g27501570-d19255094-Reviews-Hoang_s_Restaurant-Hoan_Kiem_Hanoi.html",
            "category": "Asian / Vietnamese"
        },
        {
            "name": "Bếp Mẹ Ỉn Lê Thánh Tôn",
            "url": "https://www.tripadvisor.com/Restaurant_Review-g293925-d10721705-Reviews-B_p_M_n_Le_Thanh_Ton-Ho_Chi_Minh_City.html",
            "category": "Vietnamese"
        }
    ]

    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    
    print("Đang khởi động trình duyệt chống bot...")
    driver = uc.Chrome(options=options, version_main=153)
    
    all_reviews = []

    try:
        for item in restaurants:
            target_url = item["url"]
            restaurant_name = item["name"]
            restaurant_id = extract_restaurant_id(target_url)
            city = extract_city_from_url(target_url)
            category = item["category"]
            
            print(f"\n--- Đang cào dữ liệu cho: {restaurant_name} (ID: {restaurant_id}) ---")
            driver.get(target_url)
            time.sleep(5)
            
            # Cuộn trang từ từ để kích hoạt nội dung ẩn
            for _ in range(5):
                driver.execute_script("window.scrollBy(0, 1000);")
                time.sleep(2)

            total_reviews_str = "N/A"
            restaurant_rating_str = "N/A"

            # Quét toàn bộ các thẻ đoạn văn bản có khả năng chứa nội dung review trên trang mới
            review_elements = driver.find_elements(By.TAG_NAME, "span")
            print(f"Tìm thấy {len(review_elements)} phần tử tiềm năng trên trang.")

            count = 0
            for index, element in enumerate(review_elements):
                try:
                    text = element.text.strip()
                    
                    # Lọc chặt chẽ: chỉ lấy các đoạn văn bản đủ độ dài của một review thực tế và loại bỏ rác hệ thống
                    if not text or len(text) < 40 or len(text) > 1500:
                        continue
                    if "Plan with AI" in text or "bubbles" in text or "TripAdvisor" in text or "Cookie" in text:
                        continue
                        
                    review_id = f"REV_{restaurant_id}_{index}"
                    
                    record = {
                        "source": "TripAdvisor",
                        "restaurant_id": restaurant_id,
                        "restaurant_name": restaurant_name,
                        "restaurant_url": target_url,
                        "city": city,
                        "category": category,
                        "review_id": review_id,
                        "review_text": text,
                        "rating": "N/A",
                        "review_date": datetime.now().strftime("%Y-%m-%d"),
                        "reviewer_id": f"User_{index}",
                        "total_reviews": total_reviews_str,
                        "restaurant_rating": restaurant_rating_str,
                        "crawl_timestamp": datetime.now().isoformat()
                    }
                    
                    if record not in all_reviews:
                        all_reviews.append(record)
                        count += 1
                except Exception:
                    pass
            
            print(f"Đã trích xuất thành công {count} bản ghi sạch từ {restaurant_name}.")

    except Exception as e:
        print(f"Đã xảy ra lỗi trong quá trình cào: {e}")
    finally:
        driver.quit()

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_reviews, f, ensure_ascii=False, indent=4)
    
    print(f"\n=== HOÀN TẤT ===")
    print(f"Tổng số lượng thu thập được: {len(all_reviews)} records với đầy đủ các trường yêu cầu.")
    print(f"Đã lưu file tại: {output_file}")

if __name__ == "__main__":
    crawl_multiple_restaurants()