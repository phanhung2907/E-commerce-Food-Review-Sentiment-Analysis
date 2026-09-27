import requests
import time

all_product_ids = set()

# Headers giả lập trình duyệt thật để tránh bị chặn
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://eatigo.com/"
}

regions = [29, 30]  # Các khu vực chính
categories = [14317, 14318, 14319, 14320]  # Các danh mục món ăn

print("Đang tiến hành tự động quét danh sách ID nhà hàng an toàn...")

session = requests.Session()
session.headers.update(headers)

for reg in regions:
    for cat in categories:
        for start in range(0, 200, 21):
            url = f"https://eatigo.com/v2/eatigo/restaurant/filter?region_id={reg}&size=21&start={start}&category_id={cat}"
            
            try:
                response = session.get(url, timeout=5)
                
                # Nếu bị dính lỗi rate-limit (Error 10), cho code ngủ dài hơn một chút rồi thử lại
                if response.status_code != 200 or "Error" in response.text:
                    print("Gặp giới hạn từ server, đang tạm nghỉ 3 giây...")
                    time.sleep(3)
                    continue
                    
                data = response.json()
                restaurants = data.get("data", {}).get("restaurants", [])
                
                if not restaurants:
                    break
                    
                for r in restaurants:
                    p_id = r.get("product_id") or r.get("id") or r.get("restaurant_id")
                    if p_id:
                        all_product_ids.add(str(p_id))
                        
                # Nghỉ ngắn 1 giây để quét nhanh nhưng vẫn an toàn không bị chặn
                time.sleep(1)
            except Exception as e:
                time.sleep(2)
                break

id_list = list(all_product_ids)
print(f"Đã tự động quét thành công tổng cộng: {len(id_list)} ID nhà hàng độc nhất!")

# Tự động lưu thẳng ra file text để crawler chính đọc
with open("product_ids.txt", "w", encoding="utf-8") as f:
    for pid in id_list:
        f.write(pid + "\n")

print("Đã lưu toàn bộ ID vào file product_ids.txt thành công!")