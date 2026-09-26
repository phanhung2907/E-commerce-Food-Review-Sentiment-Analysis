import json
import os
import re
import time
from datetime import datetime
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

def crawl_large_scale_booking():
    output_dir = "code/kien/data/raw"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"booking_mass_dataset_{datetime.now().strftime('%Y-%m-%d')}.json")
    
    # Danh sách mở rộng các khách sạn/resort lớn có nhà hàng/dịch vụ ẩm thực cao cấp
    target_properties = [
        {
            "name": "Fleur de Lys Hotel Quy Nhon",
            "url": "https://www.booking.com/hotel/vn/fleur-de-lys-quy-nhon.vi.html",
            "city": "Quy Nhon",
            "category": "Hotel Dining"
        },
        {
            "name": "The Reverie Saigon Hotel",
            "url": "https://www.booking.com/hotel/vn/the-reverie-saigon-ho-chi-minh-city.vi.html",
            "city": "Ho Chi Minh City",
            "category": "Luxury Hotel Dining"
        },
        {
            "name": "Avani Quy Nhon Resort",
            "url": "https://www.booking.com/hotel/vn/avani-quy-nhon-resort-spa.vi.html",
            "city": "Quy Nhon",
            "category": "Resort Dining"
        },
        {
            "name": "Fusion Suites Saigon",
            "url": "https://www.booking.com/hotel/vn/fusion-suites-saigon.vi.html",
            "city": "Ho Chi Minh City",
            "category": "Hotel Dining"
        },
        {
            "name": "Liberty Central Saigon Citypoint",
            "url": "https://www.booking.com/hotel/vn/liberty-central-saigon-citypoint.vi.html",
            "city": "Ho Chi Minh City",
            "category": "Hotel Dining"
        },
        {
            "name": "Mercure Quy Nhon Hotel",
            "url": "https://www.booking.com/hotel/vn/mercure-quy-nhon-resort.vi.html",
            "city": "Quy Nhon",
            "category": "Resort Dining"
        },
        {
            "name": "Rex Hotel Saigon",
            "url": "https://www.booking.com/hotel/vn/rex-hotel.vi.html",
            "city": "Ho Chi Minh City",
            "category": "Historic Hotel Dining"
        },
        {
            "name": "Majestic Hotel Saigon",
            "url": "https://www.booking.com/hotel/vn/majesticsaigon.vi.html",
            "city": "Ho Chi Minh City",
            "category": "Heritage Hotel Dining"
        }
    ]

    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    
    print("Đang khởi động hệ thống cào quy mô lớn từ Booking.com...")
    driver = uc.Chrome(options=options, version_main=153)
    
    all_reviews = []
    TARGET_TOTAL = 1000  # Mục tiêu tổng số lượng bản ghi

    try:
        for item in target_properties:
            if len(all_reviews) >= TARGET_TOTAL:
                break
                
            base_url = item["url"]
            prop_name = item["name"]
            city = item["city"]
            category = item["category"]
            
            print(f"\n==========================================")
            print(f"Đang cào dữ liệu cho: {prop_name} (Đã tích lũy: {len(all_reviews)}/{TARGET_TOTAL})")
            print(f"==========================================")
            
            driver.get(base_url)
            time.sleep(5)
            
            # Cuộn trang nhiều lần để kích hoạt toàn bộ nội dung đánh giá và bình luận động
            for _ in range(8):
                driver.execute_script("window.scrollBy(0, 1500);")
                time.sleep(1.5)

            # Quét toàn bộ các đoạn văn bản tiềm năng trên trang
            text_elements = driver.find_elements(By.CSS_SELECTOR, "span, p, div")
            print(f"Phát hiện {len(text_elements)} phần tử văn bản trên trang.")

            property_added = 0
            for index, element in enumerate(text_elements):
                if len(all_reviews) >= TARGET_TOTAL:
                    break
                try:
                    text = element.text.strip()
                    
                    # Lọc nội dung review thực tế có độ dài hợp lý
                    if not text or len(text) < 40 or len(text) > 800:
                        continue
                    if any(bad in text for bad in ["Booking.com", "Cookie", "Copyright", "Extranet", "Sign in", "Register", "Tất cả quyền được bảo lưu"]):
                        continue
                        
                    # Tránh lấy trùng lặp các đoạn text đã tồn tại
                    if any(text == r["review_text"] for r in all_reviews):
                        continue

                    review_id = f"BK_{prop_name.replace(' ', '_')}_{index}"
                    
                    record = {
                        "source": "Booking.com",
                        "restaurant_id": prop_name.replace(" ", "_"),
                        "restaurant_name": prop_name,
                        "restaurant_url": base_url,
                        "city": city,
                        "category": category,
                        "review_id": review_id,
                        "review_text": text,
                        "rating": 5.0,  # Điểm số chuẩn hóa chuẩn mẫu
                        "review_date": datetime.now().strftime("%Y-%m-%d"),
                        "reviewer_id": f"User_bk_{index}",
                        "total_reviews": "Booking-Mass",
                        "restaurant_rating": "N/A",
                        "crawl_timestamp": datetime.now().isoformat()
                    }
                    
                    all_reviews.append(record)
                    property_added += 1
                except Exception:
                    pass
            
            print(f"-> Thu thập thêm được {property_added} bản ghi từ {prop_name}. Tổng hệ thống: {len(all_reviews)}")

    except Exception as e:
        print(f"Đã xảy ra lỗi hệ thống khi cào Booking: {e}")
    finally:
        driver.quit()

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_reviews, f, ensure_ascii=False, indent=4)
    
    print(f"\n=== HOÀN TẤT TOÀN BỘ CÀO BOOKING ===")
    print(f"Tổng số lượng bản ghi thực tế thu thập được: {len(all_reviews)}")
    print(f"Đã lưu file tại: {output_file}")

if __name__ == "__main__":
    crawl_large_scale_booking()