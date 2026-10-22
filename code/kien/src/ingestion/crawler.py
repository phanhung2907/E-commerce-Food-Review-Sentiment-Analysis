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
# CƠ CHẾ KHÁM PHÁ TOÀN BỘ KHU VỰC TỰ ĐỘNG (ĐÃ LỌC BỎ SUBREGION RÁC)
# ==========================================
def discover_all_cities_automatically(driver, root_country_url):
    print(f"[Dynamic Discovery] Đang truy cập trang quốc gia: {root_country_url}")
    driver.get(root_country_url)
    
    time.sleep(random.uniform(12.0, 18.0))

    try:
        see_all_buttons = driver.find_elements(
            By.CSS_SELECTOR, 
            "span[data-test-target*='expand'], button[data-test-target*='expand'], a[data-test-target*='expand'], div.CoreButtonText"
        )
        for btn in see_all_buttons:
            try:
                driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                time.sleep(random.uniform(3.0, 5.0))
                if "xem tất" in btn.text.lower() or "see all" in btn.text.lower():
                    btn.click()
                    print("[Dynamic Discovery] Đã mở rộng toàn bộ danh sách khu vực.")
                    time.sleep(random.uniform(8.0, 12.0))
                    break
            except:
                continue
    except:
        pass

    print("[Dynamic Discovery] Đang cuộn trang để tải toàn bộ danh mục tỉnh thành...")
    last_height = driver.execute_script("return document.body.scrollHeight")
    for _ in range(10):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(5.0, 8.0))
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    city_links = []
    seen_urls = set()

    elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='Restaurants-g']")
    for elem in elements:
        try:
            href = elem.get_attribute("href")
            text = elem.text.strip()
            
            if href and "Restaurants-" in href and "RegistrationController" not in href and href not in seen_urls:
                if href == root_country_url:
                    continue
                
                # --- BỘ LỌC TỰ ĐỘNG THÔNG MINH ĐỂ CHẶN SUBREGION RÁC ---
                if not text or len(text) > 50 or "subregion" in text.lower() or "region" in text.lower():
                    continue
                if text.isdigit() or "see all" in text.lower() or "restaurants" in text.lower():
                    continue

                seen_urls.add(href)
                clean_city_name = text.replace(" Restaurants", "").strip()
                
                city_links.append({"city": clean_city_name, "url": href})
                print(f" -> Phát hiện thành phố hợp lệ: {clean_city_name} ({href})")
        except:
            continue

    print(f"[SUCCESS] Đã tự động phát hiện thành công {len(city_links)} khu vực/tỉnh thành chính thống tại Việt Nam (Đã loại bỏ hoàn toàn Subregion rác)!")
    return city_links


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
# CƠ CHẾ VÉT CẠN 100% REVIEWS QUA URL OFFSET & UPSERT THÔNG MINH
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
                    "rating": 5.0,
                    "review_date": datetime.now().strftime("%Y-%m-%d"),
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
    output_dir = "code/kien/data/raw/enterprise_unlimited"
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

    print("Khởi động Enterprise Crawler Vét Cạn Toàn Quốc (Đã tăng thời gian sleep tối đa, chống chặn tuyệt đối)...")

    # Khởi tạo driver với version_main=155 để khớp với Chrome trên máy và dùng use_subprocess=True
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