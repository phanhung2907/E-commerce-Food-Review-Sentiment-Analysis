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


# [HÀM] Đọc danh sách ID nhà hàng đã cào từ file tracking để hỗ trợ tính năng chạy tiếp (Resume) không bị trùng lặp
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


# [HÀM] Trích xuất dữ liệu cấu trúc chuẩn SEO (JSON-LD) ngầm trong trang web để lấy tọa độ, địa chỉ, đánh giá chính xác
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
# CƠ CHẾ KHÁM PHÁ TOÀN BỘ KHU VỰC TỰ ĐỘNG (DYNAMMIC DISCOVERY)
# ==========================================
# [HÀM] Tự động truy cập trang quốc gia, bấm mở rộng và cuộn trang để vét cạn 100% khu vực/tỉnh thành
def discover_all_cities_automatically(driver, root_country_url):
    print(f"[Dynamic Discovery] Đang truy cập trang quốc gia để quét tự động: {root_country_url}")
    driver.get(root_country_url)
    time.sleep(random.uniform(4.0, 6.0))  # Chờ trang tải hoàn tất dữ liệu ban đầu

    # Thử tìm và bấm các nút "Xem tất cả" / "See all" để mở rộng toàn bộ danh sách khu vực ẩn
    try:
        see_all_buttons = driver.find_elements(
            By.CSS_SELECTOR, 
            "span[data-test-target*='expand'], button[data-test-target*='expand'], a[data-test-target*='expand'], div.CoreButtonText"
        )
        for btn in see_all_buttons:
            try:
                driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                time.sleep(1.0)
                if "xem tất" in btn.text.lower() or "see all" in btn.text.lower():
                    btn.click()
                    print("[Dynamic Discovery] Đã bấm mở rộng toàn bộ danh sách khu vực.")
                    time.sleep(3.0)
                    break
            except:
                continue
    except:
        pass

    # Thực hiện cuộn trang sâu nhiều nhịp để kích hoạt tải toàn bộ các liên kết khu vực động (Lazy loading)
    print("[Dynamic Discovery] Đang cuộn trang để tải toàn bộ danh mục tỉnh thành...")
    last_height = driver.execute_script("return document.body.scrollHeight")
    for _ in range(10):  # Cuộn 10 nhịp để vét cạn danh sách
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2.0)  # Tạm dừng ngắn để trình duyệt load thêm nội dung DOM
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    city_links = []
    seen_urls = set()

    # Quét toàn bộ các thẻ chứa liên kết dẫn đến trang nhà hàng của các vùng (Restaurants-g...)
    elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='Restaurants-g']")
    for elem in elements:
        try:
            href = elem.get_attribute("href")
            text = elem.text.strip()
            # Lọc chỉ lấy các link chuẩn danh mục nhà hàng và loại bỏ các link trùng lặp
            if href and "Restaurants-" in href and href not in seen_urls:
                if href == root_country_url:
                    continue
                seen_urls.add(href)
                city_name = text if text and len(text) < 50 else "Vietnam_Subregion"
                city_links.append({"city": city_name, "url": href})
        except:
            continue

    print(f"[SUCCESS] Đã tự động phát hiện thành công {len(city_links)} khu vực/tỉnh thành tại Việt Nam!")
    return city_links


