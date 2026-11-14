# Nhập dữ liệu Kiên, Sang và Tuấn

Giải nén để thư mục `external_data` nằm trong `E:\Real-estate-tourism\hung\code\hung\src`. Chạy lệnh từ `E:\Real-estate-tourism\hung` với môi trường `uv` của repo. Các script dùng cấu hình MinIO và PostgreSQL hiện có trong `.env`. Kiểm tra `POSTGRES_HOST`, `POSTGRES_PORT` và `POSTGRES_DB` trỏ đúng database đích. Bucket và schema 3NF cần có sẵn.

| Thành viên | Dữ liệu được đọc |
|---|---|
| Kiên | JSON từng quán trong `data-kien/data/raw/single_restaurants`. |
| Sang | JSON từng quán trong `data-sang/data/raw/eatigo_copy/raw/single_restaurants` và `eatigo_split`. Bản `final` có các ID đã có trong hai thư mục trên. Bản `master` chứa ID kiểu `rev_sel_304` và thiếu thông tin xác thực nguồn của các ID, nên được để ngoài lần nhập này. |
| Tuấn | Các file `capichi_final_*.json` và `befood_final_*.json` trong `data-tuan/data/raw`. Mỗi file final được lưu nguyên bản trên MinIO. |

## Chạy

```powershell
Set-Location 'E:\Real-estate-tourism\hung'
$scripts = 'code/hung/src/external_data'
foreach ($owner in 'kien', 'sang', 'tuan') {
    uv run python "$scripts/upload_minIO_${owner}.py"
    if ($LASTEXITCODE -ne 0) { throw "Upload failed for $owner" }
    uv run python "$scripts/minio_to_postgres_${owner}.py"
    if ($LASTEXITCODE -ne 0) { throw "PostgreSQL import failed for $owner" }
}
uv run python "$scripts/export_database_csv.py" --output database-merge-data
```

Có thể chạy từng cặp lệnh. Uploader ghi `import-<tên>.json` vào thư mục hiện hành. Loader xác thực SHA-256 của các object được chọn trong manifest và commit toàn bộ một lần nhập thành viên trong một transaction. Nếu có lỗi, transaction của lần nhập đó được rollback. Các khóa chính đã có được giữ nguyên, các khóa mới được thêm. `rows_read` đếm dòng đầu vào và `rows_inserted` đếm dòng mới. Thêm `--dry-run` vào lệnh loader để thử SQL và rollback khi kết thúc.

Loader của Tuấn đăng ký BeFood thang điểm 5 và mở rộng ràng buộc `sources.chk_source_code` trong cùng transaction nếu cần. Nếu schema dùng ràng buộc này, tài khoản PostgreSQL cần quyền ALTER bảng `sources`. Review BeFood thiếu ID dùng SHA-256 của ID quán, nội dung và điểm để tạo khóa ổn định. Tên “Ẩn danh” không được dùng làm khóa người dùng. Nhãn sentiment và các cờ đặc trưng của BeFood được giữ trong JSON trên MinIO.

Exporter tạo một CSV UTF-8 có header cho mỗi bảng cơ sở trong schema `public`, rồi in tổng số dòng theo bảng từ cùng snapshot PostgreSQL. Dùng `--schema` nếu schema đích khác. Để xuất lại, chọn một thư mục đích mới.

Có thể dùng `--raw-root` để trỏ tới thư mục `data-<tên>` khác. Timestamp thiếu múi giờ được hiểu theo UTC+7, giống pipeline hiện tại. Với JSON thiếu ngày crawl, cột `crawl_timestamp` lấy thời điểm sửa file. Manifest lưu thời điểm này. Khi nhiều file có cùng khóa, pipeline ưu tiên file có timestamp crawl gốc, rồi đến timestamp mới hơn và số review nhiều hơn.

```sql
SELECT source_code, COUNT(*) AS reviews
FROM reviews
GROUP BY source_code
ORDER BY source_code;
```

