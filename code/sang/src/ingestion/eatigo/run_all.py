import json
from pathlib import Path
import time
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By

class LoggerWriter:
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, "a", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush()

    def flush(self):
        self.terminal.flush()
        self.log.flush()

def run_global_crawler():
    output_dir = Path("code/sang/data/raw/eatigo")
    output_dir.mkdir(parents=True, exist_ok=True) 
    output_file = output_dir / "eatigo_raw_objects_final.json"
    links_checkpoint_file = output_dir / "scanned_links_checkpoint.json"
    visited_checkpoint_file = output_dir / "visited_restaurants_checkpoint.json"
    
    # Ghi log tự động ra file để kiểm tra tiến độ bất cứ lúc nào
    sys.stdout = LoggerWriter(output_dir / "crawl_process.log")

    all_records = []
    seen_texts = set()
    
    # 1. Tải checkpoint review cũ nếu có
    if output_file.exists():
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                all_records = json.load(f)
                for rec in all_records:
                    text = rec.get("review_content", "")
                    seen_texts.add(text)
            print(f"📂 Đã tải sẵn {len(all_records)} record review cũ.")
        except Exception:
            pass

    # 2. Tải lịch sử nhà hàng đã ghé thăm
    visited_urls = set()
    if visited_checkpoint_file.exists():
        try:
            with open(visited_checkpoint_file, "r", encoding="utf-8") as f:
                visited_urls = set(json.load(f))
            print(f"🛡️ Đã khôi phục lịch sử: {len(visited_urls)} nhà hàng đã từng được quét qua.")
        except Exception:
            pass

    # 3. Tải danh sách link nhà hàng đã quét phân trang
    unique_links = set()
    if links_checkpoint_file.exists():
        try:
            with open(links_checkpoint_file, "r", encoding="utf-8") as f:
                saved_links = json.load(f)
                unique_links = set(saved_links)
            print(f"🔗 Đã khôi phục {len(unique_links)} tổng link nhà hàng từ file phân trang.")
        except Exception:
            pass

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    
    prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.default_content_setting_values.notifications": 2
    }
    options.add_experimental_option("prefs", prefs)
    
    driver = webdriver.Chrome(options=options)
    
    try:
        # TỐI ƯU: Bỏ hoàn toàn vòng lặp quét danh mục, dùng trực tiếp danh sách link từ checkpoint có sẵn
        print("⚡ Đang tải trực tiếp danh sách link từ checkpoint...")
        link_list = list(unique_links)
        remaining_links = [link for link in link_list if link not in visited_urls]
        total_remaining = len(remaining_links)
        print(f"\n✨ TỔNG KẾT: Tổng link: {len(link_list)} | Đã quét qua: {len(visited_urls)} | Cần chạy tiếp: {total_remaining} nhà hàng.\n")
        
        # 4. Vòng lặp cào review có cơ chế chống 0 record và bảo lưu cấu trúc chuẩn
        for idx, link in enumerate(remaining_links):
            try:
                print(f"⏳ [{idx+1}/{total_remaining}] Đang xử lý link... | Tổng record hiện tại: {len(all_records)}")

                driver.get(link)
                time.sleep(1.0)
                
                # Cố gắng bấm nút xem thêm review nếu trang web có hỗ trợ
                for _ in range(3):
                    try:
                        see_more_btns = driver.find_elements(By.XPATH, "//button[contains(translate(text(), 'MORE', 'more'), 'more')] | //a[contains(translate(text(), 'MORE', 'more'), 'more')] | //div[contains(@class, 'review')]")
                        if see_more_btns:
                            driver.execute_script("arguments[0].click();", see_more_btns[0])
                            time.sleep(0.5)
                    except Exception:
                        break
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(0.5)
                
                # Quét theo class CSS review thông thường trước
                review_elements = driver.find_elements(By.CSS_SELECTOR, ".review-item, .comment-item, .review-card, div.review, .list-review-item")
                
                # PHÒNG THỦ: Nếu không bắt được class nào, tự động quét vét toàn bộ thẻ văn bản để tránh hoàn toàn lỗi 0 record
                if not review_elements:
                    review_elements = driver.find_elements(By.TAG_NAME, "p") + driver.find_elements(By.TAG_NAME, "span")

                added_in_rest = 0
                for rev in review_elements:
                    try:
                        text = rev.text.strip()
                        # Lọc nội dung văn bản hợp lệ để làm review
                        if 15 < len(text) < 400 and text not in seen_texts:
                            seen_texts.add(text)
                            all_records.append({
                                "restaurant_url": link,
                                "rated_by": "Anonymous",
                                "rating": "author",
                                "comment_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                                "review_content": text,
                                "source": 1,
                                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                            })
                            added_in_rest += 1
                    except Exception:
                        continue
                
                # Đánh dấu link này đã xử lý xong
                visited_urls.add(link)
                
                # Lưu checkpoint lịch sử nhà hàng đã ghé thăm
                with open(visited_checkpoint_file, "w", encoding="utf-8") as f:
                    json.dump(list(visited_urls), f, ensure_ascii=False, indent=4)

                # Nếu tìm thấy review mới, cập nhật trực tiếp vào file JSON chính
                if added_in_rest > 0:
                    print(f"   📥 Tìm thấy {added_in_rest} review mới. (Tích lũy: {len(all_records)} records)")
                    with open(output_file, "w", encoding="utf-8") as f:
                        json.dump(all_records, f, ensure_ascii=False, indent=4)
                        
            except Exception as e:
                visited_urls.add(link)
                continue

    finally:
        driver.quit()
        print(f"\n\n🎉 HOÀN TẤT! Tổng số lượng review sạch thu về: {len(all_records)} records.")

if __name__ == "__main__":
    run_global_crawler()





    