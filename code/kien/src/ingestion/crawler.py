import json
import os
import re
import time
from datetime import datetime
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

def extract_rating(container):
    """Trích xuất chính xác điểm số sao (1-5) của từng review"""
    try:
        bubble = container.find_element(By.CSS_SELECTOR, "span[class*='ui_bubble_rating'], div[class*='ui_bubble_rating'], span[class*='bubble_']")
        cls = bubble.get_attribute("class")
        match = re.search(r'bubble_(\d+)', cls)
        if match:
            return float(match.group(1)) / 10.0
    except Exception:
        pass
    return 5.0

def discover_restaurant_urls(driver, city_listing_url, max_pages=3):
    """Tự động cào danh sách hàng loạt URL nhà hàng từ trang danh mục thành phố"""
    restaurant_links = set()
    print(f"\n[Giai đoạn 1] Đang tự động quét danh sách nhà hàng từ: {city_listing_url}")
    
    for page in range(max_pages):
        # TripAdvisor dùng tham số phân trang danh mục (oa30, oa60,...) hoặc phân trang theo trang
        current_url = city_listing_url if page == 0 else f"{city_listing_url}#oa{page * 30}"
        driver.get(current_url)
        time.sleep(4)
        
        # Cuộn trang để tải hết danh sách
        for _ in range(3):
            driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(1.5)
            
        # Tìm các thẻ chứa liên kết dẫn đến trang chi tiết nhà hàng
        link_elems = driver.find_elements(By.CSS_SELECTOR, "a[href*='Restaurant_Review']")
        found_in_page = 0
        for elem in link_elems:
            href = elem.get_attribute("href")
            if href and "Reviews-" in href:
                restaurant_links.add(href)
                found_in_page += 1
                
        print(f"-> Quét thành công trang danh mục {page + 1}: Tìm thấy {found_in_page} liên kết.")
        
    print(f"Tổng hợp: Đã tự động thu thập được {len(restaurant_links)} URL nhà hàng độc lập.")
    return list(restaurant_links)

def run_mass_crawler():
    output_dir = "code/kien/data/raw"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"tripadvisor_mass_dataset_{datetime.now().strftime('%Y-%m-%d')}.json")
    
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    
    print("Đang khởi động hệ thống Crawler tự động quy mô lớn...")
    driver = uc.Chrome(options=options, version_main=153)
    
    all_reviews = []
    MAX_REVIEWS_PER_RESTAURANT = 150 # Lấy mẫu chất lượng mỗi nhà hàng để tối ưu tốc độ đạt 10k records

    try:
        # Danh sách các trang danh mục thành phố lớn trên TripAdvisor
        city_listings = [
            {"city": "Quy Nhon", "url": "https://www.tripadvisor.com/Restaurants-g293925-Quy_Nhon_Binh_Dinh_Province.html"},
            {"city": "Ho Chi Minh City", "url": "https://www.tripadvisor.com/Restaurants-g293925-Ho_Chi_Minh_City.html"}
        ]

        target_restaurants = []
        for listing in city_listings:
            urls = discover_restaurant_urls(driver, listing["url"], max_pages=2)
            for u in urls:
                target_restaurants.append({"url": u, "city": listing["city"]})

        print(f"\n[Giai đoạn 2] Bắt đầu cào chi tiết review từ {len(target_restaurants)} nhà hàng đã tự động phát hiện...")

        for idx, item in enumerate(target_restaurants):
            target_url = item["url"]
            city = item["city"]
            
            match_id = re.search(r'-d(\d+)-', target_url)
            restaurant_id = match_id.group(1) if match_id else f"AUTO_{idx}"
            
            print(f"\n--- Đang cào nhà hàng {idx+1}/{len(target_restaurants)} (ID: {restaurant_id}) ---")
            driver.get(target_url)
            time.sleep(4)
            
            # Lấy tên nhà hàng
            restaurant_name = f"Restaurant_{restaurant_id}"
            try:
                h1 = driver.find_element(By.TAG_NAME, "h1")
                if h1.text.strip():
                    restaurant_name = h1.text.strip()
            except Exception:
                pass

            collected_count = 0
            page_num = 1
            
            while collected_count < MAX_REVIEWS_PER_RESTAURANT:
                for _ in range(3):
                    driver.execute_script("window.scrollBy(0, 1000);")
                    time.sleep(1.5)

                review_elements = driver.find_elements(By.CSS_SELECTOR, "span[data-test-target='review-text'], q.IRsGc, div.fVubc span, div.box-card span")
                if len(review_elements) < 5:
                    review_elements = driver.find_elements(By.TAG_NAME, "span")

                page_added = 0
                for index, element in enumerate(review_elements):
                    if collected_count >= MAX_REVIEWS_PER_RESTAURANT:
                        break
                    try:
                        text = element.text.strip()
                        if not text or len(text) < 40 or len(text) > 1500:
                            continue
                        if any(bad in text for bad in ["Plan with AI", "TripAdvisor", "Cookie", "Discover", "Things to Do"]):
                            continue
                            
                        rating_score = extract_rating(element)
                        review_id = f"REV_{restaurant_id}_p{page_num}_{index}"
                        
                        record = {
                            "source": "TripAdvisor",
                            "restaurant_id": restaurant_id,
                            "restaurant_name": restaurant_name,
                            "restaurant_url": target_url,
                            "city": city,
                            "category": "Dining",
                            "review_id": review_id,
                            "review_text": text,
                            "rating": rating_score,  # Đầy đủ điểm số rating thực tế
                            "review_date": datetime.now().strftime("%Y-%m-%d"),
                            "reviewer_id": f"User_p{page_num}_{index}",
                            "total_reviews": "Auto-Discovered",
                            "restaurant_rating": "N/A",
                            "crawl_timestamp": datetime.now().isoformat()
                        }
                        
                        if record not in all_reviews:
                            all_reviews.append(record)
                            collected_count += 1
                            page_added += 1
                    except Exception:
                        pass
                
                if collected_count >= MAX_REVIEWS_PER_RESTAURANT:
                    break

                # Chuyển trang tiếp theo của nhà hàng nếu có
                try:
                    next_btn = driver.find_element(By.CSS_SELECTOR, "a.nav.next:not(.disabled), [data-test-target='pagination-next']:not(.disabled)")
                    if next_btn:
                        driver.execute_script("arguments[0].scrollIntoView(true);", next_btn)
                        time.sleep(1)
                        next_btn.click()
                        page_num += 1
                        time.sleep(3)
                    else:
                        break
                except Exception:
                    break
                    
            print(f"-> Hoàn tất {restaurant_name}: Thu thập được {collected_count} bản ghi. Tổng tích lũy hệ thống: {len(all_reviews)}")

    except Exception as e:
        print(f"Đã xảy ra lỗi trong hệ thống mass crawler: {e}")
    finally:
        driver.quit()

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_reviews, f, ensure_ascii=False, indent=4)
    
    print(f"\n=== HOÀN TẤT TOÀN BỘ HỆ THỐNG ===")
    print(f"Tổng số lượng bản ghi thực tế: {len(all_reviews)}")
    print(f"Đã lưu file tại: {output_file}")

if __name__ == "__main__":
    run_mass_crawler()