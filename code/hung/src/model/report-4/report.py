"""Write the audit tables and the reader-facing Markdown report."""

import csv
import math


LANGUAGE_NAMES = {"vi": "Tiếng Việt", "en": "Tiếng Anh", "ja": "Tiếng Nhật", "fr": "Tiếng Pháp"}


def write_csv(path, rows, fields=None):
    if fields is None:
        fields = list(rows[0]) if rows else []
    temporary = path.with_suffix(".tmp")
    with temporary.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def number(value, digits=3):
    return "—" if value is None or not math.isfinite(value) else f"{value:.{digits}g}"


def percent(value):
    return "—" if value is None else f"{100 * value:.1f}%"


def interval(row):
    if row["ci_low"] is None:
        return "—"
    return f'[{number(row["ci_low"])}; {number(row["ci_high"])}]'


def proposal(row):
    parts = []
    if row["logistic_rank"] is not None:
        parts.append(f'Logistic {row["logistic_weight"]:+.4g}')
    if row["bayes_rank"] is not None:
        parts.append(f'Bayes {row["bayes_score"]:+.4g}')
    return " / ".join(parts)


def write_report(path, audit, coverage, summary, results, metrics, metadata):
    lines = [
        "# Report 4 · Từ khóa đặc trưng theo ngôn ngữ và mức rating",
        "",
        f'Xác nhận **{sum(row["status"] == "Xác nhận" for row in results)}/{len(results)} cụm ứng viên** '
        f'trên {sum(row["test_rows"] for row in audit):,} review test. '
        f'Lưu **{len(metrics)} pipeline đã huấn luyện**.',
        "",
        "## 1. Dữ liệu và cách chia",
        "",
        f'- Snapshot {metadata["input_name"]}, gồm {metadata["input_rows"]:,} review. SHA-256 '
        f'{metadata["input_sha256"]}.',
        f'- Giữ {metadata["selected_rows"]:,} review mang nhãn vi, en, ja hoặc fr trước audit. '
        f'Ngoài phạm vi {metadata["input_rows"] - metadata["selected_rows"]:,} review.',
        f'- Manifest SHA-256 {metadata["manifest_sha256"]}. Seed {metadata["seed"]}. '
        'Các quán và nhóm review trùng đã phát hiện được giữ cùng tập. Chia xấp xỉ 80/20 theo quán. '
        'Kiểm tra trùng gần dùng review dài từ 120 ký tự, chung 48 ký tự ở đầu hoặc cuối và độ tương đồng từ 90%.',
        '- Dùng rating_level_5 và gộp các nền tảng trong từng ngôn ngữ. Các nhãn ngôn ngữ suy ra vẫn có thể sai. '
        'Tệp language_audit_sample.csv ghi mẫu phân tầng để đối chiếu. Giữ mã ngôn ngữ CSV, '
        'tách thân review Tripadvisor và loại các dòng có kết quả Lingua lệch rõ với nhãn CSV. '
        'Giữ dòng quá ngắn hoặc có kết quả chưa chắc chắn để hạn chế loại nhầm.',
        '- Điểm 0 được đối chiếu bằng ID review với trường rating trong JSON lưu cục bộ. '
        'Chỉ dùng dòng có số 0 ghi trực tiếp trong raw. Tệp rating_zero_audit.csv ghi nguồn truy vết. '
        'Trường raw ghi 0 xác nhận giá trị đã crawl. Ý nghĩa của 0 trên từng nền tảng cần đối chiếu riêng.',
        "",
        "| Ngôn ngữ | Trước audit | Train | Quán train | Test | Quán test | Rating 0 được giữ | Rating 0 bị loại | Lệch ngôn ngữ | Dòng khác bị loại |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in audit:
        lines.append(
            f'| {LANGUAGE_NAMES[row["language"]]} | {row["input_rows"]:,} | {row["train_rows"]:,} | '
            f'{row["train_shops"]:,} | {row["test_rows"]:,} | {row["test_shops"]:,} | '
            f'{row["zero_kept"]} | {row["zero_dropped"]} | {row["language_drops"]} | {row["other_drops"]} |'
        )
    lines += [
        "",
        "Độ phủ bên dưới dùng các review hợp lệ sau audit và ghi cả mức chưa có dữ liệu.",
        "",
        "| Ngôn ngữ | Mức | Review train | Quán train | Review test | Quán test |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in coverage:
        lines.append(f'| {row["language"]} | {row["rating"]} | {row["train_reviews"]} | {row["train_shops"]} | {row["test_reviews"]} | {row["test_shops"]} |')
    lines += [
        "",
        "## 2. Huấn luyện và chọn ứng viên",
        "",
        '- Chuẩn hóa văn bản, che URL, email, số điện thoại và cụm tiết lộ điểm. Sinh unigram, bigram và trigram trong từng câu. '
        'Tiếng Việt tách theo âm tiết, Anh và Pháp theo từ, Nhật dùng Janome.',
        '- Fit từ vựng và IDF trong từng lượt cross-validation theo quán. Chọn C của Logistic Regression và alpha '
        'của Complement Naive Bayes bằng Average Precision (AP) trên dự đoán ngoài fold. '
        'Chọn ngưỡng dự đoán theo F1 ngoài fold, rồi fit lại trên toàn train.',
        f'- Mỗi model chọn tối đa {metadata["top_n"]} cụm có điểm dương và đủ hỗ trợ. '
        'Dùng ngưỡng ban đầu 20 review lớp đích từ 5 quán trên train. '
        'Lấy hợp hai danh sách và kiểm định một lần cho mỗi ngôn ngữ, mức và cụm.',
        '- Logistic báo hệ số TF-IDF hướng về lớp đích. Bayes báo chênh lệch trọng số đóng góp vào điểm lớp đích và lớp còn lại.',
        '- Cặp file model đặt trực tiếp trong model/<ngôn ngữ>/rating-<mức>/. '
        'Cả hai pipeline được nạp lại trong tiến trình Python mới và so với dự đoán trước khi lưu.',
        "",
        "| Ngôn ngữ | Mức | Model | C / alpha | Ngưỡng | AP test | AP theo tỷ lệ lớp | AP theo độ dài | ΔAP so với độ dài | Precision | Recall | F1 |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in metrics:
        lines.append(
            f'| {row["language"]} | {row["rating"]} | {row["model"]} | {row["parameter"]} | '
            f'{number(row["threshold"])} | {number(row["ap"])} | {number(row["class_prior_ap"])} | '
            f'{number(row["length_baseline_ap"])} | {row["delta_ap_vs_length"]:+.3f} | '
            f'{number(row["precision"])} | {number(row["recall"])} | {number(row["f1"])} |'
        )
    lines += [
        "",
        f'Mức tăng AP từ +0.02 so với baseline độ dài xuất hiện ở '
        f'{sum(row["delta_ap_vs_length"] >= 0.02 for row in metrics)}/{len(metrics)} model trên test.',
        "",
        "## 3. Kiểm định trên các quán chưa thấy khi train",
        "",
        'Dùng sự xuất hiện của cụm và rating thật để lập bảng 2×2. So sánh tỷ lệ đạt mức đích giữa nhóm có và không có cụm. '
        'Dùng Wald z một phía trên log-OR với sai số chuẩn theo nhóm quán. '
        f'Hiệu chỉnh Holm một lần cho toàn bộ {len(results)} giả thuyết đã khóa trong lượt chạy. '
        'Dòng thiếu hỗ trợ vẫn được tính trong số giả thuyết với đầu vào Holm bằng 1.',
        "",
        'Điều kiện xác nhận gồm tỷ lệ đúng chiều, OR từ 1.5, cận dưới CI 95% của OR lớn hơn 1, '
        'p-value Holm dưới 0.05 và ít nhất 10 review lớp đích chứa cụm từ ít nhất 5 quán và 5 nhóm quán. '
        'Phép Wald cũng cần các ô đếm tổng khác 0 và sai số chuẩn hữu hạn dương.',
        "",
        '| Ngôn ngữ | Mức | Logistic đề xuất | Bayes đề xuất | Sau lấy hợp | Xác nhận | Trạng thái |',
        '|---|---:|---:|---:|---:|---:|---|',
    ]
    for row in summary:
        lines.append(
            f'| {row["language"]} | {row["rating"]} | {row["logistic_candidates"]} | {row["bayes_candidates"]} | '
            f'{row["candidates"]} | {row["confirmed"]} | {row["status"]} |'
        )
    report_rows = 0
    for item in summary:
        language, level = item["language"], item["rating"]
        subset = [row for row in results if (row["language"], row["rating"]) == (language, level)]
        if not subset:
            continue
        subset.sort(key=lambda row: row["holm_rank"])
        lines += [
            "", f'### {LANGUAGE_NAMES[language]} · rating {level}', "",
            f'Kiểm định {len(subset)} ứng viên. Xác nhận {item["confirmed"]} cụm.', "",
            '| Hạng Holm | Cụm ứng viên | Model và trọng số | P-value thô | P-value Holm | OR | CI 95% | Quyết định |',
            '|---:|---|---|---:|---:|---:|---|---|',
        ]
        for row in subset:
            decision = row["status"] + (f' · {row["reason"]}' if row["reason"] else "")
            lines.append(
                f'| {row["holm_rank"]} | {row["phrase"]} | {proposal(row)} | {number(row["p_raw"])} | '
                f'{number(row["p_holm"])} | {number(row["or"])} | {interval(row)} | {decision} |'
            )
            report_rows += 1
        for row in subset:
            if row["status"] != "Xác nhận":
                continue
            lines += [
                "",
                f'**{row["phrase"]}** · {proposal(row)}. Tỷ lệ mức {level} trên test là '
                f'{percent(row["p1"])} khi có cụm và {percent(row["p2"])} khi thiếu cụm '
                f'({row["delta_pp"]:+.1f} điểm phần trăm). '
                f'Có {row["target_reviews"]} review đúng mức chứa cụm từ {row["target_shops"]} quán. '
                f'TP/FP/FN/TN = {row["tp"]}/{row["fp"]}/{row["fn"]}/{row["tn"]}.',
            ]
            if row["context"]:
                lines.append(f'- Ngữ cảnh đã rút gọn: {row["context"]}.')
            if row["length_sensitivity"]:
                lines.append(f'- Chênh lệch theo nhóm độ dài: {row["length_sensitivity"]}.')
    assert report_rows == len(results) == sum(row["candidates"] for row in summary)
    lines += [
        "", "## 4. Kết luận", "",
        'Các kết luận dưới đây mô tả liên hệ quan sát giữa cụm từ và rating trong review của dự án. '
        'Cơ cấu nền tảng, độ dài review, thời gian và đặc điểm quán có thể ảnh hưởng đến liên hệ.',
        "",
        '| Ngôn ngữ | Mức | Cụm xác nhận / ứng viên | Từ khóa xác nhận hoặc lý do |',
        '|---|---:|---:|---|',
    ]
    for row in summary:
        lines.append(
            f'| {row["language"]} | {row["rating"]} | {row["confirmed"]}/{row["candidates"]} | '
            f'{row["confirmed_phrases"] or row["status"]} |'
        )
    lines += [
        "", "## 5. Tệp đối chiếu", "",
        '- rating_coverage.csv và split_manifest.csv lưu độ phủ và cách chia.',
        '- locked_candidates.csv lưu ứng viên và trọng số trước kiểm định.',
        '- keyword_results.csv lưu đủ bảng 2×2, các metric của quy tắc dùng một cụm, hai tỷ lệ, '
        'Wald z, p-value, OR, CI và lý do quyết định.',
        '- test_metrics.csv lưu hiệu năng hai model. keywords_by_language_rating.csv lưu tóm tắt đủ 24 tổ hợp.',
        "",
    ]
    temporary = path.with_suffix(".tmp")
    temporary.write_text("\n".join(lines), encoding="utf-8")
    temporary.replace(path)