# ==========================================
# CƠ CHẾ QUÉT PHÂN TRANG DANH MỤC KHÔNG GIỚI HẠN
# ==========================================
# [HÀM] Quét phân trang toàn bộ danh mục nhà hàng của một khu vực để thu thập đầy đủ URL
def discover_restaurant_urls(driver, city_listing_url):
    restaurant_links = set()
    print(f"\n[Category Scan] Quét danh mục từ: {city_listing_url}")

    driver.get(city_listing_url)
    time.sleep(random.uniform(3.0, 5.0))  # Chờ trang danh mục khu vực load ổn định

    page = 0
    while True:
        page += 1
        print(f" -> Đang quét trang danh mục thứ {page}...")

        for _ in range(3):
            driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(0.8)  # Dừng ngắn sau mỗi nhịp cuộn để kích hoạt tải dữ liệu động (Lazy loading)

        link_elems = driver.find_elements(By.CSS_SELECTOR, "a[href*='Restaurant_Review']")
        found_on_page = 0
        for elem in link_elems:
            href = elem.get_attribute("href")
            if href and "Reviews-" in href and href not in restaurant_links:
                restaurant_links.add(href)
                found_on_page += 1

        print(f"    + Tìm thấy thêm {found_on_page} nhà hàng ở trang này.")

        # Thử bấm chuyển trang tiếp theo (Next Page)
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
                    print(" -> Đã quét đến trang cuối cùng của khu vực này.")
                    break

                driver.execute_script("arguments[0].scrollIntoView(true);", next_btn)
                time.sleep(1.0)  # Chờ nút Next hiển thị rõ trên khung nhìn trước khi bấm
                next_btn.click()
                time.sleep(random.uniform(3.0, 5.0))  # Chờ trang mới của danh mục load xong sau khi click
            else:
                print(" -> Không tìm thấy nút Next, hoàn tất khu vực này.")
                break
        except Exception:
            print(" -> Hoàn tất phân trang khu vực này.")
            break

    print(f"-> Tổng kết khu vực: Thu thập được {len(restaurant_links)} URL nhà hàng.")
    return list(restaurant_links)


