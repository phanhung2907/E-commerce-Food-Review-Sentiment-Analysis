# Database Schema Design — 3NF

## 1. Nguyên tắc

Schema được chuẩn hóa đến **Third Normal Form (3NF)**.

```text
sources
   │
   ├──< restaurants
   │       ├──< restaurant_opening_hours
   │       └──< restaurant_cuisines
   │
   ├──< reviewers
   │
   └──< reviews
           └──< review_tags
```

Các quyết định chính:

- Bỏ `canonical_url`: không cần thiết cho phân tích; `source + source_restaurant_id + url` đã đủ để nhận diện restaurant, raw data vẫn nằm trong MinIO.
- Không dùng `JSONB`.
- Không lưu ảnh hoặc URL ảnh.
- Giữ các field đếm ảnh như `total_pictures`.
- Không lưu danh sách nhiều giá trị trong một cột `TEXT`.
- `opening_hours`, `cuisines`, `tags` được tách thành bảng riêng.
- Metadata của reviewer được tách khỏi `reviews` để tránh lặp lại trên nhiều review.
- `rating_scale_max` được đặt ở `sources` vì thang điểm phụ thuộc vào platform, không phụ thuộc từng restaurant/review.
- Feature không có ở source → `NULL`.

---

## 2. `sources`

Quản lý nhãn source chuẩn và ngăn sai syntax khi ETL/insert.

| Column | Type | Null | Mô tả |
|---|---|---|---|
| `source_code` | `VARCHAR(30)` | NOT NULL | Primary Key; nhãn source chuẩn |
| `rating_scale_max` | `NUMERIC(4,2)` | NULL | Điểm tối đa của thang rating của source |

Giá trị `source_code` hiện tại:

```text
foody
tripadvisor
eatigo
capichi
```

Không được dùng biến thể như `Foody`, `FOODY`, `TripAdvisor`, `foody_shoppefood`, ...

---

## 3. `restaurants`

Một record tương ứng một restaurant trên một source.

| Column | Type | Null | Mô tả |
|---|---|---|---|
| `source_code` | `VARCHAR(30)` | NOT NULL | Source chứa restaurant |
| `source_restaurant_id` | `TEXT` | NOT NULL | ID restaurant gốc trên source |
| `name` | `TEXT` | NULL | Tên restaurant |
| `url` | `TEXT` | NULL | URL restaurant trên source |
| `city` | `TEXT` | NULL | Tỉnh/thành phố |
| `address` | `TEXT` | NULL | Địa chỉ |
| `category` | `TEXT` | NULL | Category/nhóm restaurant nếu source có |
| `location` | `TEXT` | NULL | Khu vực/location chi tiết hơn `city` nếu source có |
| `avg_rating` | `NUMERIC(4,2)` | NULL | Rating trung bình của restaurant |
| `total_reviews` | `INTEGER` | NULL | Tổng số review platform báo cho restaurant |
| `latitude` | `NUMERIC(9,6)` | NULL | Vĩ độ |
| `longitude` | `NUMERIC(9,6)` | NULL | Kinh độ |
| `price_range` | `TEXT` | NULL | Khoảng giá/mức giá |
| `telephone` | `TEXT` | NULL | Số điện thoại |
| `crawl_timestamp` | `TIMESTAMPTZ` | NOT NULL | Thời điểm dữ liệu restaurant được crawl |
| `raw_object_key` | `TEXT` | NOT NULL | Object key tương đối trỏ đến raw object trong MinIO |

Primary Key:

```sql
PRIMARY KEY (source_code, source_restaurant_id)
```

---

## 4. `restaurant_opening_hours`

Tách `opening_hours` khỏi `restaurants` để mỗi record chỉ chứa một khoảng giờ mở cửa.

| Column | Type | Null | Mô tả |
|---|---|---|---|
| `source_code` | `VARCHAR(30)` | NOT NULL | Source của restaurant |
| `source_restaurant_id` | `TEXT` | NOT NULL | Restaurant tương ứng |
| `day_of_week` | `SMALLINT` | NOT NULL | Ngày trong tuần: `1=Monday` ... `7=Sunday` |
| `period_no` | `SMALLINT` | NOT NULL | Thứ tự khoảng giờ trong ngày; hỗ trợ restaurant mở nhiều ca |
| `open_time` | `TIME` | NULL | Giờ mở cửa |
| `close_time` | `TIME` | NULL | Giờ đóng cửa |
| `is_closed` | `BOOLEAN` | NOT NULL | `TRUE` nếu restaurant nghỉ ngày đó |

Primary Key:

```sql
PRIMARY KEY (
    source_code,
    source_restaurant_id,
    day_of_week,
    period_no
)
```

---

## 5. `restaurant_cuisines`

