import csv
import json
from datetime import datetime
import time
import urllib.parse
import urllib.request

def crawl_foody_reviews(res_id, restaurant_name, city, total_reviews, target_reviews=50):
    url = 'https://www.foody.vn/__get/Review/ResLoadMore'
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Accept': 'application/json, text/plain, */*',
        'X-Requested-With': 'XMLHttpRequest',
    }

    all_reviews = []
    last_id = ''
    
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
                    # Gom toàn bộ dữ liệu thô từ item của API trả về để không bỏ sót bất kỳ feature nào
                    review_record = {
                        'source': 'Foody',
                        'restaurant_id': res_id,
                        'restaurant_name': restaurant_name,
                        'restaurant_url': f"https://www.foody.vn/quang-binh/{restaurant_name.lower().replace(' ', '-')}-{res_id}",
                        'city': city,
                        'category': 'Quán ăn / Đặc sản',
                        'total_reviews': total_reviews,
                        # Các trường mở rộng chi tiết từ API web
                        'review_id': item.get('Id'),
                        'title': item.get('Title'),
                        'description': item.get('Description', '').strip(),
                        'type': item.get('Type'),
                        'type_name': item.get('TypeName'),
                        'created_date': item.get('CreatedDate'),
                        'created_on_time_diff': item.get('CreatedOnTimeDiff'),
                        'device_name': item.get('DeviceName'),
                        'device_url': item.get('DeviceUrl'),
                        'device_type': item.get('DeviceType'),
                        'is_allow_comment': item.get('IsAllowComment'),
                        'has_thit_cay': item.get('HasThitCay'),
                        'total_views': item.get('TotalViews'),
                        'total_pictures': item.get('TotalPictures'),
                        'avg_rating': item.get('AvgRating'),
                        'video': json.dumps(item.get('Video')) if item.get('Video') else None,
                        'hashtags': json.dumps(item.get('Hashtags')) if item.get('Hashtags') else None,
                        'pictures': json.dumps(item.get('Pictures')) if item.get('Pictures') else None,
                        'owner_info': json.dumps(item.get('Owner')) if item.get('Owner') else None,
                        'restaurant_rating': item.get('AvgRating', 0),
                        'rating': item.get('AvgRating', 0),
                        'review_date': item.get('CreatedOnTimeDiff') or item.get('CreatedDate') or '',
                        'crawl_timestamp': datetime.now().isoformat()
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
        {'id': 272138, 'name': 'Gà Chỉ Sáu Cao', 'city': 'Quy Nhơn', 'total_reviews': 272},
        {'id': 138063, 'name': 'Mộc Viên Restaurant', 'city': 'Quy Nhơn', 'total_reviews': 93}
    ]

    dataset = []
    for res in restaurants:
        reviews = crawl_foody_reviews(res['id'], res['name'], res['city'], res['total_reviews'], target_reviews=50)
        dataset.extend(reviews)

    if dataset:
        # Xuất file JSON chứa toàn bộ dữ liệu vét sạch
        json_filename = 'foody_sample_data.json'
        with open(json_filename, 'w', encoding='utf-8') as json_file:
            json.dump(dataset, json_file, ensure_ascii=False, indent=4)
        print(f"\n✅ Đã cào và xuất thành công file '{json_filename}' với đầy đủ mọi features từ web!")

if __name__ == '__main__':
    main()