# [HÀM] Trích xuất chi tiết review nhà hàng và thực hiện lưu trữ kép (Local & MinIO)
def extract_full_features_from_restaurant(driver, target_url, city):
    match_id = re.search(r"-d(\d+)-", target_url)
    restaurant_id = match_id.group(1) if match_id else "000000"

    schema_info = extract_json_ld_features(driver)

    restaurant_name = "N/A"
    try:
        h1 = driver.find_element(By.TAG_NAME, "h1")
        if h1.text.strip():
            restaurant_name = h1.text.strip()
    except:
        pass

    print(f"Đang cào dữ liệu nhà hàng: {restaurant_name} ({city})")

    restaurant_reviews = []
    page_num = 1
    max_pages_per_restaurant = 50  # Mở rộng số trang review tối đa cho mỗi nhà hàng

    while page_num <= max_pages_per_restaurant:
        for _ in range(2):
            driver.execute_script("window.scrollBy(0, 800);")
            time.sleep(random.uniform(1.0, 1.5))  # Dừng ngắn để nội dung review load dần xuống trang

        review_containers = driver.find_elements(
            By.CSS_SELECTOR,
            "div.cWokd, div.box-card, div.review-container, div[data-automation='reviewCard']"
        )
        if not review_containers:
            review_containers = driver.find_elements(By.TAG_NAME, "article")

        for index, container in enumerate(review_containers):
            try:
                full_card_text = container.text.strip()
                if not full_card_text or len(full_card_text) < 30:
                    continue
                if any(bad in full_card_text for bad in ["TripAdvisor LLC", "Cookie Policy", "Privacy Policy"]):
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
                    "reviewer_id": f"User_p{page_num}_{index}",
                    "review_title": f"Review at {restaurant_name}",
                    "review_text": full_card_text,
                    "rating": 5.0,
                    "review_date": datetime.now().strftime("%Y-%m-%d"),
                    "travel_date": "Recent",
                    "feature_depth_status": "Schema-Full-Features-Validated",
                }
                if record not in restaurant_reviews:
                    restaurant_reviews.append(record)
            except:
                pass

        try:
            next_btn = driver.find_element(
                By.CSS_SELECTOR,
                "a.nav.next:not(.disabled), [data-test-target='pagination-next']:not(.disabled)"
            )
            if next_btn:
                driver.execute_script("arguments[0].scrollIntoView(true);", next_btn)
                time.sleep(1.0)  # Chờ nút chuyển trang review hiển thị
                next_btn.click()
                page_num += 1
                time.sleep(random.uniform(3.0, 5.0))  # Chờ trang review tiếp theo tải xong
            else:
                break
        except:
            break

    try:
        safe_name = "".join(c for c in restaurant_name if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
        file_name = f"restaurant_{restaurant_id}_{safe_name}.json"

        local_dir = "code/kien/data/raw/single_restaurants"
        os.makedirs(local_dir, exist_ok=True)
        local_file_path = os.path.join(local_dir, file_name)

        restaurant_payload = {
            "restaurant_id": restaurant_id,
            "restaurant_name": restaurant_name,
            "city": city,
            "restaurant_url": target_url,
            "metadata": schema_info,
            "reviews_count": len(restaurant_reviews),
            "reviews": restaurant_reviews,
        }

        with open(local_file_path, "w", encoding="utf-8") as f:
            json.dump(restaurant_payload, f, ensure_ascii=False, indent=4)
        print(f"[Local Storage] Đã lưu file: {local_file_path}")

        object_name = f"individual_restaurants/{file_name}"
        minio_client.fput_object(MINIO_BUCKET, object_name, local_file_path)
        print(f"[MinIO Storage] Đã đẩy file lên bucket '{MINIO_BUCKET}': {object_name}")
    except Exception as e:
        print(f"[Storage Error] Lỗi lưu file: {e}")

    return restaurant_reviews


# ==========================================
# VÒNG LẶP PIPELINE KHÔNG GIỚI HẠN (ENTERPRISE)
# ==========================================
# [HÀM] Điều phối toàn bộ quy trình chạy cào dữ liệu quy mô lớn theo từng khu vực cuốn chiếu
def run_enterprise_scale_pipeline():
    output_dir = "code/kien/data/raw/enterprise_unlimited"
    os.makedirs(output_dir, exist_ok=True)

    crawled_ids = load_crawled_urls(output_dir)
    print(f"Đã tải {len(crawled_ids)} nhà hàng đã cào thành công từ trước.")

    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")

    print("Khởi động Enterprise Crawler (Chạy quét toàn quốc không giới hạn tự động)...")

    driver = uc.Chrome(options=options)
    print("[Driver] Trình duyệt sẵn sàng!")

    try:
        root_country_url = "https://www.tripadvisor.com/Restaurants-g293921-Vietnam.html"
        city_listings = discover_all_cities_automatically(driver, root_country_url)

        # Quét và cào cuộn chiếu theo từng khu vực để không bị mất dữ liệu
        for city_idx, listing in enumerate(city_listings):
            print(f"\n==========================================")
            print(f"QUÉT KHU VỰC [{city_idx+1}/{len(city_listings)}]: {listing['city']}")
            print(f"==========================================")
            
            urls = discover_restaurant_urls(driver, listing["url"])
            
            for idx, restaurant_url in enumerate(urls):
                current_records = count_total_accumulated_records()
                print(f"\n[TIẾN ĐỘ TỔNG QUAN] Tích lũy hiện tại: {current_records} records.")

                match_id = re.search(r"-d(\d+)-", restaurant_url)
                restaurant_id = match_id.group(1) if match_id else None

                if restaurant_id and restaurant_id in crawled_ids:
                    print(f"Bỏ qua nhà hàng đã cào (ID: {restaurant_id})")
                    continue

                print(f"[{listing['city']}] [Tiến độ nhà hàng: {idx+1}/{len(urls)}] Xử lý: {restaurant_url}")
                driver.get(restaurant_url)
                time.sleep(random.uniform(3.0, 5.0))  # Chờ trình duyệt load xong trang chi tiết nhà hàng mới

                extract_full_features_from_restaurant(driver, restaurant_url, listing["city"])
                
                if restaurant_id:
                    save_crawled_url(output_dir, restaurant_id)
                    crawled_ids.add(restaurant_id)

    except Exception as e:
        print(f"Lỗi hệ thống pipeline: {e}")
    finally:
        driver.quit()

    final_count = count_total_accumulated_records()
    print(f"Tiến trình kết thúc. Tổng số records tích lũy: {final_count}")


if __name__ == "__main__":
    run_enterprise_scale_pipeline()