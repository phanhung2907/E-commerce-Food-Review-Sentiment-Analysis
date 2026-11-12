# Pipeline Foody — cleaning, snapshot và EDA export

Chạy từ thư mục gốc `E:\Real-estate-tourism\hung`. Dependency dùng `pyproject.toml`/`uv.lock` hiện có; không thêm package Python mới.

## Luồng dữ liệu

```text
Foody → crawler/merge → local raw_versions + raw hiện hành
    → MinIO raw_versions → raw alias + upload manifest
    → ETL đúng snapshot/hash → PostgreSQL current + data_ingestion_versions
    → export CSV có dataset_id/hash → RStudio EDA
```

Raw snapshot là toàn bộ `restaurant.json` sau đóng gói/merge, chưa phải HTTP response nguyên bản. Alias hiện hành phục vụ crawler cũ; snapshot và manifest dùng để tái lập.

## Setup và kiểm tra

Sau khi hạ tầng Docker của nhóm hoạt động:

```powershell
uv run python code/hung/src/storage/setup_minio.py
uv run python code/hung/src/storage/init_postgres.py
uv run python code/hung/src/storage/check_infrastructure.py
uv run python -B -m unittest discover -s code/hung/src/tests -v
```

`init_postgres.py` áp schema và migration bổ sung `reviews.observed_at`, `reviews.raw_object_key`, bảng `data_ingestion_versions`. Không xóa dữ liệu cũ. Runtime không tự tạo bucket/schema. Test dùng file tạm và client giả lập, không ghi vào dịch vụ thật.

## Đồng bộ raw đã có, không crawl lại

Thử một quán trước; đổi run ID cho mỗi lần upload:

```powershell
uv run python code/hung/src/storage/minio_uploader.py --source foody --city dien-bien --limit 1 --workers 1 --overwrite --run-id bootstrap-one
uv run python code/hung/src/processing/minio_to_postgres.py --source foody --manifest code/hung/data/foody_shoppefood/manifests/bootstrap-one.json --dry-run --workers 1
uv run python code/hung/src/processing/minio_to_postgres.py --source foody --manifest code/hung/data/foody_shoppefood/manifests/bootstrap-one.json --workers 1
```

Sau khi đối soát đạt, đồng bộ toàn bộ local:

```powershell
uv run python code/hung/src/storage/minio_uploader.py --source foody --workers 8 --overwrite --run-id bootstrap-local-v1
uv run python code/hung/src/processing/minio_to_postgres.py --source foody --manifest code/hung/data/foody_shoppefood/manifests/bootstrap-local-v1.json --workers 4
```

Uploader archive lịch sử trước khi cập nhật alias. Không có `--overwrite` thì giữ alias remote và manifest chọn đúng remote đó; local mới vẫn được archive. Có file lỗi sẽ tạo manifest `failed`, thoát mã 1; ETL chỉ nhận manifest `complete`. Manifest đã có không được thay thế.

## Crawl những lần sau và resume

```powershell
uv run python code/hung/src/run_pipeline.py --workers 8 --db-workers 4 --page-delay 2
```

Ghi lại crawl run ID được in ra. Resume chỉ dùng đúng lần bị gián đoạn:

```powershell
uv run python code/hung/src/run_pipeline.py --resume --run-id <crawl_run_id> --workers 8 --db-workers 4
```

File local có run ID khác không bị resume-skip. Mỗi lần upload trong pipeline có upload ID mới, kể cả retry cùng crawl. `--full-refresh` vẫn là vét lại dữ liệu nguồn, không phải lệnh xóa review cũ khỏi DB.

Các option hiện có (`--mode limit`, city, worker riêng, skip, db-dry-run) được giữ. Khi skip upload mà vẫn load, phải chỉ manifest:

```powershell
uv run python code/hung/src/run_pipeline.py --skip-restaurant-crawl --skip-review-crawl --skip-minio-upload --input-manifest code/hung/data/foody_shoppefood/manifests/bootstrap-local-v1.json
```

`--db-dry-run` của pipeline chỉ dừng ghi PostgreSQL; các bước crawl/upload vẫn chạy nếu không skip. `--dry-run` của ETL riêng chỉ đọc/transform, không ghi MinIO hoặc DB và chưa kiểm tra SQL constraint.