Một restaurant có thể phục vụ nhiều loại ẩm thực.

| Column | Type | Null | Mô tả |
|---|---|---|---|
| `source_code` | `VARCHAR(30)` | NOT NULL | Source của restaurant |
| `source_restaurant_id` | `TEXT` | NOT NULL | Restaurant tương ứng |
| `cuisine` | `TEXT` | NOT NULL | Một loại ẩm thực, ví dụ `Vietnamese`, `Asian`, `Street Food` |

Primary Key:

```sql
PRIMARY KEY (
    source_code,
    source_restaurant_id,
    cuisine
)
```

---

## 6. `reviewers`

Metadata cấp reviewer được lưu một lần thay vì lặp lại ở mọi review.

| Column | Type | Null | Mô tả |
|---|---|---|---|
| `source_code` | `VARCHAR(30)` | NOT NULL | Source chứa reviewer |
| `reviewer_id` | `TEXT` | NOT NULL | ID reviewer gốc trên source |
| `reviewer_name` | `TEXT` | NULL | Tên hiển thị |
| `total_reviews` | `INTEGER` | NULL | Tổng số review reviewer đã đăng theo metadata của platform |
| `total_pictures` | `INTEGER` | NULL | Tổng số ảnh reviewer đã đăng; chỉ lưu số lượng |
| `trust_percent` | `NUMERIC(5,2)` | NULL | `TrustPercent` do Foody trả về; source hiện tại không mô tả rõ công thức tính |
| `verifying_percent` | `NUMERIC(5,2)` | NULL | `VerifyingPercent` do Foody trả về; source hiện tại không mô tả rõ công thức tính |
| `is_verified` | `BOOLEAN` | NULL | Platform có đánh dấu reviewer là verified hay không |

Primary Key:

```sql
PRIMARY KEY (source_code, reviewer_id)
```

---

## 7. `reviews`

Một restaurant có nhiều reviews.

| Column | Type | Null | Mô tả |
|---|---|---|---|
| `source_code` | `VARCHAR(30)` | NOT NULL | Source chứa review |
| `source_review_id` | `TEXT` | NOT NULL | ID review gốc trên source |
| `source_restaurant_id` | `TEXT` | NOT NULL | Restaurant mà review thuộc về |
| `reviewer_id` | `TEXT` | NULL | Reviewer tương ứng; `NULL` nếu source không cung cấp ID |
| `reviewer_name_raw` | `TEXT` | NULL | Tên reviewer gắn trực tiếp với review khi source chỉ cung cấp tên nhưng không có reviewer ID |
| `review_title` | `TEXT` | NULL | Tiêu đề review |
| `review_text` | `TEXT` | NULL | Nội dung review |
| `rating` | `NUMERIC(4,2)` | NULL | Điểm rating của review |
| `review_date` | `TIMESTAMPTZ` | NULL | Thời điểm review được đăng |
| `travel_date` | `DATE` | NULL | Ngày trải nghiệm nếu source có |
| `language` | `VARCHAR(10)` | NULL | Mã ngôn ngữ, ví dụ `vi`, `en`, `ja`, `ko` |
| `device_name` | `TEXT` | NULL | Thiết bị dùng để đăng review nếu source có |
| `total_views` | `INTEGER` | NULL | Tổng lượt xem review |
| `total_pictures` | `INTEGER` | NULL | Số ảnh đính kèm; không lưu ảnh |
| `total_likes` | `INTEGER` | NULL | Tổng lượt thích |
| `total_comments` | `INTEGER` | NULL | Tổng số comment/phản hồi |
| `guest_count` | `TEXT` | NULL | Số lượng khách từ source, ví dụ `2+` |
| `visit_again` | `TEXT` | NULL | Ý định quay lại, ví dụ `Chắc chắn`, `Có thể` |
| `money_spend` | `TEXT` | NULL | Mức chi tiêu, ví dụ `150,000đ +` |
| `feature_depth_status` | `TEXT` | NULL | Nhãn completeness nếu crawler/source có |

Primary Key:

```sql
PRIMARY KEY (source_code, source_review_id)
```

Foreign Keys:

```sql
FOREIGN KEY (source_code, source_restaurant_id)
    REFERENCES restaurants(source_code, source_restaurant_id)

FOREIGN KEY (source_code, reviewer_id)
    REFERENCES reviewers(source_code, reviewer_id)
```

`reviewer_id` được phép `NULL`.

---

## 8. `review_tags`

Một review có thể có nhiều tags.

| Column | Type | Null | Mô tả |
|---|---|---|---|
| `source_code` | `VARCHAR(30)` | NOT NULL | Source của review |
| `source_review_id` | `TEXT` | NOT NULL | Review tương ứng |
| `tag` | `TEXT` | NOT NULL | Một tag của review |

