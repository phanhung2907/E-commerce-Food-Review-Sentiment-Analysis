## Nhật ký làm việc với AI - Cào dữ liệu Foody

**Mục tiêu:** 
Hoàn thành Source Feasibility Check cho nguồn Foody: Tìm API, kiểm tra phân trang và viết script lấy hơn 100 sample reviews.

**Quá trình thực hiện:**
1. Mở Developer Tools (F12) > Tab Network > Fetch/XHR.
2. Tìm được request API: `[https://www.foody.vn/__get/Review/ResLoadMore](https://www.foody.vn/__get/Review/ResLoadMore)`.
3. Xác định được cơ chế phân trang (pagination) thông qua tham số `LastId` trong Payload.
4. Trích xuất thành công các field bắt buộc: `review_text`, `rating`, `review_date`, `restaurant_id`, `total_reviews`, `city`.

**Đoạn code Crawler hoàn chỉnh (Python):**

```python
import requests
import pandas as pd
import time

def crawl_foody_reviews(res_id, restaurant_name, city, total_reviews, target_reviews=100):
    url = "https://www.foody.vn/__get/Review/ResLoadMore"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Accept': 'application/json, text/plain, */*',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    all_reviews = []
    last_id = "" 
    
    while len(all_reviews) < target_reviews:
        params = {
            't': int(time.time() * 1000), 
            'ResId': res_id,
            'LastId': last_id,
            'Count': 20, 
            'Type': 1,
            'isLatest': 'true'
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code != 200:
                break
                
            data = response.json()
            items = data.get('Items', [])
            
            if not items:
                break
                
            for item in items:
                review_record = {
                    'source': 'Foody',
                    'restaurant_id': res_id,
                    'restaurant_name': restaurant_name,
                    'city': city,
                    'total_reviews': total_reviews,
                    'review_id': item.get('Id'),
                    'review_text': item.get('Description', '').strip(), 
                    'rating': item.get('AvgRating', 0),
                    'review_date': item.get('CreatedOn', '')
                }
                all_reviews.append(review_record)
                last_id = item.get('Id')
                
                if len(all_reviews) >= target_reviews:
                    break
                    
            time.sleep(1.5) 
            
        except Exception as e:
            break
            
    return all_reviews

def main():
    restaurants = [
        {'id': 272138, 'name': 'Gà Chỉ Sáu Cao', 'city': 'Quy Nhơn', 'total_reviews': 272},
        {'id': 123456, 'name': 'Bún Bò Quế', 'city': 'Quy Nhơn', 'total_reviews': 150},
        {'id': 654321, 'name': 'Bánh Xèo Tôm Nhảy', 'city': 'Quy Nhơn', 'total_reviews': 320}
    ]
    
    dataset = []
    for res in restaurants:
        reviews = crawl_foody_reviews(res['id'], res['name'], res['city'], res['total_reviews'], target_reviews=40)
        dataset.extend(reviews)
        
    if dataset:
        df = pd.DataFrame(dataset)
        df.to_csv('foody_sample_data.csv', index=False, encoding='utf-8-sig')

if __name__ == "__main__":
    main()
```
