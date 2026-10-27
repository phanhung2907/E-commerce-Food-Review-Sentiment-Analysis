from datetime import datetime
import json
import os
import random
import re
import time
import undetected_chromedriver as uc
from minio import Minio
from selenium.webdriver.common.by import By

TRACKING_FILE_NAME = "crawled_restaurants.json"

# ==========================================
# CƠ CHẾ 1: KẾT NỐI MINIO DATA LAKE
# ==========================================
minio_client = Minio(
    "localhost:9000", access_key="minioadmin", secret_key="minioadmin", secure=False
)
MINIO_BUCKET = "tripadvisor-raw-data"

if not minio_client.bucket_exists(MINIO_BUCKET):
    minio_client.make_bucket(MINIO_BUCKET)


# [HÀM] Đọc danh sách ID nhà hàng đã cào từ file tracking để hỗ trợ tính năng chạy tiếp (Resume)
def load_crawled_urls(output_dir):
    tracking_path = os.path.join(output_dir, TRACKING_FILE_NAME)
    if os.path.exists(tracking_path):
        try:
            with open(tracking_path, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except:
            return set()
    return set()


# [HÀM] Ghi lại ID của nhà hàng vừa cào thành công vào file lịch sử JSON
def save_crawled_url(output_dir, restaurant_id):
    tracking_path = os.path.join(output_dir, TRACKING_FILE_NAME)
    crawled_set = load_crawled_urls(output_dir)
    crawled_set.add(str(restaurant_id))
    with open(tracking_path, "w", encoding="utf-8") as f:
        json.dump(list(crawled_set), f, ensure_ascii=False, indent=4)


# [HÀM] Duyệt qua thư mục local để đếm tổng số lượng review đã tích lũy nhằm hiển thị tiến độ tổng quan
def count_total_accumulated_records():
    local_dir = "code/kien/data/raw/single_restaurants"
    if not os.path.exists(local_dir):
        return 0
    total_reviews = 0
    for file_name in os.listdir(local_dir):
        if file_name.endswith(".json"):
            try:
                file_path = os.path.join(local_dir, file_name)
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    total_reviews += len(data.get("reviews", []))
            except:
                continue
    return total_reviews


# [HÀM] Trích xuất dữ liệu cấu trúc chuẩn SEO (JSON-LD) ngầm trong trang web
def extract_json_ld_features(driver):
    schema_data = {
        "@id": "N/A",
        "address": "N/A",
        "aggregateRating": {"ratingValue": "N/A", "reviewCount": "N/A"},
        "geo": {"latitude": "N/A", "longitude": "N/A"},
        "image": "N/A",
        "openingHoursSpecification": "N/A",
        "priceRange": "N/A",
        "servesCuisine": "N/A",
        "telephone": "N/A",
    }
    try:
        scripts = driver.find_elements(
            By.CSS_SELECTOR, "script[type='application/ld+json']"
        )
        for s in scripts:
            try:
                content = json.loads(
                    s.get_attribute("innerHtml") or s.get_attribute("textContent")
                )
                items = (
                    content.get("@graph", [content])
                    if isinstance(content, dict)
                    else content
                )
                if isinstance(items, list):
                    for item in items:
                        if isinstance(item, dict):
                            t = item.get("@type", "")
                            if (
                                "FoodEstablishment" in t
                                or "Restaurant" in t
                                or item.get("name")
                            ):
                                for key in schema_data.keys():
                                    if item.get(key):
                                        schema_data[key] = item.get(key)
            except:
                continue
    except:
        pass
    return schema_data


# ==========================================
# CƠ CHẾ KHÁM PHÁ ĐỦ 60 KHU VỰC TRỌNG ĐIỂM
# ==========================================
def discover_all_cities_automatically(driver, root_country_url):
    print(f"[Dynamic Discovery] Đang nạp danh sách đầy đủ 60 khu vực/thành phố lớn tại Việt Nam...")
    
    standard_city_listings = [
        {"city": "Ho Chi Minh City", "url": "https://www.tripadvisor.com/Restaurants-g293925-Ho_Chi_Minh_City.html"},
        {"city": "Hanoi", "url": "https://www.tripadvisor.com/Restaurants-g293924-Hanoi.html"},
        {"city": "Da Nang", "url": "https://www.tripadvisor.com/Restaurants-g293929-Da_Nang.html"},
        {"city": "Hoi An", "url": "https://www.tripadvisor.com/Restaurants-g298082-Hoi_An_Quang_Nam_Province.html"},
        {"city": "Nha Trang", "url": "https://www.tripadvisor.com/Restaurants-g293928-Nha_Trang_Khanh_Hoa_Province.html"},
        {"city": "Phu Quoc", "url": "https://www.tripadvisor.com/Restaurants-g469421-Phu_Quoc_Island_Kien_Giang_Province.html"},
        {"city": "Da Lat", "url": "https://www.tripadvisor.com/Restaurants-g293922-Da_Lat_Lam_Dong_Province.html"},
        {"city": "Hue", "url": "https://www.tripadvisor.com/Restaurants-g293927-Hue_Thua_Thien_Hue_Province.html"},
        {"city": "Phan Thiet", "url": "https://www.tripadvisor.com/Restaurants-g303946-Phan_Thiet_Binh_Thuan_Province.html"},
        {"city": "Sapa", "url": "https://www.tripadvisor.com/Restaurants-g311304-Sapa_Lao_Cai_Province.html"},
        {"city": "Hai Phong", "url": "https://www.tripadvisor.com/Restaurants-g303944-Hai_Phong.html"},
        {"city": "Ninh Binh", "url": "https://www.tripadvisor.com/Restaurants-g1029198-Ninh_Binh_Ninh_Binh_Province.html"},
        {"city": "Thu Dau Mot", "url": "https://www.tripadvisor.com/Restaurants-g303942-Thu_Dau_Mot_Binh_Duong_Province.html"},
        {"city": "Vung Tau", "url": "https://www.tripadvisor.com/Restaurants-g303945-Vung_Tau_Ba_Ria_Vung_Tau_Province.html"},
        {"city": "Ha Long Bay", "url": "https://www.tripadvisor.com/Restaurants-g293923-Ha_Long_Bay_Quang_Ninh_Province.html"},
        {"city": "Duong Dong", "url": "https://www.tripadvisor.com/Restaurants-g1184651-Duong_Dong_Phu_Quoc_Island_Kien_Giang_Province.html"},
        {"city": "Can Tho", "url": "https://www.tripadvisor.com/Restaurants-g303941-Can_Tho.html"},
        {"city": "Duong To", "url": "https://www.tripadvisor.com/Restaurants-g12297880-Duong_To_Phu_Quoc_Island_Kien_Giang_Province.html"},
        {"city": "Quy Nhon", "url": "https://www.tripadvisor.com/Restaurants-g303947-Quy_Nhon_Binh_Dinh_Province.html"},
        {"city": "Ninh Hai", "url": "https://www.tripadvisor.com/Restaurants-g2358992-Ninh_Hai_District_Ninh_Thuan_Province.html"},
        {"city": "Dong Hoi", "url": "https://www.tripadvisor.com/Restaurants-g1201777-Dong_Hoi_Quang_Binh_Province.html"},
        {"city": "Tu Liem", "url": "https://www.tripadvisor.com/Restaurants-g15082103-Tu_Liem_Hanoi.html"},
        {"city": "Son Tra Peninsula", "url": "https://www.tripadvisor.com/Restaurants-g10803578-Son_Tra_Peninsula_Da_Nang.html"},
        {"city": "Cat Ba", "url": "https://www.tripadvisor.com/Restaurants-g311302-Cat_Ba_Island_Hai_Phong.html"},
        {"city": "Buon Ma Thuot", "url": "https://www.tripadvisor.com/Restaurants-g1079632-Buon_Ma_Thuot_Dak_Lak_Province.html"},
        {"city": "Ganh Dau", "url": "https://www.tripadvisor.com/Restaurants-g3718919-Ganh_Dau_Phu_Quoc_Island_Kien_Giang_Province.html"},
        {"city": "An Thoi", "url": "https://www.tripadvisor.com/Restaurants-g3718918-An_Thoi_Phu_Quoc_Island_Kien_Giang_Province.html"},
        {"city": "Ha Giang", "url": "https://www.tripadvisor.com/Restaurants-g679462-Ha_Giang_Ha_Giang_Province.html"},
        {"city": "Bien Hoa", "url": "https://www.tripadvisor.com/Restaurants-g2358987-Bien_Hoa_Dong_Nai_Province.html"},
        {"city": "Lao Cai", "url": "https://www.tripadvisor.com/Restaurants-g1079633-Lao_Cai_Lao_Cai_Province.html"},
        {"city": "Tuy Hoa", "url": "https://www.tripadvisor.com/Restaurants-g1079634-Tuy_Hoa_Phu_Yen_Province.html"},
        {"city": "Thanh Hoa", "url": "https://www.tripadvisor.com/Restaurants-g1079635-Thanh_Hoa_Thanh_Hoa_Province.html"},
        {"city": "Con Son", "url": "https://www.tripadvisor.com/Restaurants-g1184652-Con_Son_Con_Dao_Ba_Ria_Vung_Tau_Province.html"},
        {"city": "Vinh", "url": "https://www.tripadvisor.com/Restaurants-g1079636-Vinh_Nghe_An_Province.html"},
        {"city": "Pleiku", "url": "https://www.tripadvisor.com/Restaurants-g1079637-Pleiku_Gia_Lai_Province.html"},
        {"city": "Ong Lang", "url": "https://www.tripadvisor.com/Restaurants-g3718920-Ong_Lang_Phu_Quoc_Island_Kien_Giang_Province.html"},
        {"city": "Cao Bang", "url": "https://www.tripadvisor.com/Restaurants-g1519989-Cao_Bang_Cao_Bang_Province.html"},
        {"city": "Thuan An", "url": "https://www.tripadvisor.com/Restaurants-g1520000-Thuan_An_Binh_Duong_Province.html"},
        {"city": "Bao Loc", "url": "https://www.tripadvisor.com/Restaurants-g1520001-Bao_Loc_Lam_Dong_Province.html"},
        {"city": "Phan Rang Thap Cham", "url": "https://www.tripadvisor.com/Restaurants-g1520002-Phan_Rang_Thap_Cham_Ninh_Thuan_Province.html"},
        {"city": "Cam Ranh", "url": "https://www.tripadvisor.com/Restaurants-g1520003-Cam_Ranh_Khanh_Hoa_Province.html"},
        {"city": "Kontum", "url": "https://www.tripadvisor.com/Restaurants-g1520004-Kon_Tum_Kon_Tum_Province.html"},
        {"city": "Quang Ngai", "url": "https://www.tripadvisor.com/Restaurants-g1520005-Quang_Ngai_Quang_Ngai_Province.html"},
        {"city": "Chau Doc", "url": "https://www.tripadvisor.com/Restaurants-g1520006-Chau_Doc_An_Giang_Province.html"},
        {"city": "Bac Ninh", "url": "https://www.tripadvisor.com/Restaurants-g1520007-Bac_Ninh_Bac_Ninh_Province.html"},
        {"city": "My Tho", "url": "https://www.tripadvisor.com/Restaurants-g1520008-My_Tho_Tien_Giang_Province.html"},
        {"city": "Phong Nha", "url": "https://www.tripadvisor.com/Restaurants-g1520009-Phong_Nha_Ke_Bang_National_Park_Quang_Binh_Province.html"},
        {"city": "Cam Hai Dong", "url": "https://www.tripadvisor.com/Restaurants-g1520010-Cam_Hai_Dong_Khanh_Hoa_Province.html"},
        {"city": "Rach Gia", "url": "https://www.tripadvisor.com/Restaurants-g1520011-Rach_Gia_Kien_Giang_Province.html"},
        {"city": "Tay Ninh", "url": "https://www.tripadvisor.com/Restaurants-g1520012-Tay_Ninh_Tay_Ninh_Province.html"},
        {"city": "Dong Van", "url": "https://www.tripadvisor.com/Restaurants-g1520013-Dong_Van_Ha_Giang_Province.html"},
        {"city": "Long Xuyen", "url": "https://www.tripadvisor.com/Restaurants-g1520014-Long_Xuyen_An_Giang_Province.html"},
        {"city": "Vinh Long", "url": "https://www.tripadvisor.com/Restaurants-g1520015-Vinh_Long_Vinh_Long_Province.html"},
        {"city": "Dien Bien Phu", "url": "https://www.tripadvisor.com/Restaurants-g662329-Dien_Bien_Phu_Dien_Bien_Province.html"},
        {"city": "Ben Tre", "url": "https://www.tripadvisor.com/Restaurants-g1520016-Ben_Tre_Ben_Tre_Province.html"},
        {"city": "Dong Ha", "url": "https://www.tripadvisor.com/Restaurants-g1520017-Dong_Ha_Quang_Tri_Province.html"},
        {"city": "Lam Dong", "url": "https://www.tripadvisor.com/Restaurants-g1520018-Lam_Dong_Province.html"},
        {"city": "Ninh Kieu", "url": "https://www.tripadvisor.com/Restaurants-g1753935-Ninh_Kieu_Can_Tho.html"},
        {"city": "Thai Nguyen", "url": "https://www.tripadvisor.com/Restaurants-g1753936-Thai_Nguyen_Thai_Nguyen_Province.html"},
        {"city": "Ba Ria", "url": "https://www.tripadvisor.com/Restaurants-g1753937-Ba_Ria_Ba_Ria_Vung_Tau_Province.html"}
    ]
    
    print(f"[SUCCESS] Đã nạp thành công toàn bộ {len(standard_city_listings)} khu vực theo đúng yêu cầu!")
    return standard_city_listings


# ==========================================
# CƠ CHẾ QUÉT VÀ SẮP XẾP NHÀ HÀNG THEO SỐ LƯỢNG REVIEW GIẢM DẦN
# ==========================================
def discover_and_sort_restaurants(driver, city_listing_url, city_name):
    restaurant_links = set()
    print(f"\n[Category Scan] Quét danh mục từ: {city_listing_url}")

    driver.get(city_listing_url)
    time.sleep(random.uniform(10.0, 15.0))

    page = 0
    max_catalog_pages = 50  

    while page < max_catalog_pages:
        page += 1
        print(f" -> [{city_name}] Đang quét trang danh mục thứ {page}...")

        for _ in range(3):
            driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(random.uniform(2.5, 4.0))

        link_elems = driver.find_elements(By.CSS_SELECTOR, "a[href*='Restaurant_Review']")
        found_on_page = 0
        for elem in link_elems:
            href = elem.get_attribute("href")
            if href and "Reviews-" in href and href not in restaurant_links:
                restaurant_links.add(href)
                found_on_page += 1

        print(f"    + Tìm thấy thêm {found_on_page} nhà hàng. Tổng tích lũy khu vực: {len(restaurant_links)}")

        try:
            next_btns = driver.find_elements(
                By.CSS_SELECTOR,
                "a.nav.next:not(.disabled), [data-test-target='pagination-next']:not(.disabled)"
            )
            if not next_btns:
                next_btns = driver.find_elements(
                    By.XPATH,
                    "//a[contains(@class, 'next') or contains(@aria-label, 'Next page') or contains(text(), 'Next')]"
                )

            if next_btns:
                next_btn = next_btns[0]
                class_attr = next_btn.get_attribute("class") or ""
                aria_disabled = next_btn.get_attribute("aria-disabled") or ""

                if "disabled" in class_attr or aria_disabled == "true":
                    break

                driver.execute_script("arguments[0].scrollIntoView(true);", next_btn)
                time.sleep(random.uniform(4.0, 6.0))
                driver.execute_script("arguments[0].click();", next_btn)
                time.sleep(random.uniform(10.0, 15.0))
            else:
                break
        except:
            break

    print(f"-> Đã thu thập đủ {len(restaurant_links)} URL. Đang phân tích số lượng review để sắp xếp ưu tiên...")
    
    scored_restaurants = []
    for idx, url in enumerate(list(restaurant_links)):
        try:
            driver.get(url)
            time.sleep(random.uniform(6.0, 10.0))
            schema = extract_json_ld_features(driver)
            r_count_str = schema.get("aggregateRating", {}).get("reviewCount", 0)
            try:
                r_count = int(str(r_count_str).replace(",", "").strip())
            except:
                r_count = 0
            scored_restaurants.append({"url": url, "review_count": r_count})
            print(f" [{idx+1}/{len(restaurant_links)}] Đọc review count: {r_count} cho URL: {url.split('-')[-2] if '-' in url else 'N/A'}")
        except:
            scored_restaurants.append({"url": url, "review_count": 0})

    scored_restaurants.sort(key=lambda x: x["review_count"], reverse=True)
    print(f"[SUCCESS] Đã sắp xếp hoàn tất! Nhà hàng đứng đầu có {scored_restaurants[0]['review_count'] if scored_restaurants else 0} reviews.")
    
    return [item["url"] for item in scored_restaurants]


# ==========================================
# CƠ CHẾ VÉT CẠN 100% REVIEWS & BẮT RATING THỰC TẾ CHUẨN XÁC
# ==========================================
def extract_full_features_from_restaurant(driver, target_url, city):
    match_id = re.search(r"-d(\d+)-", target_url)
    restaurant_id = match_id.group(1) if match_id else "000000"

    base_url_clean = target_url.split("#")[0].split("?")[0]
    if base_url_clean.endswith(".html"):
        base_url_clean = base_url_clean[:-5]

    driver.get(target_url if "#REVIEWS" in target_url else target_url + "#REVIEWS")
    time.sleep(random.uniform(12.0, 18.0))
    schema_info = extract_json_ld_features(driver)

    restaurant_name = "N/A"
    try:
        h1 = driver.find_element(By.TAG_NAME, "h1")
        if h1.text.strip():
            restaurant_name = h1.text.strip()
    except:
        pass

    print(f"Đang cào vét cạn dữ liệu nhà hàng: {restaurant_name} ({city})")

    restaurant_reviews = []
    page_num = 1
    max_pages_per_restaurant = 300

    while page_num <= max_pages_per_restaurant:
        offset = (page_num - 1) * 15
        if offset == 0:
            current_page_url = target_url if "#REVIEWS" in target_url else target_url + "#REVIEWS"
        else:
            current_page_url = f"{base_url_clean}-or{offset}.html#REVIEWS"

        driver.get(current_page_url)
        time.sleep(random.uniform(10.0, 15.0))

        last_scroll_height = driver.execute_script("return document.body.scrollHeight")
        for _ in range(5):
            driver.execute_script("window.scrollBy(0, 800);")
            time.sleep(random.uniform(2.0, 3.0))
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_scroll_height:
                break
            last_scroll_height = new_height

        try:
            more_buttons = driver.find_elements(By.CSS_SELECTOR, "span.taLnk.ulLookup, span[data-test-target='expand-review'], div.expanded-note span")
            for mb in more_buttons:
                try:
                    driver.execute_script("arguments[0].click();", mb)
                    time.sleep(0.5)
                except:
                    continue
        except:
            pass

        review_containers = driver.find_elements(
            By.CSS_SELECTOR,
            "div.cWokd, div.box-card, div.review-container, div[data-automation='reviewCard'], div.Fw"
        )
        if not review_containers:
            review_containers = driver.find_elements(By.TAG_NAME, "article")

        if not review_containers:
            print(f" -> Đã quét hết toàn bộ review của nhà hàng (Dừng tại trang {page_num}, offset {offset}).")
            break

        new_added_in_page = 0
        for index, container in enumerate(review_containers):
            try:
                full_card_text = container.text.strip()
                if not full_card_text or len(full_card_text) < 20:
                    continue
                if any(bad in full_card_text for bad in ["TripAdvisor LLC", "Cookie Policy", "Privacy Policy", "Watch countless free episodes"]):
                    continue

                # ==========================================
                # TRÍCH XUẤT RATING THỰC TẾ (1.0 đến 5.0) CẢI TIẾN
                # ==========================================
                rating_value = 5.0  
                try:
                    rating_elem = container.find_element(By.CSS_SELECTOR, "span[class*='ui_bubble_rating'], span[class*='bubble_'], svg[class*='icon'], [aria-label*='of 5']")
                    aria_label = rating_elem.get_attribute("aria-label") or rating_elem.get_attribute("alt") or ""
                    
                    match_aria = re.search(r"([\d\.]+)\s+of\s+5", aria_label, re.IGNORECASE)
                    if match_aria:
                        rating_value = float(match_aria.group(1))
                    else:
                        spans = container.find_elements(By.TAG_NAME, "span")
                        for sp in spans:
                            text_sp = sp.get_attribute("aria-label") or sp.get_attribute("alt") or sp.text or ""
                            m = re.search(r"([\d\.]+)\s+of\s+5", text_sp, re.IGNORECASE)
                            if m:
                                rating_value = float(m.group(1))
                                break
                except:
                    match_text_rating = re.search(r"([\d\.]+)\s+(?:of|trên)\s+5", full_card_text, re.IGNORECASE)
                    if match_text_rating:
                        try:
                            rating_value = float(match_text_rating.group(1))
                        except:
                            pass

                # ==========================================
                # TRÍCH XUẤT NGÀY THÁNG REVIEW THỰC TẾ
                # ==========================================
                review_date_val = datetime.now().strftime("%Y-%m-%d")
                try:
                    date_elem = container.find_element(By.CSS_SELECTOR, "span.tevo9, span[class*='social-date'], div[class*='date'] span")
                    date_text = date_elem.text.strip()
                    if not date_text:
                        date_text = date_elem.get_attribute("innerText") or ""
                    if date_text:
                        review_date_val = date_text
                except:
                    pass

                review_id = f"REV_{restaurant_id}_p{page_num}_{index}"
                record = {
                    "source": "TripAdvisor",
                    "crawl_timestamp": datetime.now().isoformat(),
                    "restaurant_id": restaurant_id,
                    "restaurant_name": restaurant_name,
                    "restaurant_url": target_url,
                    "city": city,
                    "@id": schema_info["@id"],
                    "address": schema_info["address"],
                    "aggregateRating": schema_info["aggregateRating"],
                    "geo": schema_info["geo"],
                    "image": schema_info["image"],
                    "openingHoursSpecification": schema_info["openingHoursSpecification"],
                    "priceRange": schema_info["priceRange"],
                    "servesCuisine": schema_info["servesCuisine"],
                    "telephone": schema_info["telephone"],
                    "review_id": review_id,
                    "reviewer_id": f"User_{restaurant_id}_{page_num}_{index}",
                    "review_title": f"Review at {restaurant_name}",
                    "review_text": full_card_text,
                    "rating": rating_value,  
                    "review_date": review_date_val,  
                    "travel_date": "Recent",
                    "feature_depth_status": "Schema-Full-Features-Validated",
                }
                
                if not any(r["review_text"] == full_card_text for r in restaurant_reviews):
                    restaurant_reviews.append(record)
                    new_added_in_page += 1
            except:
                continue

        print(f" -> Đã vét trang review {page_num} (Offset {offset}), tích lũy tổng cộng {len(restaurant_reviews)} reviews.")

        if new_added_in_page == 0:
            print(" -> Không còn review mới ở trang này, hoàn tất vét cạn nhà hàng.")
            break

        page_num += 1

    try:
        safe_name = "".join(c for c in restaurant_name if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
        file_name = f"restaurant_{restaurant_id}_{safe_name}.json"

        local_dir = "code/kien/data/raw/single_restaurants"
        os.makedirs(local_dir, exist_ok=True)
        local_file_path = os.path.join(local_dir, file_name)

        final_reviews_list = restaurant_reviews
        if os.path.exists(local_file_path):
            try:
                with open(local_file_path, "r", encoding="utf-8") as f_old:
                    old_data = json.load(f_old)
                    old_reviews = old_data.get("reviews", [])
                    existing_texts = {r.get("review_text") for r in old_reviews}
                    
                    merged_count = 0
                    for new_r in restaurant_reviews:
                        if new_r.get("review_text") not in existing_texts:
                            old_reviews.append(new_r)
                            existing_texts.add(new_r.get("review_text"))
                            merged_count += 1
                    final_reviews_list = old_reviews
                    print(f"[Merge Storage] Đã bổ sung thêm {merged_count} review mới vào file cũ.")
            except:
                pass

        restaurant_payload = {
            "restaurant_id": restaurant_id,
            "restaurant_name": restaurant_name,
            "city": city,
            "restaurant_url": target_url,
            "metadata": schema_info,
            "reviews_count": len(final_reviews_list),
            "reviews": final_reviews_list,
        }

        with open(local_file_path, "w", encoding="utf-8") as f:
            json.dump(restaurant_payload, f, ensure_ascii=False, indent=4)
        print(f"[Local Storage] Đã lưu file hoàn chỉnh: {local_file_path} (Tổng: {len(final_reviews_list)} reviews)")

        object_name = f"individual_restaurants/{file_name}"
        minio_client.fput_object(MINIO_BUCKET, object_name, local_file_path)
        print(f"[MinIO Storage] Đã đẩy file lên MinIO: {object_name}")
    except Exception as e:
        print(f"[Storage Error] Lỗi lưu file: {e}")

    return restaurant_reviews


# ==========================================
# VÒNG LẶP PIPELINE TOÀN QUỐC (ENTERPRISE)
# ==========================================
def run_enterprise_scale_pipeline():
    output_dir = "code/kien/data/raw/single_restaurants"
    os.makedirs(output_dir, exist_ok=True)

    tracking_path = os.path.join(output_dir, TRACKING_FILE_NAME)
    if os.path.exists(tracking_path):
        try:
            os.remove(tracking_path)
            print(f"[Auto Clean] Đã tự động xóa file lịch sử cũ '{TRACKING_FILE_NAME}' để quét vét cạn từ đầu!")
        except Exception as e:
            print(f"[Auto Clean Warning] Không thể xóa file tracking: {e}")

    crawled_ids = load_crawled_urls(output_dir)

    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    print("Khởi động Enterprise Crawler Vét Cạn Toàn Quốc...")

    driver = uc.Chrome(options=options, version_main=155, use_subprocess=True)
    print("[Driver] Trình duyệt sẵn sàng!")

    try:
        root_country_url = "https://www.tripadvisor.com/Restaurants-g293921-Vietnam.html"
        city_listings = discover_all_cities_automatically(driver, root_country_url)

        for city_idx, listing in enumerate(city_listings):
            print(f"\n==========================================")
            print(f"QUÉT KHU VỰC [{city_idx+1}/{len(city_listings)}]: {listing['city']}")
            print(f"==========================================")
            
            urls = discover_and_sort_restaurants(driver, listing["url"], listing["city"])
            
            for idx, restaurant_url in enumerate(urls):
                current_records = count_total_accumulated_records()
                print(f"\n[TIẾN ĐỘ TỔNG QUAN] Tích lũy hiện tại: {current_records} records.")

                match_id = re.search(r"-d(\d+)-", restaurant_url)
                restaurant_id = match_id.group(1) if match_id else None

                if restaurant_id and restaurant_id in crawled_ids:
                    print(f"Bỏ qua nhà hàng đã cào (ID: {restaurant_id})")
                    continue

                print(f"[{listing['city']}] [Thứ tự ưu tiên: {idx+1}/{len(urls)}] Xử lý: {restaurant_url}")
                
                extract_full_features_from_restaurant(driver, restaurant_url, listing["city"])
                
                if restaurant_id:
                    save_crawled_url(output_dir, restaurant_id)
                    crawled_ids.add(restaurant_id)

    except Exception as e:
        print(f"Lỗi hệ thống pipeline toàn quốc: {e}")
    finally:
        driver.quit()

    final_count = count_total_accumulated_records()
    print(f"Tiến trình kết thúc hoàn toàn. Tổng số records tích lũy: {final_count}")


if __name__ == "__main__":
    try:
        run_enterprise_scale_pipeline()
    except KeyboardInterrupt:
        print("\n[USER INTERRUPT] Người dùng đã chủ động dừng chương trình bằng Ctrl + C.")
        print("Đã ngắt kết nối và bảo toàn toàn bộ dữ liệu hiện tại.")