Primary Key:

```sql
PRIMARY KEY (source_code, source_review_id, tag)
```

---

## 9. PostgreSQL DDL

```sql
CREATE TABLE sources (
    source_code VARCHAR(30) PRIMARY KEY,
    rating_scale_max NUMERIC(4,2)
);


CREATE TABLE restaurants (
    source_code VARCHAR(30) NOT NULL,
    source_restaurant_id TEXT NOT NULL,

    name TEXT,
    url TEXT,
    city TEXT,
    address TEXT,
    category TEXT,
    location TEXT,

    avg_rating NUMERIC(4,2),
    total_reviews INTEGER,

    latitude NUMERIC(9,6),
    longitude NUMERIC(9,6),

    price_range TEXT,
    telephone TEXT,

    crawl_timestamp TIMESTAMPTZ NOT NULL,
    raw_object_key TEXT NOT NULL,

    PRIMARY KEY (source_code, source_restaurant_id),

    FOREIGN KEY (source_code)
        REFERENCES sources(source_code)
);


CREATE TABLE restaurant_opening_hours (
    source_code VARCHAR(30) NOT NULL,
    source_restaurant_id TEXT NOT NULL,

    day_of_week SMALLINT NOT NULL,
    period_no SMALLINT NOT NULL DEFAULT 1,

    open_time TIME,
    close_time TIME,
    is_closed BOOLEAN NOT NULL DEFAULT FALSE,

    PRIMARY KEY (
        source_code,
        source_restaurant_id,
        day_of_week,
        period_no
    ),

    FOREIGN KEY (source_code, source_restaurant_id)
        REFERENCES restaurants(source_code, source_restaurant_id),

    CHECK (day_of_week BETWEEN 1 AND 7)
);


CREATE TABLE restaurant_cuisines (
    source_code VARCHAR(30) NOT NULL,
    source_restaurant_id TEXT NOT NULL,
    cuisine TEXT NOT NULL,

    PRIMARY KEY (
        source_code,
        source_restaurant_id,
        cuisine
    ),

    FOREIGN KEY (source_code, source_restaurant_id)
        REFERENCES restaurants(source_code, source_restaurant_id)
);


CREATE TABLE reviewers (
    source_code VARCHAR(30) NOT NULL,
    reviewer_id TEXT NOT NULL,

    reviewer_name TEXT,
    total_reviews INTEGER,
    total_pictures INTEGER,

    trust_percent NUMERIC(5,2),
    verifying_percent NUMERIC(5,2),
    is_verified BOOLEAN,

    PRIMARY KEY (source_code, reviewer_id),

    FOREIGN KEY (source_code)
        REFERENCES sources(source_code)
);


CREATE TABLE reviews (
    source_code VARCHAR(30) NOT NULL,
    source_review_id TEXT NOT NULL,
    source_restaurant_id TEXT NOT NULL,

    reviewer_id TEXT,
    reviewer_name_raw TEXT,

    review_title TEXT,
    review_text TEXT,
    rating NUMERIC(4,2),

    review_date TIMESTAMPTZ,
    travel_date DATE,
    language VARCHAR(10),
    device_name TEXT,

    total_views INTEGER,
    total_pictures INTEGER,
    total_likes INTEGER,
    total_comments INTEGER,

    guest_count TEXT,
    visit_again TEXT,
    money_spend TEXT,

    feature_depth_status TEXT,

    PRIMARY KEY (source_code, source_review_id),

    FOREIGN KEY (source_code)
        REFERENCES sources(source_code),

    FOREIGN KEY (source_code, source_restaurant_id)
        REFERENCES restaurants(source_code, source_restaurant_id),

    FOREIGN KEY (source_code, reviewer_id)
        REFERENCES reviewers(source_code, reviewer_id)
);


CREATE TABLE review_tags (
    source_code VARCHAR(30) NOT NULL,
    source_review_id TEXT NOT NULL,
    tag TEXT NOT NULL,

    PRIMARY KEY (
        source_code,
        source_review_id,
        tag
    ),

    FOREIGN KEY (source_code, source_review_id)
        REFERENCES reviews(source_code, source_review_id)
);


CREATE INDEX idx_restaurants_city
    ON restaurants(city);

CREATE INDEX idx_reviews_restaurant
    ON reviews(source_code, source_restaurant_id);

CREATE INDEX idx_reviews_review_date
    ON reviews(review_date);
```

---

## 10. Source labels

Dữ liệu chuẩn ban đầu:

```sql
INSERT INTO sources (source_code, rating_scale_max) VALUES
    ('foody', 10),
    ('tripadvisor', 5),
    ('eatigo', 5),
    ('capichi', 5);
```

Mọi crawler và ETL phải map về đúng `source_code` này trước khi insert vào PostgreSQL.
