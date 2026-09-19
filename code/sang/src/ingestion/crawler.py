import csv
import json
from datetime import datetime
import time
import urllib.parse
import urllib.request


def crawl_foody_reviews(
    res_id, restaurant_name, city, total_reviews, target_reviews=50
):
  url = 'https://www.foody.vn/__get/Review/ResLoadMore'

  headers = {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
      'Accept': 'application/json, text/plain, */*',
      'X-Requested-With': 'XMLHttpRequest',
  }

  all_reviews = []
  last_id = ''

  print(f'Đang thu thập đủ {target_reviews} dòng cho quán: {restaurant_name}...')

  while len(all_reviews) < target_reviews:
    params = {
        't': str(int(time.time() * 1000)),
        'ResId': str(res_id),
        'LastId': str(last_id),
        'Count': '20',
        'Type': '1',
        'isLatest': 'true',
    }
    
    all_reviews = []
    last_id = "" 
    
    print(f"Đang thu thập đủ {target_reviews} dòng cho quán: {restaurant_name}...")
    
    while len(all_reviews) < target_reviews:
        params = {
            't': str(int(time.time() * 1000)), 
            'ResId': str(res_id),
            'LastId': str(last_id),
            'Count': '20', 
            'Type': '1',
            'isLatest': 'true'
        }
        
        query_string = urllib.parse.urlencode(params)
        full_url = f"{url}?{query_string}"
        
        try:
            req = urllib.request.Request(full_url, headers=headers)
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode('utf-8'))
                items = data.get('Items', [])
                
                if not items:
                    break
                    
                for item in items:
                    review_date = item.get('CreatedOnTimeDiff') or item.get('CreatedDate') or ''
                    
                    review_record = {
                        'source': 'Foody',
                        'restaurant_id': res_id,
                        'restaurant_name': restaurant_name,
                        'restaurant_url': f"https://www.foody.vn/quang-binh/{restaurant_name.lower().replace(' ', '-')}-{res_id}",
                        'city': city,
                        'category': 'Quán ăn / Đặc sản',
                        'total_reviews': total_reviews,
                        'review_id': item.get('Id'),
                        'review_text': item.get('Description', '').strip(), 
                        'rating': item.get('AvgRating', 0),
                        'review_date': review_date
                    }
                    all_reviews.append(review_record)
                    last_id = item.get('Id')
                    
                    if len(all_reviews) >= target_reviews:
                        break
                
                time.sleep(1) 
                
        except Exception as e:
            print(f"Lỗi: {e}")
            break

        
              
    return all_reviews


def main():
  restaurants = [
      {
          'id': 272138,
          'name': 'Gà Chỉ Sáu Cao',
          'city': 'Quy Nhơn',
          'total_reviews': 272,
      },
      {
          'id': 138063,
          'name': 'Mộc Viên Restaurant',
          'city': 'Quy Nhơn',
          'total_reviews': 93,
      },
  ]

  dataset = []
  for res in restaurants:
    reviews = crawl_foody_reviews(
        res['id'],
        res['name'],
        res['city'],
        res['total_reviews'],
        target_reviews=50,
    )
    dataset.extend(reviews)

  if dataset:
    # 1. Định nghĩa đầy đủ danh sách trường (Schema chuẩn Week 2)
    fieldnames = [
        'source',
        'restaurant_id',
        'restaurant_name',
        'restaurant_url',
        'city',
        'category',
        'total_reviews',
        'restaurant_rating',
        'review_id',
        'reviewer_id',
        'review_text',
        'rating',
        'review_date',
        'crawl_timestamp',
    ]

    # 2. Xuất file CSV
    csv_filename = 'foody_sample_data.csv'
    with open(csv_filename, 'w', newline='', encoding='utf-8-sig') as output_file:
      dict_writer = csv.DictWriter(output_file, fieldnames=fieldnames)
      dict_writer.writeheader()
      dict_writer.writerows(dataset)
    print(
        f"\n✅ HOÀN TẤT! Đã lưu file CSV '{csv_filename}' với {len(dataset)}"
        ' dòng.'
    )

    # 3. Tự động chuyển đổi từ dữ liệu sang file JSON
    json_filename = 'foody_sample_data.json'
    with open(json_filename, 'w', encoding='utf-8') as json_file:
      json.dump(dataset, json_file, ensure_ascii=False, indent=4)
    print(
        f"✅ HOÀN TẤT! Đã xuất thêm file JSON '{json_filename}' thành công!"
    )


if __name__ == '__main__':
  main()