## Đường dẫn lưu trữ

```text
Local:
code/hung/data/foody_shoppefood/raw/<city>/<id>/restaurant.json
code/hung/data/foody_shoppefood/raw_versions/<city>/<id>/<sha256>/restaurant.json
code/hung/data/foody_shoppefood/manifests/<upload_run_id>.json

MinIO:
foody/raw/<city>/<id>/restaurant.json
foody/raw_versions/<city>/<id>/<sha256>/restaurant.json
foody/manifests/<upload_run_id>.json
```

SHA là hash bytes file; timestamp/format đổi cũng tạo hash khác. Cơ chế không cần native bucket versioning; chưa cấu hình Object Lock. Tránh nhiều pipeline đồng thời cập nhật alias cùng quán. Không xóa snapshot được manifest/report/model tham chiếu.

## Chính sách PostgreSQL

- Một transaction/snapshot quán, có khóa theo source + restaurant ID, ghi current và ledger cùng commit.
- Cùng raw hash + transform version đã nạp sẽ bỏ qua; code hash mâu thuẫn với bản đó báo lỗi. Thay logic phải tăng `TRANSFORM_VERSION` trong `storage/data_versioning.py` và lưu code/lockfile.
- Snapshot cũ hơn current chỉ ghi ledger, không làm lùi current. Khác snapshot nhưng cùng timestamp sẽ báo lỗi để đối soát.
- Review cùng ID refresh theo thời điểm quan sát; tags của review refresh được thay. Không tự xóa review không thấy ở lần sau.
- Quán/reviewer vẫn có COALESCE và các bảng con khác giữ chính sách cũ; DB current có thể chứa giá trị biết được từ nhiều lần crawl.

**Chuyển tiếp legacy:** timestamp crawler cũ không offset được hiểu theo giả định +07:00 rồi chuyển UTC. Xác nhận giả định này nếu từng crawl ở máy múi giờ khác. Lần nạp có version đầu tiên cho quán có legacy raw key `/raw/` dùng raw hiện hành đã đối soát để bootstrap; không nạp snapshot lịch sử ngẫu nhiên trước. Không tự sửa timestamp DB cũ bằng migration.

## Audit và xuất dataset EDA

```powershell
uv run python code/hung/src/processing/audit_local_data.py --output code/hung/reports/cleaning_local_audit.json
uv run python code/hung/src/processing/export_analysis_snapshot.py --dataset-id eda-v1-20261019
```

Audit chỉ đọc raw local, xuất số liệu tổng hợp, không xuất text/người viết. Export đọc DB trong một transaction nhất quán và tạo `data/processed/<dataset_id>/reviews.csv`, `restaurants.csv`, `raw_lineage.csv`, `manifest.json`. Dataset ID cũ không bị ghi đè; còn review thiếu lineage thì export báo lỗi. File CSV giữ dữ liệu trước lọc eligibility, chưa tạo nhãn hoặc split.

Trong bảng quán, metadata platform và thống kê mẫu crawl có tên riêng. Không coi `mean_rating_crawled` là rating platform hoặc là điểm đã được kiểm tra miền hợp lệ. Đọc ID dưới dạng chuỗi và CSV UTF-8 trong RStudio.

## Xem lại lịch sử

Chọn `object_name`/SHA trong manifest, chạy ETL `--object-key <immutable_key> --dry-run` để kiểm tra. Muốn replay lịch sử, dùng DB riêng đã setup và code/lockfile đúng phiên bản; không ép snapshot cũ ghi đè DB chính. Snapshot đã bị ghi đè trước khi có versioning chỉ có thể khôi phục nếu còn backup hoặc native object version.

Báo cáo chi tiết và kế hoạch: `code/hung/reports/BAO_CAO_CLEANING_VA_DATA_VERSIONING.md`, `plans/PLAN_EDA_CHI_TIET_TUAN_5_6.md`. Chưa chạy end-to-end với dịch vụ thật ở thời điểm bàn giao; thực hiện checklist tích hợp trong báo cáo sau khi MinIO/PostgreSQL hoạt động.
