# Report 4 · Từ khóa đặc trưng theo ngôn ngữ và mức rating

Xác nhận **86/264 cụm ứng viên** trên 67,798 review test. Lưu **34 pipeline đã huấn luyện**.

## 1. Dữ liệu và cách chia

- Snapshot reviews_preprocessed.csv, gồm 384,059 review. SHA-256 e9509d8dee403157d376b667a42e8ac1ef4e42d5df850efcc3b25e205591a718.
- Giữ 347,271 review mang nhãn vi, en, ja hoặc fr trước audit. Ngoài phạm vi 36,788 review.
- Manifest SHA-256 31ff6a046f4b66693a7d2b1d7dc51f6ace2f9564f1b9801789dd208bce2c0656. Seed 20261114. Các quán và nhóm review trùng đã phát hiện được giữ cùng tập. Chia xấp xỉ 80/20 theo quán. Kiểm tra trùng gần dùng review dài từ 120 ký tự, chung 48 ký tự ở đầu hoặc cuối và độ tương đồng từ 90%.
- Dùng rating_level_5 và gộp các nền tảng trong từng ngôn ngữ. Các nhãn ngôn ngữ suy ra vẫn có thể sai. Tệp language_audit_sample.csv ghi mẫu phân tầng để đối chiếu. Giữ mã ngôn ngữ CSV, tách thân review Tripadvisor và loại các dòng có kết quả Lingua lệch rõ với nhãn CSV. Giữ dòng quá ngắn hoặc có kết quả chưa chắc chắn để hạn chế loại nhầm.
- Điểm 0 được đối chiếu bằng ID review với trường rating trong JSON lưu cục bộ. Chỉ dùng dòng có số 0 ghi trực tiếp trong raw. Tệp rating_zero_audit.csv ghi nguồn truy vết. Trường raw ghi 0 xác nhận giá trị đã crawl. Ý nghĩa của 0 trên từng nền tảng cần đối chiếu riêng.

| Ngôn ngữ | Trước audit | Train | Quán train | Test | Quán test | Rating 0 được giữ | Rating 0 bị loại | Lệch ngôn ngữ | Dòng khác bị loại |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Tiếng Việt | 278,247 | 220,810 | 28,666 | 55,090 | 7,144 | 90 | 0 | 2310 | 37 |
| Tiếng Anh | 34,267 | 26,823 | 1,232 | 6,498 | 308 | 12 | 0 | 946 | 0 |
| Tiếng Nhật | 30,569 | 24,338 | 596 | 6,187 | 149 | 0 | 0 | 42 | 2 |
| Tiếng Pháp | 4,188 | 84 | 61 | 23 | 16 | 0 | 0 | 4081 | 0 |

Độ phủ bên dưới dùng các review hợp lệ sau audit và ghi cả mức chưa có dữ liệu.

| Ngôn ngữ | Mức | Review train | Quán train | Review test | Quán test |
|---|---:|---:|---:|---:|---:|
| vi | 0 | 72 | 69 | 18 | 17 |
| vi | 1 | 13477 | 4906 | 3361 | 1207 |
| vi | 2 | 11646 | 5357 | 2898 | 1354 |
| vi | 3 | 43588 | 11422 | 10750 | 2878 |
| vi | 4 | 103344 | 21404 | 26520 | 5297 |
| vi | 5 | 48683 | 11561 | 11543 | 2864 |
| en | 0 | 10 | 6 | 2 | 2 |
| en | 1 | 2618 | 253 | 576 | 55 |
| en | 2 | 1378 | 214 | 346 | 51 |
| en | 3 | 1457 | 261 | 410 | 64 |
| en | 4 | 2140 | 456 | 587 | 111 |
| en | 5 | 19220 | 786 | 4577 | 180 |
| ja | 0 | 0 | 0 | 0 | 0 |
| ja | 1 | 608 | 236 | 151 | 59 |
| ja | 2 | 577 | 223 | 148 | 55 |
| ja | 3 | 1343 | 298 | 333 | 75 |
| ja | 4 | 2117 | 337 | 510 | 91 |
| ja | 5 | 19693 | 528 | 5045 | 137 |
| fr | 0 | 0 | 0 | 0 | 0 |
| fr | 1 | 11 | 9 | 4 | 4 |
| fr | 2 | 7 | 6 | 1 | 1 |
| fr | 3 | 2 | 2 | 1 | 1 |
| fr | 4 | 7 | 7 | 2 | 2 |
| fr | 5 | 57 | 42 | 15 | 10 |

## 2. Huấn luyện và chọn ứng viên

- Chuẩn hóa văn bản, che URL, email, số điện thoại và cụm tiết lộ điểm. Sinh unigram, bigram và trigram trong từng câu. Tiếng Việt tách theo âm tiết, Anh và Pháp theo từ, Nhật dùng Janome.
- Fit từ vựng và IDF trong từng lượt cross-validation theo quán. Chọn C của Logistic Regression và alpha của Complement Naive Bayes bằng Average Precision (AP) trên dự đoán ngoài fold. Chọn ngưỡng dự đoán theo F1 ngoài fold, rồi fit lại trên toàn train.
- Mỗi model chọn tối đa 10 cụm có điểm dương và đủ hỗ trợ. Dùng ngưỡng ban đầu 20 review lớp đích từ 5 quán trên train. Lấy hợp hai danh sách và kiểm định một lần cho mỗi ngôn ngữ, mức và cụm.
- Logistic báo hệ số TF-IDF hướng về lớp đích. Bayes báo chênh lệch trọng số đóng góp vào điểm lớp đích và lớp còn lại.
- Cặp file model đặt trực tiếp trong model/<ngôn ngữ>/rating-<mức>/. Cả hai pipeline được nạp lại trong tiến trình Python mới và so với dự đoán trước khi lưu.

| Ngôn ngữ | Mức | Model | C / alpha | Ngưỡng | AP test | AP theo tỷ lệ lớp | AP theo độ dài | ΔAP so với độ dài | Precision | Recall | F1 |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| vi | 0 | logistic | 2.0 | 0.00342 | 0.0069 | 0.000327 | 0.0013 | +0.006 | 0 | 0 | 0 |
| vi | 0 | bayes | 0.25 | 0.211 | 0.00137 | 0.000327 | 0.0013 | +0.000 | 0 | 0 | 0 |
| vi | 1 | logistic | 2.0 | 0.25 | 0.663 | 0.061 | 0.0799 | +0.584 | 0.557 | 0.744 | 0.637 |
| vi | 1 | bayes | 0.25 | 0.881 | 0.592 | 0.061 | 0.0799 | +0.512 | 0.489 | 0.805 | 0.609 |
| vi | 2 | logistic | 2.0 | 0.121 | 0.305 | 0.0526 | 0.0515 | +0.253 | 0.286 | 0.698 | 0.406 |
| vi | 2 | bayes | 0.25 | 0.741 | 0.288 | 0.0526 | 0.0515 | +0.237 | 0.284 | 0.73 | 0.409 |
| vi | 3 | logistic | 0.5 | 0.207 | 0.444 | 0.195 | 0.299 | +0.145 | 0.374 | 0.651 | 0.475 |
| vi | 3 | bayes | 0.25 | 0.42 | 0.424 | 0.195 | 0.299 | +0.124 | 0.34 | 0.677 | 0.452 |
| vi | 4 | logistic | 0.5 | 0.379 | 0.795 | 0.481 | 0.625 | +0.170 | 0.689 | 0.872 | 0.77 |
| vi | 4 | bayes | 0.25 | 0.467 | 0.781 | 0.481 | 0.625 | +0.157 | 0.673 | 0.853 | 0.753 |
| vi | 5 | logistic | 2.0 | 0.258 | 0.602 | 0.21 | 0.322 | +0.279 | 0.483 | 0.72 | 0.578 |
| vi | 5 | bayes | 0.25 | 0.424 | 0.568 | 0.21 | 0.322 | +0.246 | 0.459 | 0.76 | 0.572 |
| en | 1 | logistic | 2.0 | 0.121 | 0.216 | 0.0886 | 0.0987 | +0.117 | 0.202 | 0.495 | 0.287 |
| en | 1 | bayes | 0.25 | 0.0805 | 0.177 | 0.0886 | 0.0987 | +0.078 | 0.148 | 0.549 | 0.233 |
| en | 2 | logistic | 2.0 | 0.0763 | 0.151 | 0.0532 | 0.0596 | +0.091 | 0.151 | 0.419 | 0.222 |
| en | 2 | bayes | 0.25 | 0.0121 | 0.0925 | 0.0532 | 0.0596 | +0.033 | 0.0807 | 0.714 | 0.145 |
| en | 3 | logistic | 2.0 | 0.122 | 0.303 | 0.0631 | 0.0734 | +0.229 | 0.296 | 0.517 | 0.376 |
| en | 3 | bayes | 0.25 | 0.111 | 0.256 | 0.0631 | 0.0734 | +0.182 | 0.244 | 0.5 | 0.328 |
| en | 4 | logistic | 2.0 | 0.124 | 0.307 | 0.0903 | 0.131 | +0.175 | 0.272 | 0.635 | 0.381 |
| en | 4 | bayes | 0.25 | 0.134 | 0.277 | 0.0903 | 0.131 | +0.146 | 0.245 | 0.579 | 0.345 |
| en | 5 | logistic | 2.0 | 0.454 | 0.89 | 0.704 | 0.81 | +0.079 | 0.78 | 0.953 | 0.858 |
| en | 5 | bayes | 0.25 | 0.307 | 0.888 | 0.704 | 0.81 | +0.078 | 0.781 | 0.951 | 0.858 |
| ja | 1 | logistic | 2.0 | 0.142 | 0.437 | 0.0244 | 0.0687 | +0.368 | 0.396 | 0.57 | 0.467 |
| ja | 1 | bayes | 0.25 | 0.613 | 0.315 | 0.0244 | 0.0687 | +0.247 | 0.274 | 0.53 | 0.361 |
| ja | 2 | logistic | 2.0 | 0.0768 | 0.172 | 0.0239 | 0.0629 | +0.109 | 0.179 | 0.568 | 0.273 |
| ja | 2 | bayes | 0.25 | 0.51 | 0.135 | 0.0239 | 0.0629 | +0.072 | 0.154 | 0.372 | 0.218 |
| ja | 3 | logistic | 2.0 | 0.136 | 0.234 | 0.0538 | 0.0902 | +0.144 | 0.258 | 0.532 | 0.347 |
| ja | 3 | bayes | 0.25 | 0.513 | 0.212 | 0.0538 | 0.0902 | +0.121 | 0.217 | 0.613 | 0.32 |
| ja | 4 | logistic | 2.0 | 0.148 | 0.233 | 0.0824 | 0.128 | +0.104 | 0.224 | 0.478 | 0.306 |
| ja | 4 | bayes | 0.25 | 0.505 | 0.205 | 0.0824 | 0.128 | +0.077 | 0.214 | 0.512 | 0.302 |
| ja | 5 | logistic | 2.0 | 0.498 | 0.964 | 0.815 | 0.884 | +0.080 | 0.905 | 0.954 | 0.929 |
| ja | 5 | bayes | 0.25 | 0.094 | 0.959 | 0.815 | 0.884 | +0.075 | 0.908 | 0.944 | 0.925 |
| fr | 5 | logistic | 2.0 | 0.548 | 0.778 | 0.652 | 0.749 | +0.029 | 0.688 | 0.733 | 0.71 |
| fr | 5 | bayes | 1.0 | 0.387 | 0.778 | 0.652 | 0.749 | +0.029 | 0.688 | 0.733 | 0.71 |

Mức tăng AP từ +0.02 so với baseline độ dài xuất hiện ở 32/34 model trên test.

## 3. Kiểm định trên các quán chưa thấy khi train

Dùng sự xuất hiện của cụm và rating thật để lập bảng 2×2. So sánh tỷ lệ đạt mức đích giữa nhóm có và không có cụm. Dùng Wald z một phía trên log-OR với sai số chuẩn theo nhóm quán. Hiệu chỉnh Holm một lần cho toàn bộ 264 giả thuyết đã khóa trong lượt chạy. Dòng thiếu hỗ trợ vẫn được tính trong số giả thuyết với đầu vào Holm bằng 1.

Điều kiện xác nhận gồm tỷ lệ đúng chiều, OR từ 1.5, cận dưới CI 95% của OR lớn hơn 1, p-value Holm dưới 0.05 và ít nhất 10 review lớp đích chứa cụm từ ít nhất 5 quán và 5 nhóm quán. Phép Wald cũng cần các ô đếm tổng khác 0 và sai số chuẩn hữu hạn dương.

| Ngôn ngữ | Mức | Logistic đề xuất | Bayes đề xuất | Sau lấy hợp | Xác nhận | Trạng thái |
|---|---:|---:|---:|---:|---:|---|
| vi | 0 | 2 | 0 | 2 | 0 | Chưa có cụm được xác nhận |
| vi | 1 | 10 | 10 | 20 | 12 | Có cụm xác nhận |
| vi | 2 | 10 | 10 | 20 | 7 | Có cụm xác nhận |
| vi | 3 | 10 | 10 | 20 | 13 | Có cụm xác nhận |
| vi | 4 | 10 | 10 | 20 | 10 | Có cụm xác nhận |
| vi | 5 | 10 | 10 | 20 | 6 | Có cụm xác nhận |
| en | 0 | 0 | 0 | 0 | 0 | Thiếu review hoặc quán lớp đích trên train |
| en | 1 | 10 | 10 | 15 | 0 | Chưa có cụm được xác nhận |
| en | 2 | 10 | 5 | 11 | 1 | Có cụm xác nhận |
| en | 3 | 10 | 10 | 15 | 1 | Có cụm xác nhận |
| en | 4 | 10 | 10 | 17 | 1 | Có cụm xác nhận |
| en | 5 | 10 | 10 | 19 | 4 | Có cụm xác nhận |
| ja | 0 | 0 | 0 | 0 | 0 | Thiếu review hoặc quán lớp đích trên train |
| ja | 1 | 10 | 10 | 18 | 9 | Có cụm xác nhận |
| ja | 2 | 10 | 10 | 14 | 6 | Có cụm xác nhận |
| ja | 3 | 10 | 10 | 17 | 7 | Có cụm xác nhận |
| ja | 4 | 10 | 10 | 16 | 7 | Có cụm xác nhận |
| ja | 5 | 10 | 10 | 19 | 2 | Có cụm xác nhận |
| fr | 0 | 0 | 0 | 0 | 0 | Thiếu review hoặc quán lớp đích trên train |
| fr | 1 | 0 | 0 | 0 | 0 | Thiếu review hoặc quán lớp đích trên train |
| fr | 2 | 0 | 0 | 0 | 0 | Thiếu review hoặc quán lớp đích trên train |
| fr | 3 | 0 | 0 | 0 | 0 | Thiếu review hoặc quán lớp đích trên train |
| fr | 4 | 0 | 0 | 0 | 0 | Thiếu review hoặc quán lớp đích trên train |
| fr | 5 | 1 | 1 | 1 | 0 | Chưa có cụm được xác nhận |

### Tiếng Việt · rating 0

Kiểm định 2 ứng viên. Xác nhận 0 cụm.

| Hạng Holm | Cụm ứng viên | Model và trọng số | P-value thô | P-value Holm | OR | CI 95% | Quyết định |
|---:|---|---|---:|---:|---:|---|---|
| 224 | cũng | Logistic +0.2205 | — | — | 0.269 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 225 | ăn | Logistic +1.436 | — | — | 0.399 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |

### Tiếng Việt · rating 1

Kiểm định 20 ứng viên. Xác nhận 12 cụm.

| Hạng Holm | Cụm ứng viên | Model và trọng số | P-value thô | P-value Holm | OR | CI 95% | Quyết định |
|---:|---|---|---:|---:|---:|---|---|
| 1 | tệ | Logistic +5.932 | 0 | 0 | 13.2 | [11.6; 14.9] | Xác nhận |
| 7 | làm ăn | Logistic +4.953 | 2.8e-131 | 7.21e-129 | 15.9 | [12.7; 19.9] | Xác nhận |
| 8 | dở | Logistic +4.633 | 1.67e-127 | 4.29e-125 | 7.56 | [6.41; 8.92] | Xác nhận |
| 15 | lừa | Logistic +4.922 | 2.11e-52 | 5.28e-50 | 22.4 | [15; 33.5] | Xác nhận |
| 16 | chửi | Logistic +4.579 | 2.5e-45 | 6.22e-43 | 13.6 | [9.46; 19.6] | Xác nhận |
| 17 | ko | Logistic +4.343 | 5.22e-40 | 1.29e-37 | 1.98 | [1.79; 2.19] | Xác nhận |
| 19 | kém | Logistic +4.28 | 1.33e-37 | 3.26e-35 | 3.67 | [3.01; 4.49] | Xác nhận |
| 20 | lừa đảo | Bayes +4.052 | 2.35e-29 | 5.75e-27 | 58.5 | [28.7; 119] | Xác nhận |
| 24 | chém | Logistic +4.865 | 7.7e-24 | 1.86e-21 | 5.94 | [4.19; 8.43] | Xác nhận |
| 38 | hôi | Logistic +3.993 | 2.37e-13 | 5.37e-11 | 2.82 | [2.13; 3.73] | Xác nhận |
| 50 | thất đức | Bayes +4.167 | 3.95e-11 | 8.5e-09 | 147 | [32.7; 662] | Xác nhận |
| 55 | tẩy chay | Bayes +4.529 | 1.52e-10 | 3.2e-08 | 96.9 | [23.3; 402] | Xác nhận |
| 120 | bán | Logistic +3.988 | 0.171 | 1 | 1.08 | [0.926; 1.25] | Không đạt · OR < 1.5; CI chứa 1 hoặc thấp hơn; p Holm ≥ 0.05 |
| 226 | chú không đảm | Bayes +4.703 | — | — | — | — | Chưa đủ bằng chứng · Ô đếm bằng 0 |
| 227 | làm ăn thất | Bayes +4.49 | — | — | — | — | Chưa đủ bằng chứng · Ô đếm bằng 0 |
| 228 | lừa đảo khách | Bayes +4.787 | — | — | 15.4 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 229 | món không đảm | Bayes +4.851 | — | — | — | — | Chưa đủ bằng chứng · Ô đếm bằng 0 |
| 230 | này ra nhé | Bayes +4.233 | — | — | — | — | Chưa đủ bằng chứng · Ô đếm bằng 0 |
| 231 | tiệm sớm | Bayes +4.03 | — | — | 46.2 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 232 | ăn thất đức | Bayes +4.585 | — | — | — | — | Chưa đủ bằng chứng · Ô đếm bằng 0 |

**tệ** · Logistic +5.932. Tỷ lệ mức 1 trên test là 41.5% khi có cụm và 5.1% khi thiếu cụm (+36.4 điểm phần trăm). Có 619 review đúng mức chứa cụm từ 371 quán. TP/FP/FN/TN = 619/873/2742/50856.
- Ngữ cảnh đã rút gọn: tệ / ăn cơm không quá tệ với một phần cơm.
- Chênh lệch theo nhóm độ dài: nhóm 1: +53.3 đpt (17991 review, 257 có cụm); nhóm 2: +40.3 đpt (18365 review, 564 có cụm); nhóm 3: +28.2 đpt (18734 review, 671 có cụm).

**làm ăn** · Logistic +4.953. Tỷ lệ mức 1 trên test là 49.6% khi có cụm và 5.8% khi thiếu cụm (+43.8 điểm phần trăm). Có 175 review đúng mức chứa cụm từ 141 quán. TP/FP/FN/TN = 175/178/3186/51551.
- Ngữ cảnh đã rút gọn: shop làm ăn không đọc à / bye cái quán này làm ăn tệ quá bỏ hết.
- Chênh lệch theo nhóm độ dài: nhóm 1: +58.9 đpt (17991 review, 58 có cụm); nhóm 2: +50.7 đpt (18365 review, 140 có cụm); nhóm 3: +33.4 đpt (18734 review, 155 có cụm).

**dở** · Logistic +4.633. Tỷ lệ mức 1 trên test là 31.2% khi có cụm và 5.6% khi thiếu cụm (+25.5 điểm phần trăm). Có 305 review đúng mức chứa cụm từ 212 quán. TP/FP/FN/TN = 305/674/3056/51055.
- Ngữ cảnh đã rút gọn: hết vảy chứ ăn dở ẹc mà còn giao / dở không hợp khẩu vị.
- Chênh lệch theo nhóm độ dài: nhóm 1: +45.2 đpt (17991 review, 195 có cụm); nhóm 2: +30.3 đpt (18365 review, 351 có cụm); nhóm 3: +14.0 đpt (18734 review, 433 có cụm).

**lừa** · Logistic +4.922. Tỷ lệ mức 1 trên test là 58.7% khi có cụm và 6.0% khi thiếu cụm (+52.7 điểm phần trăm). Có 88 review đúng mức chứa cụm từ 67 quán. TP/FP/FN/TN = 88/62/3273/51667.
- Ngữ cảnh đã rút gọn: hết khoai hay gì lừa dối vừa thôi sai / lừa dối.
- Chênh lệch theo nhóm độ dài: nhóm 1: +70.7 đpt (17991 review, 24 có cụm); nhóm 2: +47.1 đpt (18365 review, 47 có cụm); nhóm 3: +52.3 đpt (18734 review, 79 có cụm).

**chửi** · Logistic +4.579. Tỷ lệ mức 1 trên test là 46.5% khi có cụm và 6.0% khi thiếu cụm (+40.5 điểm phần trăm). Có 60 review đúng mức chứa cụm từ 49 quán. TP/FP/FN/TN = 60/69/3301/51660.
- Ngữ cảnh đã rút gọn: ko đặt ko nhận chửi khách ko ra gì / hộp cơm ra muốn chửi thề luôn.
- Chênh lệch theo nhóm độ dài: nhóm 1: +68.4 đpt (17991 review, 13 có cụm); nhóm 2: +51.8 đpt (18365 review, 38 có cụm); nhóm 3: +32.4 đpt (18734 review, 78 có cụm).

**ko** · Logistic +4.343. Tỷ lệ mức 1 trên test là 10.2% khi có cụm và 5.4% khi thiếu cụm (+4.8 điểm phần trăm). Có 796 review đúng mức chứa cụm từ 488 quán. TP/FP/FN/TN = 796/7015/2565/44714.
- Ngữ cảnh đã rút gọn: món ăn ko đáng so với giá / phẩm quá ít và ko ngon so sánh cùng.
- Chênh lệch theo nhóm độ dài: nhóm 1: +11.4 đpt (17991 review, 1058 có cụm); nhóm 2: +6.1 đpt (18365 review, 3108 có cụm); nhóm 3: +3.8 đpt (18734 review, 3645 có cụm).

**kém** · Logistic +4.28. Tỷ lệ mức 1 trên test là 18.7% khi có cụm và 5.9% khi thiếu cụm (+12.8 điểm phần trăm). Có 155 review đúng mức chứa cụm từ 133 quán. TP/FP/FN/TN = 155/672/3206/51057.
- Ngữ cảnh đã rút gọn: sushi kém chất lượng / chi nhánh khác thì kém xa không hợp khẩu.
- Chênh lệch theo nhóm độ dài: nhóm 1: +33.0 đpt (17991 review, 104 có cụm); nhóm 2: +17.5 đpt (18365 review, 260 có cụm); nhóm 3: +7.5 đpt (18734 review, 463 có cụm).

**lừa đảo** · Bayes +4.052. Tỷ lệ mức 1 trên test là 78.9% khi có cụm và 6.0% khi thiếu cụm (+72.9 điểm phần trăm). Có 45 review đúng mức chứa cụm từ 36 quán. TP/FP/FN/TN = 45/12/3316/51717.
- Ngữ cảnh đã rút gọn: lừa đảo đóng gói chưa tốt / lừa đảo sai thiếu món.
- Chênh lệch theo nhóm độ dài: nhóm 1: +85.2 đpt (17991 review, 16 có cụm); nhóm 2: +63.1 đpt (18365 review, 13 có cụm); nhóm 3: +71.4 đpt (18734 review, 28 có cụm).

**chém** · Logistic +4.865. Tỷ lệ mức 1 trên test là 27.5% khi có cụm và 6.0% khi thiếu cụm (+21.5 điểm phần trăm). Có 81 review đúng mức chứa cụm từ 49 quán. TP/FP/FN/TN = 81/214/3280/51515.
- Ngữ cảnh đã rút gọn: người và giá tiền chém rất ngọt ngào thì / ăn xong thì chặt chém 45k.
- Chênh lệch theo nhóm độ dài: nhóm 1: +50.6 đpt (17991 review, 22 có cụm); nhóm 2: +32.8 đpt (18365 review, 111 có cụm); nhóm 3: +11.9 đpt (18734 review, 162 có cụm).

**hôi** · Logistic +3.993. Tỷ lệ mức 1 trên test là 15.3% khi có cụm và 6.0% khi thiếu cụm (+9.3 điểm phần trăm). Có 75 review đúng mức chứa cụm từ 70 quán. TP/FP/FN/TN = 75/416/3286/51313.
- Ngữ cảnh đã rút gọn: cũ và có mùi hôi mình đã bỏ gà / thịt rim quá hôi.
- Chênh lệch theo nhóm độ dài: nhóm 1: +31.8 đpt (17991 review, 67 có cụm); nhóm 2: +16.7 đpt (18365 review, 141 có cụm); nhóm 3: +2.0 đpt (18734 review, 283 có cụm).

**thất đức** · Bayes +4.167. Tỷ lệ mức 1 trên test là 90.5% khi có cụm và 6.1% khi thiếu cụm (+84.4 điểm phần trăm). Có 19 review đúng mức chứa cụm từ 16 quán. TP/FP/FN/TN = 19/2/3342/51727.
- Ngữ cảnh đã rút gọn: chó con mẹ mày thất đức / buôn kiểu vầy vừa thất đức vừa tạo nghiệp.
- Chênh lệch theo nhóm độ dài: nhóm 1: +91.5 đpt (17991 review, 6 có cụm); nhóm 2: +82.8 đpt (18365 review, 9 có cụm); nhóm 3: +79.7 đpt (18734 review, 6 có cụm).

**tẩy chay** · Bayes +4.529. Tỷ lệ mức 1 trên test là 86.2% khi có cụm và 6.1% khi thiếu cụm (+80.1 điểm phần trăm). Có 25 review đúng mức chứa cụm từ 19 quán. TP/FP/FN/TN = 25/4/3336/51725.
- Ngữ cảnh đã rút gọn: tẩy chay là vừa / chứ mình là tẩy chay luôn.
- Chênh lệch theo nhóm độ dài: nhóm 1: +91.4 đpt (17991 review, 2 có cụm); nhóm 2: +77.2 đpt (18365 review, 6 có cụm); nhóm 3: +82.1 đpt (18734 review, 21 có cụm).

### Tiếng Việt · rating 2

Kiểm định 20 ứng viên. Xác nhận 7 cụm.

| Hạng Holm | Cụm ứng viên | Model và trọng số | P-value thô | P-value Holm | OR | CI 95% | Quyết định |
|---:|---|---|---:|---:|---:|---|---|
| 13 | ko | Logistic +3.72 | 3.54e-63 | 8.91e-61 | 2.27 | [2.06; 2.5] | Xác nhận |
| 18 | chán | Logistic +2.843 | 2.24e-39 | 5.53e-37 | 3.43 | [2.85; 4.12] | Xác nhận |
| 27 | nhạt | Logistic +2.867 | 5.23e-18 | 1.24e-15 | 2.08 | [1.76; 2.46] | Xác nhận |
| 32 | mong | Logistic +2.524 | 2.77e-16 | 6.46e-14 | 2.4 | [1.94; 2.97] | Xác nhận |
| 35 | không ngon | Logistic +5.21 | 1.05e-14 | 2.41e-12 | 2.04 | [1.7; 2.44] | Xác nhận |
| 46 | ko ngon | Logistic +2.96 | 8.32e-12 | 1.82e-09 | 2.47 | [1.9; 3.21] | Xác nhận |
| 53 | cộc lốc | Bayes +2.378 | 1.09e-10 | 2.3e-08 | 9.04 | [4.58; 17.8] | Xác nhận |
| 92 | ruồi | Logistic +2.86 | 0.000633 | 0.109 | 3.06 | [1.55; 6.04] | Không đạt · p Holm ≥ 0.05 |
| 93 | k ngon | Logistic +3 | 0.00129 | 0.223 | 1.71 | [1.21; 2.42] | Không đạt · p Holm ≥ 0.05 |
| 233 | chỉ đc | Logistic +2.71 | — | — | 2.63 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 234 | cũng ko ngon | Logistic +2.725 | — | — | 1.33 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 235 | ko cần khách | Bayes +2.349 | — | — | 7.21 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 236 | kém quá | Bayes +2.459 | — | — | 7.21 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 237 | ra trong khi | Bayes +2.535 | — | — | 8.33 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 238 | rất không hài | Bayes +2.32 | — | — | 21.1 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 239 | thêm lần nào | Bayes +2.346 | — | — | 4.75 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 240 | thật thất | Bayes +2.526 | — | — | 5.64 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 241 | thật thất vọng | Bayes +2.66 | — | — | 5.64 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 242 | vọng thật sự | Bayes +2.43 | — | — | 10.8 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 243 | vụ rất kém | Bayes +2.374 | — | — | 15 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |

**ko** · Logistic +3.72. Tỷ lệ mức 2 trên test là 9.7% khi có cụm và 4.5% khi thiếu cụm (+5.2 điểm phần trăm). Có 759 review đúng mức chứa cụm từ 533 quán. TP/FP/FN/TN = 759/7052/2139/45140.
- Ngữ cảnh đã rút gọn: thay thành trứng cũng ko gọi báo / đã dặn ko bỏ rau vẫn lấy.
- Chênh lệch theo nhóm độ dài: nhóm 1: +9.3 đpt (17991 review, 1058 có cụm); nhóm 2: +6.7 đpt (18365 review, 3108 có cụm); nhóm 3: +3.3 đpt (18734 review, 3645 có cụm).

**chán** · Logistic +2.843. Tỷ lệ mức 2 trên test là 15.4% khi có cụm và 5.0% khi thiếu cụm (+10.4 điểm phần trăm). Có 176 review đúng mức chứa cụm từ 145 quán. TP/FP/FN/TN = 176/966/2722/51226.
- Ngữ cảnh đã rút gọn: mà làm nhìn chán thiệt sự đóng gói / bán kiểu gì nhìn chán đời đóng gói chưa.
- Chênh lệch theo nhóm độ dài: nhóm 1: +11.8 đpt (17991 review, 110 có cụm); nhóm 2: +14.7 đpt (18365 review, 386 có cụm); nhóm 3: +8.3 đpt (18734 review, 646 có cụm).

**nhạt** · Logistic +2.867. Tỷ lệ mức 2 trên test là 10.0% khi có cụm và 5.1% khi thiếu cụm (+5.0 điểm phần trăm). Có 191 review đúng mức chứa cụm từ 159 quán. TP/FP/FN/TN = 191/1711/2707/50481.
- Ngữ cảnh đã rút gọn: thì kh dẻo và nhạt toẹt nhưng là cái / mì nhạt mì đút lò phô.
- Chênh lệch theo nhóm độ dài: nhóm 1: +11.7 đpt (17991 review, 140 có cụm); nhóm 2: +11.9 đpt (18365 review, 549 có cụm); nhóm 3: +1.9 đpt (18734 review, 1213 có cụm).

**mong** · Logistic +2.524. Tỷ lệ mức 2 trên test là 11.5% khi có cụm và 5.2% khi thiếu cụm (+6.4 điểm phần trăm). Có 105 review đúng mức chứa cụm từ 95 quán. TP/FP/FN/TN = 105/805/2793/51387.
- Ngữ cảnh đã rút gọn: thì rất mặn luôn mong quán lưu ý hơn / mình ít nhất cx mong đợi là pizza phải.
- Chênh lệch theo nhóm độ dài: nhóm 1: +8.8 đpt (17991 review, 70 có cụm); nhóm 2: +6.6 đpt (18365 review, 320 có cụm); nhóm 3: +6.6 đpt (18734 review, 520 có cụm).

**không ngon** · Logistic +5.21. Tỷ lệ mức 2 trên test là 9.9% khi có cụm và 5.1% khi thiếu cụm (+4.8 điểm phần trăm). Có 133 review đúng mức chứa cụm từ 122 quán. TP/FP/FN/TN = 133/1205/2765/50987.
- Ngữ cảnh đã rút gọn: không ngon / không ngon m.
- Chênh lệch theo nhóm độ dài: nhóm 1: +18.4 đpt (17991 review, 143 có cụm); nhóm 2: +6.1 đpt (18365 review, 433 có cụm); nhóm 3: +2.2 đpt (18734 review, 762 có cụm).

**ko ngon** · Logistic +2.96. Tỷ lệ mức 2 trên test là 11.9% khi có cụm và 5.2% khi thiếu cụm (+6.7 điểm phần trăm). Có 66 review đúng mức chứa cụm từ 63 quán. TP/FP/FN/TN = 66/488/2832/51704.
- Ngữ cảnh đã rút gọn: nói là hom nay ko ngon mình có ăn thử / trải nghiệm món ăn ko ngon sai thiếu món.
- Chênh lệch theo nhóm độ dài: nhóm 1: +11.6 đpt (17991 review, 76 có cụm); nhóm 2: +9.0 đpt (18365 review, 236 có cụm); nhóm 3: +3.1 đpt (18734 review, 242 có cụm).

**cộc lốc** · Bayes +2.378. Tỷ lệ mức 2 trên test là 33.3% khi có cụm và 5.2% khi thiếu cụm (+28.1 điểm phần trăm). Có 13 review đúng mức chứa cụm từ 12 quán. TP/FP/FN/TN = 13/26/2885/52166.
- Ngữ cảnh đã rút gọn: nhăn nhó nói chuyện cộc lốc / thân thiện nói chuyện cộc lốc lại khó chịu với.
- Chênh lệch theo nhóm độ dài: nhóm 1: +27.8 đpt (17991 review, 3 có cụm); nhóm 2: +22.3 đpt (18365 review, 14 có cụm); nhóm 3: +32.5 đpt (18734 review, 22 có cụm).

### Tiếng Việt · rating 3

Kiểm định 20 ứng viên. Xác nhận 13 cụm.

| Hạng Holm | Cụm ứng viên | Model và trọng số | P-value thô | P-value Holm | OR | CI 95% | Quyết định |
|---:|---|---|---:|---:|---:|---|---|
| 23 | không ngon | Logistic +2.29 | 7.6e-26 | 1.84e-23 | 2.01 | [1.77; 2.3] | Xác nhận |
| 30 | bình thường | Logistic +2.063 | 8.76e-17 | 2.06e-14 | 1.58 | [1.42; 1.77] | Xác nhận |
| 56 | mùi vị tuyệt | Bayes +3.743 | 2.15e-10 | 4.49e-08 | 37.2 | [12; 116] | Xác nhận |
| 58 | cho biết | Logistic +2.271 | 1.68e-09 | 3.47e-07 | 1.86 | [1.52; 2.29] | Xác nhận |
| 59 | vị tuyệt vời | Bayes +3.305 | 8.94e-09 | 1.84e-06 | 8.85 | [4.14; 18.9] | Xác nhận |
| 60 | cho lắm | Logistic +1.995 | 1.39e-08 | 2.84e-06 | 1.59 | [1.35; 1.87] | Xác nhận |
| 64 | chật | Logistic +2.264 | 1.78e-07 | 3.59e-05 | 1.5 | [1.29; 1.76] | Xác nhận |
| 66 | vị tuyệt | Bayes +3.09 | 5.84e-07 | 0.000116 | 6.21 | [2.97; 13] | Xác nhận |
| 69 | chán | Logistic +2.01 | 1.25e-06 | 0.000245 | 1.44 | [1.24; 1.68] | Không đạt · OR < 1.5 |
| 76 | tuyệt vời mềm | Bayes +4.626 | 4.54e-06 | 0.000858 | 132 | [15.3; 1.15e+03] | Xác nhận |
| 77 | vời mềm | Bayes +4.634 | 4.54e-06 | 0.000858 | 132 | [15.3; 1.15e+03] | Xác nhận |
| 85 | tuyệt vời thơm | Bayes +4.522 | 0.000123 | 0.0221 | 20.6 | [4.09; 104] | Xác nhận |
| 86 | vời thơm | Bayes +4.583 | 0.000124 | 0.0222 | 13.8 | [3.39; 55.9] | Xác nhận |
| 87 | bình | Logistic +2.077 | 0.000141 | 0.0251 | 1.28 | [1.12; 1.46] | Không đạt · OR < 1.5 |
| 88 | mùo | Bayes +4.45 | 0.000208 | 0.0368 | 9.08 | [2.67; 30.9] | Xác nhận |
| 102 | tuy nhiên | Logistic +2.121 | 0.009 | 1 | 1.17 | [1.03; 1.34] | Không đạt · OR < 1.5; p Holm ≥ 0.05 |
| 114 | không thích | Logistic +1.988 | 0.056 | 1 | 1.15 | [0.968; 1.36] | Không đạt · OR < 1.5; CI chứa 1 hoặc thấp hơn; p Holm ≥ 0.05 |
| 244 | mùo vị | Bayes +5.459 | — | — | — | — | Chưa đủ bằng chứng · Ô đếm bằng 0 |
| 245 | mùo vị tuyệt | Bayes +6.117 | — | — | — | — | Chưa đủ bằng chứng · Ô đếm bằng 0 |
| 246 | thích lắm luôn | Logistic +2.255 | — | — | 0.0877 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |

**không ngon** · Logistic +2.29. Tỷ lệ mức 3 trên test là 32.4% khi có cụm và 19.2% khi thiếu cụm (+13.2 điểm phần trăm). Có 433 review đúng mức chứa cụm từ 326 quán. TP/FP/FN/TN = 433/905/10317/43435.
- Ngữ cảnh đã rút gọn: cơm không ngon / không ngon cũng không dở.
- Chênh lệch theo nhóm độ dài: nhóm 1: +3.5 đpt (17991 review, 143 có cụm); nhóm 2: +21.5 đpt (18365 review, 433 có cụm); nhóm 3: +15.8 đpt (18734 review, 762 có cụm).

**bình thường** · Logistic +2.063. Tỷ lệ mức 3 trên test là 27.2% khi có cụm và 19.1% khi thiếu cụm (+8.1 điểm phần trăm). Có 803 review đúng mức chứa cụm từ 538 quán. TP/FP/FN/TN = 803/2151/9947/42189.
- Ngữ cảnh đã rút gọn: thể mùi vị khá bình thường nếu cà ri nhiều / bình thường đặt gà giòn là.
- Chênh lệch theo nhóm độ dài: nhóm 1: +9.3 đpt (17991 review, 199 có cụm); nhóm 2: +17.1 đpt (18365 review, 920 có cụm); nhóm 3: +9.8 đpt (18734 review, 1835 có cụm).

**mùi vị tuyệt** · Bayes +3.743. Tỷ lệ mức 3 trên test là 90.0% khi có cụm và 19.5% khi thiếu cụm (+70.5 điểm phần trăm). Có 36 review đúng mức chứa cụm từ 19 quán. TP/FP/FN/TN = 36/4/10714/44336.
- Ngữ cảnh đã rút gọn: mùi vị tuyệt vời mềm ngon và / mùi vị tuyệt vời mềm và rất.
- Chênh lệch theo nhóm độ dài: nhóm 1: +64.4 đpt (17991 review, 39 có cụm); nhóm 3: -14.6 đpt (18734 review, 1 có cụm).

**cho biết** · Logistic +2.271. Tỷ lệ mức 3 trên test là 31.0% khi có cụm và 19.4% khi thiếu cụm (+11.6 điểm phần trăm). Có 191 review đúng mức chứa cụm từ 130 quán. TP/FP/FN/TN = 191/426/10559/43914.
- Ngữ cảnh đã rút gọn: thử món này cho biết / được mng nên thử cho biết.
- Chênh lệch theo nhóm độ dài: nhóm 1: -12.7 đpt (17991 review, 26 có cụm); nhóm 2: +20.6 đpt (18365 review, 197 có cụm); nhóm 3: +14.9 đpt (18734 review, 394 có cụm).

**vị tuyệt vời** · Bayes +3.305. Tỷ lệ mức 3 trên test là 68.1% khi có cụm và 19.5% khi thiếu cụm (+48.7 điểm phần trăm). Có 47 review đúng mức chứa cụm từ 23 quán. TP/FP/FN/TN = 47/22/10703/44318.
- Ngữ cảnh đã rút gọn: luôn hương vị tuyệt vời / mùi vị tuyệt vời mềm ngon và ngọt.
- Chênh lệch theo nhóm độ dài: nhóm 1: +55.8 đpt (17991 review, 55 có cụm); nhóm 2: +3.9 đpt (18365 review, 5 có cụm); nhóm 3: -14.7 đpt (18734 review, 9 có cụm).

**cho lắm** · Logistic +1.995. Tỷ lệ mức 3 trên test là 27.6% khi có cụm và 19.4% khi thiếu cụm (+8.2 điểm phần trăm). Có 273 review đúng mức chứa cụm từ 226 quán. TP/FP/FN/TN = 273/716/10477/43624.
- Ngữ cảnh đã rút gọn: cách chế biến này cho lắm nó là da heo / không hợp với mình cho lắm.
- Chênh lệch theo nhóm độ dài: nhóm 1: +2.3 đpt (17991 review, 33 có cụm); nhóm 2: +21.3 đpt (18365 review, 291 có cụm); nhóm 3: +9.0 đpt (18734 review, 665 có cụm).

**chật** · Logistic +2.264. Tỷ lệ mức 3 trên test là 26.6% khi có cụm và 19.4% khi thiếu cụm (+7.2 điểm phần trăm). Có 254 review đúng mức chứa cụm từ 176 quán. TP/FP/FN/TN = 254/702/10496/43638.
- Ngữ cảnh đã rút gọn: không ok lắm khá chật lúc mình vào ở / quán hơi chật cô bán nói chuyện.
- Chênh lệch theo nhóm độ dài: nhóm 1: +7.0 đpt (17991 review, 60 có cụm); nhóm 2: +12.3 đpt (18365 review, 301 có cụm); nhóm 3: +10.6 đpt (18734 review, 595 có cụm).

**vị tuyệt** · Bayes +3.09. Tỷ lệ mức 3 trên test là 60.0% khi có cụm và 19.5% khi thiếu cụm (+40.5 điểm phần trăm). Có 48 review đúng mức chứa cụm từ 23 quán. TP/FP/FN/TN = 48/32/10702/44308.
- Ngữ cảnh đã rút gọn: luôn hương vị tuyệt vời / mùi vị tuyệt vời mềm ngon và.
- Chênh lệch theo nhóm độ dài: nhóm 1: +54.6 đpt (17991 review, 57 có cụm); nhóm 2: -3.6 đpt (18365 review, 8 có cụm); nhóm 3: -14.7 đpt (18734 review, 15 có cụm).

**tuyệt vời mềm** · Bayes +4.626. Tỷ lệ mức 3 trên test là 97.0% khi có cụm và 19.5% khi thiếu cụm (+77.5 điểm phần trăm). Có 32 review đúng mức chứa cụm từ 18 quán. TP/FP/FN/TN = 32/1/10718/44339.
- Ngữ cảnh đã rút gọn: mùi vị tuyệt vời mềm ngon và ngọt / mùi vị tuyệt vời mềm và rất là ngọt.
- Chênh lệch theo nhóm độ dài: nhóm 1: +72.1 đpt (17991 review, 32 có cụm); nhóm 2: -16.1 đpt (18365 review, 1 có cụm).

**vời mềm** · Bayes +4.634. Tỷ lệ mức 3 trên test là 97.0% khi có cụm và 19.5% khi thiếu cụm (+77.5 điểm phần trăm). Có 32 review đúng mức chứa cụm từ 18 quán. TP/FP/FN/TN = 32/1/10718/44339.
- Ngữ cảnh đã rút gọn: mùi vị tuyệt vời mềm ngon và ngọt / mùi vị tuyệt vời mềm và rất là ngọt.
- Chênh lệch theo nhóm độ dài: nhóm 1: +72.1 đpt (17991 review, 32 có cụm); nhóm 2: -16.1 đpt (18365 review, 1 có cụm).

**tuyệt vời thơm** · Bayes +4.522. Tỷ lệ mức 3 trên test là 83.3% khi có cụm và 19.5% khi thiếu cụm (+63.8 điểm phần trăm). Có 10 review đúng mức chứa cụm từ 7 quán. TP/FP/FN/TN = 10/2/10740/44338.
- Ngữ cảnh đã rút gọn: kem là trên cả tuyệt vời thơm mềm béo không ngậy / mùo vị tuyệt vời thơm và ngọt.
- Chênh lệch theo nhóm độ dài: nhóm 1: +72.0 đpt (17991 review, 8 có cụm); nhóm 2: +33.9 đpt (18365 review, 2 có cụm); nhóm 3: +35.4 đpt (18734 review, 2 có cụm).

**vời thơm** · Bayes +4.583. Tỷ lệ mức 3 trên test là 76.9% khi có cụm và 19.5% khi thiếu cụm (+57.4 điểm phần trăm). Có 10 review đúng mức chứa cụm từ 7 quán. TP/FP/FN/TN = 10/3/10740/44337.
- Ngữ cảnh đã rút gọn: là trên cả tuyệt vời thơm mềm béo không ngậy / mùo vị tuyệt vời thơm và ngọt.
- Chênh lệch theo nhóm độ dài: nhóm 1: +72.0 đpt (17991 review, 8 có cụm); nhóm 2: +17.2 đpt (18365 review, 3 có cụm); nhóm 3: +35.4 đpt (18734 review, 2 có cụm).

**mùo** · Bayes +4.45. Tỷ lệ mức 3 trên test là 68.8% khi có cụm và 19.5% khi thiếu cụm (+49.3 điểm phần trăm). Có 11 review đúng mức chứa cụm từ 7 quán. TP/FP/FN/TN = 11/5/10739/44335.
- Ngữ cảnh đã rút gọn: mùo vị tuyệt vời thơm / mùo vị tuyệt vời mềm.
- Chênh lệch theo nhóm độ dài: nhóm 1: +62.9 đpt (17991 review, 11 có cụm); nhóm 2: +17.2 đpt (18365 review, 3 có cụm); nhóm 3: -14.6 đpt (18734 review, 2 có cụm).

### Tiếng Việt · rating 4

Kiểm định 20 ứng viên. Xác nhận 10 cụm.

| Hạng Holm | Cụm ứng viên | Model và trọng số | P-value thô | P-value Holm | OR | CI 95% | Quyết định |
|---:|---|---|---:|---:|---:|---|---|
| 2 | lắm | Logistic +2.766 | 9.13e-216 | 2.4e-213 | 2.77 | [2.6; 2.95] | Xác nhận |
| 3 | cũng | Logistic +5.152 | 4.83e-205 | 1.26e-202 | 3.01 | [2.8; 3.23] | Xác nhận |
| 4 | khá | Logistic +4.98 | 6.6e-167 | 1.72e-164 | 3.1 | [2.86; 3.36] | Xác nhận |
| 5 | giá | Logistic +2.688 | 3e-139 | 7.8e-137 | 2.35 | [2.2; 2.51] | Xác nhận |
| 6 | này | Logistic +3.382 | 3.25e-139 | 8.42e-137 | 2.51 | [2.33; 2.69] | Xác nhận |
| 9 | đông | Logistic +2.765 | 2.83e-101 | 7.24e-99 | 2.31 | [2.14; 2.49] | Xác nhận |
| 10 | thích | Logistic +3.197 | 2.82e-97 | 7.18e-95 | 2.54 | [2.33; 2.77] | Xác nhận |
| 12 | khá ngon | Logistic +4.178 | 2.58e-84 | 6.52e-82 | 2.71 | [2.45; 3] | Xác nhận |
| 22 | bên này | Logistic +2.875 | 6.21e-26 | 1.51e-23 | 4.28 | [3.26; 5.62] | Xác nhận |
| 63 | giá hơi đắt | Logistic +2.814 | 1.12e-07 | 2.26e-05 | 3.32 | [2.11; 5.23] | Xác nhận |
| 98 | lượng như hình | Bayes +3.172 | 0.00304 | 0.508 | 4.58 | [1.54; 13.6] | Không đạt · p Holm ≥ 0.05 |
| 247 | khá là rẽ | Bayes +2.82 | — | — | — | — | Chưa đủ bằng chứng · Ô đếm bằng 0 |
| 248 | kỳ luôn nhe | Bayes +2.806 | — | — | — | — | Chưa đủ bằng chứng · Ô đếm bằng 0 |
| 249 | lắm luôn nhe | Bayes +3.916 | — | — | — | — | Chưa đủ bằng chứng · Ô đếm bằng 0 |
| 250 | nhe giá cả | Bayes +3.006 | — | — | — | — | Chưa đủ bằng chứng · Ô đếm bằng 0 |
| 251 | nhe không gian | Bayes +3.178 | — | — | — | — | Chưa đủ bằng chứng · Ô đếm bằng 0 |
| 252 | nhe nhân | Bayes +2.699 | — | — | — | — | Chưa đủ bằng chứng · Ô đếm bằng 0 |
| 253 | nhe đồ | Bayes +2.864 | — | — | — | — | Chưa đủ bằng chứng · Ô đếm bằng 0 |
| 254 | nhe đồ ăn | Bayes +2.835 | — | — | — | — | Chưa đủ bằng chứng · Ô đếm bằng 0 |
| 255 | sđt ship | Bayes +2.956 | — | — | — | — | Chưa đủ bằng chứng · Ô đếm bằng 0 |

**lắm** · Logistic +2.766. Tỷ lệ mức 4 trên test là 66.9% khi có cụm và 42.2% khi thiếu cụm (+24.7 điểm phần trăm). Có 8809 review đúng mức chứa cụm từ 2752 quán. TP/FP/FN/TN = 8809/4355/17711/24215.
- Ngữ cảnh đã rút gọn: thịt chả ngon lắm / chín ăn còn cứng lắm quán ơi.
- Chênh lệch theo nhóm độ dài: nhóm 1: +11.3 đpt (17991 review, 1063 có cụm); nhóm 2: +13.6 đpt (18365 review, 3960 có cụm); nhóm 3: +9.5 đpt (18734 review, 8141 có cụm).

**cũng** · Logistic +5.152. Tỷ lệ mức 4 trên test là 63.6% khi có cụm và 36.7% khi thiếu cụm (+26.9 điểm phần trăm). Có 14924 review đúng mức chứa cụm từ 3627 quán. TP/FP/FN/TN = 14924/8556/11596/20014.
- Ngữ cảnh đã rút gọn: cũng đc / an cũng đc mua lớn ma.
- Chênh lệch theo nhóm độ dài: nhóm 1: +18.8 đpt (17991 review, 1707 có cụm); nhóm 2: +10.8 đpt (18365 review, 8104 có cụm); nhóm 3: +6.2 đpt (18734 review, 13669 có cụm).

**khá** · Logistic +4.98. Tỷ lệ mức 4 trên test là 67.8% khi có cụm và 40.5% khi thiếu cụm (+27.3 điểm phần trăm). Có 10421 review đúng mức chứa cụm từ 3075 quán. TP/FP/FN/TN = 10421/4940/16099/23630.
- Ngữ cảnh đã rút gọn: nước mắm hơi ngọt khá ngon / bỏ đưa cho khách khá ngon.
- Chênh lệch theo nhóm độ dài: nhóm 1: +21.4 đpt (17991 review, 1404 có cụm); nhóm 2: +15.2 đpt (18365 review, 4818 có cụm); nhóm 3: +12.0 đpt (18734 review, 9139 có cụm).

**giá** · Logistic +2.688. Tỷ lệ mức 4 trên test là 62.2% khi có cụm và 41.2% khi thiếu cụm (+21.0 điểm phần trăm). Có 11342 review đúng mức chứa cụm từ 3418 quán. TP/FP/FN/TN = 11342/6889/15178/21681.
- Ngữ cảnh đã rút gọn: giá hơi đắt / quán cải thiện nđánh giá chung.
- Chênh lệch theo nhóm độ dài: nhóm 1: +20.4 đpt (17991 review, 2114 có cụm); nhóm 2: +7.7 đpt (18365 review, 6524 có cụm); nhóm 3: +4.6 đpt (18734 review, 9593 có cụm).

**này** · Logistic +3.382. Tỷ lệ mức 4 trên test là 64.2% khi có cụm và 41.7% khi thiếu cụm (+22.5 điểm phần trăm). Có 10108 review đúng mức chứa cụm từ 3068 quán. TP/FP/FN/TN = 10108/5636/16412/22934.
- Ngữ cảnh đã rút gọn: chả hơi chua cơm này ăn cơm tấm hơi / mà hơi xu cái này.
- Chênh lệch theo nhóm độ dài: nhóm 1: +13.8 đpt (17991 review, 1110 có cụm); nhóm 2: +9.0 đpt (18365 review, 5080 có cụm); nhóm 3: +5.1 đpt (18734 review, 9554 có cụm).

**đông** · Logistic +2.765. Tỷ lệ mức 4 trên test là 65.4% khi có cụm và 45.1% khi thiếu cụm (+20.3 điểm phần trăm). Có 5397 review đúng mức chứa cụm từ 1785 quán. TP/FP/FN/TN = 5397/2850/21123/25720.
- Ngữ cảnh đã rút gọn: trách mà quán rất đông và thường hết rất / thì vẫn luôn luôn đông khách lúc nào tới.
- Chênh lệch theo nhóm độ dài: nhóm 1: +29.1 đpt (17991 review, 391 có cụm); nhóm 2: +9.6 đpt (18365 review, 2635 có cụm); nhóm 3: +1.6 đpt (18734 review, 5221 có cụm).

**thích** · Logistic +3.197. Tỷ lệ mức 4 trên test là 66.2% khi có cụm và 43.6% khi thiếu cụm (+22.6 điểm phần trăm). Có 7365 review đúng mức chứa cụm từ 2313 quán. TP/FP/FN/TN = 7365/3758/19155/24812.
- Ngữ cảnh đã rút gọn: shipper tốt bụng giải thích là quán làm sẵn / khách hàng có người thích ăn tương đen thì.
- Chênh lệch theo nhóm độ dài: nhóm 1: +10.0 đpt (17991 review, 1052 có cụm); nhóm 2: +12.8 đpt (18365 review, 3679 có cụm); nhóm 3: +9.1 đpt (18734 review, 6392 có cụm).

**khá ngon** · Logistic +4.178. Tỷ lệ mức 4 trên test là 70.6% khi có cụm và 47.0% khi thiếu cụm (+23.6 điểm phần trăm). Có 1906 review đúng mức chứa cụm từ 1084 quán. TP/FP/FN/TN = 1906/794/24614/27776.
- Ngữ cảnh đã rút gọn: nước mắm hơi ngọt khá ngon / bỏ đưa cho khách khá ngon.
- Chênh lệch theo nhóm độ dài: nhóm 1: +38.3 đpt (17991 review, 322 có cụm); nhóm 2: +15.2 đpt (18365 review, 948 có cụm); nhóm 3: +8.1 đpt (18734 review, 1430 có cụm).

**bên này** · Logistic +2.875. Tỷ lệ mức 4 trên test là 79.8% khi có cụm và 47.9% khi thiếu cụm (+31.8 điểm phần trăm). Có 272 review đúng mức chứa cụm từ 193 quán. TP/FP/FN/TN = 272/69/26248/28501.
- Ngữ cảnh đã rút gọn: giá bên này rẻ nhất ko nhầm / bên này họ bảo có ship.
- Chênh lệch theo nhóm độ dài: nhóm 1: +27.1 đpt (17991 review, 14 có cụm); nhóm 2: +30.1 đpt (18365 review, 112 có cụm); nhóm 3: +12.7 đpt (18734 review, 215 có cụm).

**giá hơi đắt** · Logistic +2.814. Tỷ lệ mức 4 trên test là 75.5% khi có cụm và 48.1% khi thiếu cụm (+27.4 điểm phần trăm). Có 80 review đúng mức chứa cụm từ 75 quán. TP/FP/FN/TN = 80/26/26440/28544.
- Ngữ cảnh đã rút gọn: giá hơi đắt / ko có kèm canh giá hơi đắt.
- Chênh lệch theo nhóm độ dài: nhóm 1: +65.7 đpt (17991 review, 35 có cụm); nhóm 2: +1.9 đpt (18365 review, 40 có cụm); nhóm 3: +19.7 đpt (18734 review, 31 có cụm).

### Tiếng Việt · rating 5

Kiểm định 20 ứng viên. Xác nhận 6 cụm.

| Hạng Holm | Cụm ứng viên | Model và trọng số | P-value thô | P-value Holm | OR | CI 95% | Quyết định |
|---:|---|---|---:|---:|---:|---|---|
| 11 | xỉu | Logistic +3.812 | 8.73e-88 | 2.22e-85 | 14.6 | [11.2; 19] | Xác nhận |
| 14 | ngon xỉu | Logistic +6.75 | 4.65e-57 | 1.17e-54 | 112 | [62.6; 201] | Xác nhận |
| 36 | gói tốt | Logistic +4.149 | 1.17e-13 | 2.69e-11 | 1.58e+03 | [221; 1.14e+04] | Xác nhận |
| 37 | đóng gói tốt | Logistic +4.133 | 1.17e-13 | 2.69e-11 | 1.58e+03 | [221; 1.14e+04] | Xác nhận |
| 47 | tiền sạch | Bayes +7.134 | 9.5e-12 | 2.07e-09 | 862 | [120; 6.2e+03] | Xác nhận |
| 81 | ngonn | Logistic +4.079 | 3.65e-05 | 0.00672 | 2.77 | [1.67; 4.57] | Xác nhận |
| 96 | gogi | Logistic +4.264 | 0.002 | 0.338 | 4.59 | [1.63; 13] | Không đạt · p Holm ≥ 0.05 |
| 101 | nghiện | Logistic +3.851 | 0.00639 | 1 | 1.29 | [1.06; 1.58] | Không đạt · OR < 1.5; p Holm ≥ 0.05 |
| 103 | ngờ | Logistic +3.71 | 0.0121 | 1 | 1.24 | [1.03; 1.5] | Không đạt · OR < 1.5; p Holm ≥ 0.05 |
| 127 | nhaa | Logistic +3.741 | 0.41 | 1 | 1.08 | [0.564; 2.06] | Không đạt · OR < 1.5; CI chứa 1 hoặc thấp hơn; p Holm ≥ 0.05 |
| 131 | không bị | Logistic +5.427 | 1 | 1 | 0.73 | [0.619; 0.86] | Không đạt · Sai chiều; OR < 1.5; CI chứa 1 hoặc thấp hơn; p Holm ≥ 0.05 |
| 256 | gói tốt sạch | Bayes +7.232 | — | — | — | — | Chưa đủ bằng chứng · Ô đếm bằng 0 |
| 257 | ngon xỉu đáng | Bayes +8.086 | — | — | — | — | Chưa đủ bằng chứng · Ô đếm bằng 0 |
| 258 | ngon xỉu đóng | Bayes +7.139 | — | — | — | — | Chưa đủ bằng chứng · Ô đếm bằng 0 |
| 259 | xỉu đáng | Bayes +8.089 | — | — | — | — | Chưa đủ bằng chứng · Ô đếm bằng 0 |
| 260 | xỉu đáng đồng | Bayes +8.086 | — | — | — | — | Chưa đủ bằng chứng · Ô đếm bằng 0 |
| 261 | xỉu đóng | Bayes +7.139 | — | — | — | — | Chưa đủ bằng chứng · Ô đếm bằng 0 |
| 262 | xỉu đóng gói | Bayes +7.139 | — | — | — | — | Chưa đủ bằng chứng · Ô đếm bằng 0 |
| 263 | đồng tiền sạch | Bayes +8.046 | — | — | — | — | Chưa đủ bằng chứng · Ô đếm bằng 0 |
| 264 | đồng tiền đóng | Bayes +7.31 | — | — | — | — | Chưa đủ bằng chứng · Ô đếm bằng 0 |

**xỉu** · Logistic +3.812. Tỷ lệ mức 5 trên test là 78.8% khi có cụm và 20.3% khi thiếu cụm (+58.5 điểm phần trăm). Có 491 review đúng mức chứa cụm từ 213 quán. TP/FP/FN/TN = 491/132/11052/43415.
- Ngữ cảnh đã rút gọn: ngon xỉu đóng gói tốt / ngonnn sạch sẽ ngon xỉu sạch sẽ.
- Chênh lệch theo nhóm độ dài: nhóm 1: +65.3 đpt (17991 review, 421 có cụm); nhóm 2: +40.9 đpt (18365 review, 107 có cụm); nhóm 3: +3.4 đpt (18734 review, 95 có cụm).

**ngon xỉu** · Logistic +6.75. Tỷ lệ mức 5 trên test là 96.6% khi có cụm và 20.3% khi thiếu cụm (+76.3 điểm phần trăm). Có 457 review đúng mức chứa cụm từ 186 quán. TP/FP/FN/TN = 457/16/11086/43531.
- Ngữ cảnh đã rút gọn: ngon xỉu đóng gói tốt / ngonnn sạch sẽ ngon xỉu sạch sẽ.
- Chênh lệch theo nhóm độ dài: nhóm 1: +66.4 đpt (17991 review, 408 có cụm); nhóm 2: +72.4 đpt (18365 review, 52 có cụm); nhóm 3: +12.8 đpt (18734 review, 13 có cụm).

**gói tốt** · Logistic +4.149. Tỷ lệ mức 5 trên test là 99.8% khi có cụm và 20.4% khi thiếu cụm (+79.4 điểm phần trăm). Có 405 review đúng mức chứa cụm từ 166 quán. TP/FP/FN/TN = 405/1/11138/43546.
- Ngữ cảnh đã rút gọn: ngon xỉu đóng gói tốt / tiền đóng gói tốt.
- Chênh lệch theo nhóm độ dài: nhóm 1: +66.2 đpt (17991 review, 366 có cụm); nhóm 2: +82.0 đpt (18365 review, 39 có cụm); nhóm 3: +89.7 đpt (18734 review, 1 có cụm).

**đóng gói tốt** · Logistic +4.133. Tỷ lệ mức 5 trên test là 99.8% khi có cụm và 20.4% khi thiếu cụm (+79.4 điểm phần trăm). Có 405 review đúng mức chứa cụm từ 166 quán. TP/FP/FN/TN = 405/1/11138/43546.
- Ngữ cảnh đã rút gọn: ngon xỉu đóng gói tốt / tiền đóng gói tốt.
- Chênh lệch theo nhóm độ dài: nhóm 1: +66.2 đpt (17991 review, 366 có cụm); nhóm 2: +82.0 đpt (18365 review, 39 có cụm); nhóm 3: +89.7 đpt (18734 review, 1 có cụm).

**tiền sạch** · Bayes +7.134. Tỷ lệ mức 5 trên test là 99.6% khi có cụm và 20.6% khi thiếu cụm (+78.9 điểm phần trăm). Có 224 review đúng mức chứa cụm từ 122 quán. TP/FP/FN/TN = 224/1/11319/43546.
- Ngữ cảnh đã rút gọn: tiền sạch sẽ / tiền sạch sẽ đóng gói tốt.
- Chênh lệch theo nhóm độ dài: nhóm 1: +65.9 đpt (17991 review, 202 có cụm); nhóm 2: +81.9 đpt (18365 review, 22 có cụm); nhóm 3: -10.3 đpt (18734 review, 1 có cụm).

**ngonn** · Logistic +4.079. Tỷ lệ mức 5 trên test là 42.3% khi có cụm và 20.9% khi thiếu cụm (+21.3 điểm phần trăm). Có 30 review đúng mức chứa cụm từ 26 quán. TP/FP/FN/TN = 30/41/11513/43506.
- Ngữ cảnh đã rút gọn: ngonn lắm ln nhưng mà / thoi nhưng mà vẫn ngonn như ngày nào 10đ.
- Chênh lệch theo nhóm độ dài: nhóm 1: +37.2 đpt (17991 review, 25 có cụm); nhóm 2: +29.2 đpt (18365 review, 19 có cụm); nhóm 3: +0.8 đpt (18734 review, 27 có cụm).

### Tiếng Anh · rating 1

Kiểm định 15 ứng viên. Xác nhận 0 cụm.

| Hạng Holm | Cụm ứng viên | Model và trọng số | P-value thô | P-value Holm | OR | CI 95% | Quyết định |
|---:|---|---|---:|---:|---:|---|---|
| 94 | hanoi | Logistic +4.328 | 0.00151 | 0.258 | 2.21 | [1.31; 3.74] | Không đạt · p Holm ≥ 0.05 |
| 110 | worst | Logistic +2.407 / Bayes +0.7511 | 0.0369 | 1 | 3.36 | [0.89; 12.7] | Không đạt · CI chứa 1 hoặc thấp hơn; p Holm ≥ 0.05 |
| 118 | bad | Logistic +3.023 | 0.134 | 1 | 1.81 | [0.633; 5.16] | Không đạt · CI chứa 1 hoặc thấp hơn; p Holm ≥ 0.05 |
| 126 | good food | Logistic +2.511 | 0.363 | 1 | 1.09 | [0.664; 1.8] | Không đạt · OR < 1.5; CI chứa 1 hoặc thấp hơn; p Holm ≥ 0.05 |
| 132 | amazing service | Logistic +2.38 / Bayes +0.5284 | — | — | 5.18 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 133 | attitude | Logistic +2.263 / Bayes +0.441 | — | — | 2.44 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 134 | clean | Logistic +2.356 | — | — | 0.461 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 135 | good food good | Bayes +0.4126 | — | — | 0.979 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 136 | how to eat | Bayes +0.3768 | — | — | 3.36 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 137 | not fresh | Bayes +0.5236 | — | — | 3.46 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 138 | old quarter | Bayes +0.8355 | — | — | 1.14 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 139 | owner | Logistic +2.326 | — | — | 0.654 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 140 | quarter | Bayes +0.7234 | — | — | 0.791 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 141 | terrible | Logistic +4.786 / Bayes +1.38 | — | — | 1.82 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 142 | trang | Logistic +3.625 / Bayes +0.793 | — | — | 2.81 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |

### Tiếng Anh · rating 2

Kiểm định 11 ứng viên. Xác nhận 1 cụm.

| Hạng Holm | Cụm ứng viên | Model và trọng số | P-value thô | P-value Holm | OR | CI 95% | Quyết định |
|---:|---|---|---:|---:|---:|---|---|
| 40 | not fresh | Logistic +1.998 / Bayes +0.4808 | 1.36e-12 | 3.05e-10 | 8.29 | [4.58; 15] | Xác nhận |
| 106 | hanoi | Logistic +2.18 | 0.0226 | 1 | 2.12 | [1.02; 4.41] | Không đạt · p Holm ≥ 0.05 |
| 108 | server | Logistic +2.1 | 0.029 | 1 | 1.82 | [0.98; 3.39] | Không đạt · CI chứa 1 hoặc thấp hơn; p Holm ≥ 0.05 |
| 124 | us | Logistic +1.892 | 0.213 | 1 | 1.21 | [0.757; 1.93] | Không đạt · OR < 1.5; CI chứa 1 hoặc thấp hơn; p Holm ≥ 0.05 |
| 130 | eat | Logistic +2.14 | 0.953 | 1 | 0.531 | [0.253; 1.12] | Không đạt · Sai chiều; OR < 1.5; CI chứa 1 hoặc thấp hơn; p Holm ≥ 0.05 |
| 143 | compared | Logistic +1.883 | — | — | 1.57 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 144 | limited | Logistic +1.993 | — | — | 2.55 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 145 | not worth | Logistic +2.359 / Bayes +0.5216 | — | — | 3.98 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 146 | poor | Logistic +2.426 / Bayes +0.1722 | — | — | 0.832 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 147 | showed | Bayes +0.2864 | — | — | 1.85 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 148 | trang | Logistic +2.809 / Bayes +0.1623 | — | — | 1.37 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |

**not fresh** · Logistic +1.998 / Bayes +0.4808. Tỷ lệ mức 2 trên test là 31.2% khi có cụm và 5.2% khi thiếu cụm (+26.1 điểm phần trăm). Có 10 review đúng mức chứa cụm từ 5 quán. TP/FP/FN/TN = 10/22/336/6130.
- Ngữ cảnh đã rút gọn: also chill crabs not fresh meat quite watery / chicken and fish are not fresh at all hard and.
- Chênh lệch theo nhóm độ dài: nhóm 1: +36.2 đpt (2189 review, 7 có cụm); nhóm 2: +39.7 đpt (2079 review, 11 có cụm); nhóm 3: +11.1 đpt (2230 review, 14 có cụm).

### Tiếng Anh · rating 3

Kiểm định 15 ứng viên. Xác nhận 1 cụm.

| Hạng Holm | Cụm ứng viên | Model và trọng số | P-value thô | P-value Holm | OR | CI 95% | Quyết định |
|---:|---|---|---:|---:|---:|---|---|
| 80 | not as | Bayes +0.4601 | 3.53e-05 | 0.00654 | 4.41 | [2.12; 9.16] | Xác nhận |
| 115 | average | Logistic +2.913 | 0.0561 | 1 | 2.06 | [0.844; 5.05] | Không đạt · CI chứa 1 hoặc thấp hơn; p Holm ≥ 0.05 |
| 116 | ok | Logistic +2.898 / Bayes +0.2149 | 0.0562 | 1 | 2.16 | [0.835; 5.58] | Không đạt · CI chứa 1 hoặc thấp hơn; p Holm ≥ 0.05 |
| 117 | only | Logistic +2.16 | 0.0589 | 1 | 1.72 | [0.872; 3.39] | Không đạt · CI chứa 1 hoặc thấp hơn; p Holm ≥ 0.05 |
| 149 | buffet | Logistic +2.532 | — | — | 3.55 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 150 | buffet spread | Bayes +0.3974 | — | — | 2.6 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 151 | crabs | Logistic +2.549 / Bayes +0.6902 | — | — | 1.49 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 152 | food variety | Bayes +0.6156 | — | — | 6.3 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 153 | limited | Logistic +4.019 / Bayes +0.8359 | — | — | 4.86 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 154 | not fresh | Bayes +0.7041 | — | — | 4.21 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 155 | not much | Logistic +2.286 / Bayes +1.25 | — | — | 7.09 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 156 | not worth | Bayes +0.8362 | — | — | 7.09 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 157 | okay | Logistic +2.083 | — | — | 1.27 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 158 | salty | Logistic +2.17 / Bayes +0.4978 | — | — | 3 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 159 | wasn't | Logistic +2.328 | — | — | 0.527 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |

**not as** · Bayes +0.4601. Tỷ lệ mức 3 trên test là 22.4% khi có cụm và 6.1% khi thiếu cụm (+16.2 điểm phần trăm). Có 15 review đúng mức chứa cụm từ 5 quán. TP/FP/FN/TN = 15/52/395/6036.
- Ngữ cảnh đã rút gọn: that their food are not as good as before / food was not as good as before.
- Chênh lệch theo nhóm độ dài: nhóm 1: +46.1 đpt (2189 review, 13 có cụm); nhóm 2: +40.0 đpt (2079 review, 15 có cụm); nhóm 3: -1.5 đpt (2230 review, 39 có cụm).

### Tiếng Anh · rating 4

Kiểm định 17 ứng viên. Xác nhận 1 cụm.

| Hạng Holm | Cụm ứng viên | Model và trọng số | P-value thô | P-value Holm | OR | CI 95% | Quyết định |
|---:|---|---|---:|---:|---:|---|---|
| 65 | overall | Logistic +2.982 | 2.21e-07 | 4.42e-05 | 2.75 | [1.86; 4.08] | Xác nhận |
| 90 | salty | Bayes +0.5625 | 0.000521 | 0.0913 | 3.62 | [1.68; 7.82] | Không đạt · p Holm ≥ 0.05 |
| 91 | tea | Logistic +2.05 | 0.000537 | 0.0934 | 3.73 | [1.69; 8.19] | Không đạt · p Holm ≥ 0.05 |
| 107 | coffee | Logistic +1.962 | 0.0246 | 1 | 2.43 | [1; 5.88] | Không đạt · p Holm ≥ 0.05 |
| 112 | however | Logistic +3.599 | 0.0377 | 1 | 1.76 | [0.944; 3.26] | Không đạt · CI chứa 1 hoặc thấp hơn; p Holm ≥ 0.05 |
| 123 | seafood | Logistic +2.015 | 0.204 | 1 | 1.52 | [0.563; 4.12] | Không đạt · CI chứa 1 hoặc thấp hơn; p Holm ≥ 0.05 |
| 160 | base | Bayes +0.5994 | — | — | — | — | Chưa đủ bằng chứng · Ô đếm bằng 0 |
| 161 | clearing | Bayes +0.4663 | — | — | 1.87 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 162 | desserts | Logistic +2.227 | — | — | 2.46 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 163 | durian | Logistic +2.165 / Bayes +0.8302 | — | — | 2.73 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 164 | except | Bayes +0.7622 | — | — | 3.74 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 165 | food variety | Bayes +0.4376 | — | — | 1.73 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 166 | good spread | Bayes +0.4885 | — | — | 1.92 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 167 | items | Logistic +1.943 | — | — | 1.78 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 168 | not bad | Logistic +1.886 / Bayes +0.8023 | — | — | 3 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 169 | otherwise | Logistic +2.002 / Bayes +0.5244 | — | — | 0.944 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 170 | service was good | Bayes +0.7397 | — | — | 2.03 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |

**overall** · Logistic +2.982. Tỷ lệ mức 4 trên test là 20.6% khi có cụm và 8.6% khi thiếu cụm (+12.0 điểm phần trăm). Có 45 review đúng mức chứa cụm từ 8 quán. TP/FP/FN/TN = 45/173/542/5738.
- Ngữ cảnh đã rút gọn: overall a satisfying meal / the food and overall service were good and.
- Chênh lệch theo nhóm độ dài: nhóm 1: +31.6 đpt (2189 review, 24 có cụm); nhóm 2: +29.7 đpt (2079 review, 48 có cụm); nhóm 3: +7.3 đpt (2230 review, 146 có cụm).

### Tiếng Anh · rating 5

Kiểm định 19 ứng viên. Xác nhận 4 cụm.

| Hạng Holm | Cụm ứng viên | Model và trọng số | P-value thô | P-value Holm | OR | CI 95% | Quyết định |
|---:|---|---|---:|---:|---:|---|---|
| 73 | read more | Logistic +5.764 | 1.64e-06 | 0.000314 | 9.78 | [3.74; 25.6] | Xác nhận |
| 74 | read | Logistic +5.693 | 1.83e-06 | 0.00035 | 9.24 | [3.6; 23.7] | Xác nhận |
| 79 | always | Logistic +4.156 | 3.03e-05 | 0.00563 | 1.99 | [1.42; 2.8] | Xác nhận |
| 84 | best | Logistic +3.44 | 4.59e-05 | 0.00831 | 2.29 | [1.51; 3.46] | Xác nhận |
| 99 | delicious | Logistic +2.85 | 0.00552 | 0.916 | 1.75 | [1.14; 2.7] | Không đạt · p Holm ≥ 0.05 |
| 100 | excellent | Logistic +3.486 | 0.00598 | 0.987 | 1.72 | [1.13; 2.62] | Không đạt · p Holm ≥ 0.05 |
| 105 | great | Logistic +5.076 | 0.0197 | 1 | 1.65 | [1.02; 2.65] | Không đạt · p Holm ≥ 0.05 |
| 111 | fast delivery | Bayes +2.412 | 0.0375 | 1 | 6.74 | [0.825; 55] | Không đạt · CI chứa 1 hoặc thấp hơn; p Holm ≥ 0.05 |
| 128 | pizza | Logistic +5.45 | 0.549 | 1 | 0.923 | [0.257; 3.32] | Không đạt · Sai chiều; OR < 1.5; CI chứa 1 hoặc thấp hơn; p Holm ≥ 0.05 |
| 129 | bar | Logistic +2.74 | 0.593 | 1 | 0.855 | [0.231; 3.16] | Không đạt · Sai chiều; OR < 1.5; CI chứa 1 hoặc thấp hơn; p Holm ≥ 0.05 |
| 171 | always great | Bayes +2.659 | — | — | 0.42 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 172 | bass | Bayes +2.416 | — | — | — | — | Chưa đủ bằng chứng · Ô đếm bằng 0 |
| 173 | best pizza | Bayes +2.6 | — | — | — | — | Chưa đủ bằng chứng · Ô đếm bằng 0 |
| 174 | burrata | Bayes +2.705 | — | — | — | — | Chưa đủ bằng chứng · Ô đếm bằng 0 |
| 175 | cuban | Bayes +2.516 | — | — | — | — | Chưa đủ bằng chứng · Ô đếm bằng 0 |
| 176 | italian | Bayes +2.428 | — | — | — | — | Chưa đủ bằng chứng · Ô đếm bằng 0 |
| 177 | miami | Logistic +3.399 / Bayes +3.639 | — | — | — | — | Chưa đủ bằng chứng · Ô đếm bằng 0 |
| 178 | opera | Bayes +2.414 | — | — | 2.52 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 179 | sea bass | Bayes +2.387 | — | — | — | — | Chưa đủ bằng chứng · Ô đếm bằng 0 |

**read more** · Logistic +5.764. Tỷ lệ mức 5 trên test là 94.8% khi có cụm và 64.9% khi thiếu cụm (+29.9 điểm phần trăm). Có 1140 review đúng mức chứa cụm từ 38 quán. TP/FP/FN/TN = 1140/63/3437/1858.
- Ngữ cảnh đã rút gọn: read more / we had left and read more about the restaurant we.
- Chênh lệch theo nhóm độ dài: nhóm 2: +14.8 đpt (2079 review, 12 có cụm); nhóm 3: +25.3 đpt (2230 review, 1191 có cụm).

**read** · Logistic +5.693. Tỷ lệ mức 5 trên test là 94.5% khi có cụm và 64.9% khi thiếu cụm (+29.6 điểm phần trăm). Có 1146 review đúng mức chứa cụm từ 39 quán. TP/FP/FN/TN = 1146/67/3431/1854.
- Ngữ cảnh đã rút gọn: those positive reviews i read online seems questionable though / read more.
- Chênh lệch theo nhóm độ dài: nhóm 1: -59.3 đpt (2189 review, 1 có cụm); nhóm 2: +14.8 đpt (2079 review, 12 có cụm); nhóm 3: +25.1 đpt (2230 review, 1200 có cụm).

**always** · Logistic +4.156. Tỷ lệ mức 5 trên test là 82.3% khi có cụm và 70.0% khi thiếu cụm (+12.3 điểm phần trăm). Có 209 review đúng mức chứa cụm từ 58 quán. TP/FP/FN/TN = 209/45/4368/1876.
- Ngữ cảnh đã rút gọn: always the best / fantastic as always.
- Chênh lệch theo nhóm độ dài: nhóm 1: +30.1 đpt (2189 review, 61 có cụm); nhóm 2: +4.7 đpt (2079 review, 56 có cụm); nhóm 3: +0.1 đpt (2230 review, 137 có cụm).

**best** · Logistic +3.44. Tỷ lệ mức 5 trên test là 83.8% khi có cụm và 69.4% khi thiếu cụm (+14.4 điểm phần trăm). Có 394 review đúng mức chứa cụm từ 66 quán. TP/FP/FN/TN = 394/76/4183/1845.
- Ngữ cảnh đã rút gọn: always the best / best mexican place in town.
- Chênh lệch theo nhóm độ dài: nhóm 1: +10.3 đpt (2189 review, 65 có cụm); nhóm 2: +12.5 đpt (2079 review, 142 có cụm); nhóm 3: +7.1 đpt (2230 review, 263 có cụm).

### Tiếng Nhật · rating 1

Kiểm định 18 ứng viên. Xác nhận 9 cụm.

| Hạng Holm | Cụm ứng viên | Model và trọng số | P-value thô | P-value Holm | OR | CI 95% | Quyết định |
|---:|---|---|---:|---:|---:|---|---|
| 26 | 時間 | Logistic +2.54 | 9.79e-21 | 2.34e-18 | 9.16 | [5.73; 14.6] | Xác nhận |
| 28 | ない | Logistic +4.747 | 1.13e-17 | 2.68e-15 | 8.23 | [5.06; 13.4] | Xác nhận |
| 29 | れ | Logistic +2.385 | 3.52e-17 | 8.3e-15 | 6.77 | [4.32; 10.6] | Xác nhận |
| 31 | 最悪 | Logistic +4.082 / Bayes +1.294 | 1.65e-16 | 3.87e-14 | 19.4 | [9.51; 39.5] | Xác nhận |
| 48 | し | Logistic +2.319 | 2.1e-11 | 4.57e-09 | 4.23 | [2.76; 6.49] | Xác nhận |
| 49 | 頼ん | Logistic +2.242 | 2.81e-11 | 6.07e-09 | 7.51 | [4.11; 13.7] | Xác nhận |
| 54 | れ た | Logistic +2.366 / Bayes +0.8678 | 1.51e-10 | 3.18e-08 | 11.8 | [5.48; 25.5] | Xác nhận |
| 70 | なかっ た | Logistic +2.345 | 1.52e-06 | 0.000296 | 4.29 | [2.33; 7.91] | Xác nhận |
| 71 | なかっ | Logistic +2.361 | 1.52e-06 | 0.000296 | 4.26 | [2.32; 7.82] | Xác nhận |
| 181 | い ない | Bayes +0.7763 | — | — | 7.11 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 182 | し ない | Bayes +1.048 | — | — | 10.8 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 183 | すぎる | Logistic +2.955 | — | — | 5.13 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 184 | た のに | Bayes +0.6937 | — | — | 9.21 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 185 | た もの | Bayes +1.305 | — | — | 14.7 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 186 | 全く | Bayes +0.7965 | — | — | 15.6 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 187 | 商品 | Bayes +0.7038 | — | — | 6.05 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 188 | 届い た | Bayes +0.5941 | — | — | 9.59 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 189 | 連絡 | Bayes +0.6788 | — | — | 23.8 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |

**時間** · Logistic +2.54. Tỷ lệ mức 1 trên test là 16.4% khi có cụm và 2.1% khi thiếu cụm (+14.3 điểm phần trăm). Có 24 review đúng mức chứa cụm từ 18 quán. TP/FP/FN/TN = 24/122/127/5914.
- Ngữ cảnh đã rút gọn: し て から 1 時間 たっ て も 配達 / から 受け取り まで 1 時間 かかり まし た.
- Chênh lệch theo nhóm độ dài: nhóm 2: +14.1 đpt (2571 review, 13 có cụm); nhóm 3: +11.9 đpt (2073 review, 133 có cụm).

**ない** · Logistic +4.747. Tỷ lệ mức 1 trên test là 13.1% khi có cụm và 1.8% khi thiếu cụm (+11.3 điểm phần trăm). Có 46 review đúng mức chứa cụm từ 34 quán. TP/FP/FN/TN = 46/305/105/5731.
- Ngữ cảnh đã rút gọn: 麺 が 入っ て ない です / 納豆 と サラダ ない です よ.
- Chênh lệch theo nhóm độ dài: nhóm 1: +12.3 đpt (1543 review, 8 có cụm); nhóm 2: +9.2 đpt (2571 review, 48 có cụm); nhóm 3: +9.5 đpt (2073 review, 295 có cụm).

**れ** · Logistic +2.385. Tỷ lệ mức 1 trên test là 12.8% khi có cụm và 2.1% khi thiếu cụm (+10.7 điểm phần trăm). Có 23 review đúng mức chứa cụm từ 21 quán. TP/FP/FN/TN = 23/156/128/5880.
- Ngữ cảnh đã rút gọn: て も 配達 さ れ ない の は さすが / て 非常 に 待たさ れ た 挙句 届い た.
- Chênh lệch theo nhóm độ dài: nhóm 1: -0.3 đpt (1543 review, 1 có cụm); nhóm 2: +13.0 đpt (2571 review, 7 có cụm); nhóm 3: +8.1 đpt (2073 review, 171 có cụm).

**最悪** · Logistic +4.082 / Bayes +1.294. Tỷ lệ mức 1 trên test là 31.2% khi có cụm và 2.3% khi thiếu cụm (+29.0 điểm phần trăm). Có 10 review đúng mức chứa cụm từ 10 quán. TP/FP/FN/TN = 10/22/141/6014.
- Ngữ cảnh đã rút gọn: 言っ て 来 て 最悪 / 最悪 でし た.
- Chênh lệch theo nhóm độ dài: nhóm 1: -0.3 đpt (1543 review, 2 có cụm); nhóm 2: +20.9 đpt (2571 review, 9 có cụm); nhóm 3: +33.0 đpt (2073 review, 21 có cụm).

**し** · Logistic +2.319. Tỷ lệ mức 1 trên test là 6.9% khi có cụm và 1.7% khi thiếu cụm (+5.2 điểm phần trăm). Có 60 review đúng mức chứa cụm từ 37 quán. TP/FP/FN/TN = 60/814/91/5222.
- Ngữ cảnh đã rút gọn: 注文 を し て から 1 時間 / お 弁当 を オーダー し た のに 大変 残念.
- Chênh lệch theo nhóm độ dài: nhóm 1: -0.3 đpt (1543 review, 11 có cụm); nhóm 2: +3.4 đpt (2571 review, 132 có cụm); nhóm 3: +3.1 đpt (2073 review, 731 có cụm).

**頼ん** · Logistic +2.242. Tỷ lệ mức 1 trên test là 14.7% khi có cụm và 2.2% khi thiếu cụm (+12.5 điểm phần trăm). Có 14 review đúng mức chứa cụm từ 12 quán. TP/FP/FN/TN = 14/81/137/5955.
- Ngữ cảnh đã rút gọn: シーザー サラダ を 頼ん だ のに caesar と / おにぎり を 鮭 を 頼ん だ のに ツナマヨ だっ.
- Chênh lệch theo nhóm độ dài: nhóm 1: -0.3 đpt (1543 review, 1 có cụm); nhóm 2: +23.8 đpt (2571 review, 16 có cụm); nhóm 3: +7.7 đpt (2073 review, 78 có cụm).

**れ た** · Logistic +2.366 / Bayes +0.8678. Tỷ lệ mức 1 trên test là 21.7% khi có cụm và 2.3% khi thiếu cụm (+19.4 điểm phần trăm). Có 10 review đúng mức chứa cụm từ 9 quán. TP/FP/FN/TN = 10/36/141/6000.
- Ngữ cảnh đã rút gọn: て 非常 に 待たさ れ た 挙句 届い た 料理 / お金 だけ 取ら れ た.
- Chênh lệch theo nhóm độ dài: nhóm 1: -0.3 đpt (1543 review, 1 có cụm); nhóm 2: -1.4 đpt (2571 review, 1 có cụm); nhóm 3: +17.7 đpt (2073 review, 44 có cụm).

**なかっ た** · Logistic +2.345. Tỷ lệ mức 1 trên test là 9.2% khi có cụm và 2.3% khi thiếu cụm (+6.9 điểm phần trăm). Có 12 review đúng mức chứa cụm từ 11 quán. TP/FP/FN/TN = 12/119/139/5917.
- Ngữ cảnh đã rút gọn: ピザ も 硬く 美味しく なかっ た / が ゆがか れ て なかっ た の は いつも の.
- Chênh lệch theo nhóm độ dài: nhóm 2: +22.2 đpt (2571 review, 30 có cụm); nhóm 3: -0.5 đpt (2073 review, 101 có cụm).

**なかっ** · Logistic +2.361. Tỷ lệ mức 1 trên test là 9.1% khi có cụm và 2.3% khi thiếu cụm (+6.8 điểm phần trăm). Có 12 review đúng mức chứa cụm từ 11 quán. TP/FP/FN/TN = 12/120/139/5916.
- Ngữ cảnh đã rút gọn: ピザ も 硬く 美味しく なかっ た / が ゆがか れ て なかっ た の は いつも.
- Chênh lệch theo nhóm độ dài: nhóm 2: +22.2 đpt (2571 review, 30 có cụm); nhóm 3: -0.5 đpt (2073 review, 102 có cụm).

### Tiếng Nhật · rating 2

Kiểm định 14 ứng viên. Xác nhận 6 cụm.

| Hạng Holm | Cụm ứng viên | Model và trọng số | P-value thô | P-value Holm | OR | CI 95% | Quyết định |
|---:|---|---|---:|---:|---:|---|---|
| 33 | 残念 | Logistic +2.602 | 1.13e-15 | 2.62e-13 | 9 | [5.23; 15.5] | Xác nhận |
| 41 | なかっ た | Logistic +2.225 / Bayes +0.1825 | 2.05e-12 | 4.59e-10 | 7.79 | [4.36; 13.9] | Xác nhận |
| 42 | ない | Logistic +4.222 | 2.31e-12 | 5.14e-10 | 5.16 | [3.24; 8.22] | Xác nhận |
| 43 | なかっ | Logistic +2.355 / Bayes +0.1883 | 4.23e-12 | 9.39e-10 | 7.72 | [4.3; 13.9] | Xác nhận |
| 67 | のに | Logistic +1.925 / Bayes +0.06373 | 7.47e-07 | 0.000148 | 7.11 | [3.2; 15.8] | Xác nhận |
| 82 | か | Logistic +2.083 | 3.89e-05 | 0.00712 | 3.61 | [1.91; 6.83] | Xác nhận |
| 190 | しか | Bayes +0.6313 | — | — | 9.29 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 191 | た のに | Bayes +0.2862 | — | — | 11.5 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 192 | てる | Logistic +2.472 / Bayes +0.05602 | — | — | 1.58 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 193 | 写真 | Logistic +2.013 / Bayes +0.2616 | — | — | 6.99 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 194 | 冷め | Logistic +2.211 / Bayes +0.3301 | — | — | 3.87 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 195 | 美味しく なかっ | Bayes +1.108 | — | — | 5.13 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 196 | 美味しく なかっ た | Bayes +1.108 | — | — | 5.13 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 197 | 肉 | Logistic +2.192 | — | — | 2.79 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |

**残念** · Logistic +2.602. Tỷ lệ mức 2 trên test là 16.3% khi có cụm và 2.1% khi thiếu cụm (+14.1 điểm phần trăm). Có 20 review đúng mức chứa cụm từ 15 quán. TP/FP/FN/TN = 20/103/128/5936.
- Ngữ cảnh đã rút gọn: 残念 です / ご飯 が 少なく て 残念 でし た.
- Chênh lệch theo nhóm độ dài: nhóm 1: -0.6 đpt (1543 review, 2 có cụm); nhóm 2: +8.6 đpt (2571 review, 10 có cụm); nhóm 3: +12.9 đpt (2073 review, 111 có cụm).

**なかっ た** · Logistic +2.225 / Bayes +0.1825. Tỷ lệ mức 2 trên test là 14.5% khi có cụm và 2.1% khi thiếu cụm (+12.4 điểm phần trăm). Có 19 review đúng mức chứa cụm từ 15 quán. TP/FP/FN/TN = 19/112/129/5927.
- Ngữ cảnh đã rút gọn: 多く 全部 食べ られ なかっ た / は カラシ しか ついて なかっ た が 何 も 味.
- Chênh lệch theo nhóm độ dài: nhóm 2: +22.2 đpt (2571 review, 30 có cụm); nhóm 3: +7.3 đpt (2073 review, 101 có cụm).

**ない** · Logistic +4.222. Tỷ lệ mức 2 trên test là 9.4% khi có cụm và 2.0% khi thiếu cụm (+7.4 điểm phần trăm). Có 33 review đúng mức chứa cụm từ 20 quán. TP/FP/FN/TN = 33/318/115/5721.
- Ngữ cảnh đã rút gọn: 再 注文 は し ない と 思い ます / 全く おかず に なら ない.
- Chênh lệch theo nhóm độ dài: nhóm 1: +11.9 đpt (1543 review, 8 có cụm); nhóm 2: +0.7 đpt (2571 review, 48 có cụm); nhóm 3: +6.5 đpt (2073 review, 295 có cụm).

**なかっ** · Logistic +2.355 / Bayes +0.1883. Tỷ lệ mức 2 trên test là 14.4% khi có cụm và 2.1% khi thiếu cụm (+12.3 điểm phần trăm). Có 19 review đúng mức chứa cụm từ 15 quán. TP/FP/FN/TN = 19/113/129/5926.
- Ngữ cảnh đã rút gọn: 多く 全部 食べ られ なかっ た / は カラシ しか ついて なかっ た が 何 も.
- Chênh lệch theo nhóm độ dài: nhóm 2: +22.2 đpt (2571 review, 30 có cụm); nhóm 3: +7.2 đpt (2073 review, 102 có cụm).

**のに** · Logistic +1.925 / Bayes +0.06373. Tỷ lệ mức 2 trên test là 14.0% khi có cụm và 2.2% khi thiếu cụm (+11.7 điểm phần trăm). Có 12 review đúng mức chứa cụm từ 9 quán. TP/FP/FN/TN = 12/74/136/5965.
- Ngữ cảnh đã rút gọn: 焼き を たのん だ のに 白玉 入り の 普通 / ずっと 待っ て た のに 受け取り まで に 時間.
- Chênh lệch theo nhóm độ dài: nhóm 2: +28.7 đpt (2571 review, 10 có cụm); nhóm 3: +7.2 đpt (2073 review, 76 có cụm).

**か** · Logistic +2.083. Tỷ lệ mức 2 trên test là 7.5% khi có cụm và 2.2% khi thiếu cụm (+5.3 điểm phần trăm). Có 16 review đúng mức chứa cụm từ 12 quán. TP/FP/FN/TN = 16/196/132/5843.
- Ngữ cảnh đã rút gọn: 使っ て ほしい の か 非常 に わかり にくかっ / 食え ない ので 写真 か テキスト で 内容 物.
- Chênh lệch theo nhóm độ dài: nhóm 1: -0.6 đpt (1543 review, 3 có cụm); nhóm 2: +4.2 đpt (2571 review, 18 có cụm); nhóm 3: +3.2 đpt (2073 review, 191 có cụm).

### Tiếng Nhật · rating 3

Kiểm định 17 ứng viên. Xác nhận 7 cụm.

| Hạng Holm | Cụm ứng viên | Model và trọng số | P-value thô | P-value Holm | OR | CI 95% | Quyết định |
|---:|---|---|---:|---:|---:|---|---|
| 34 | ない | Logistic +2.446 | 3.24e-15 | 7.49e-13 | 4 | [2.82; 5.67] | Xác nhận |
| 51 | なかっ た | Logistic +2.311 / Bayes +0.5848 | 5.97e-11 | 1.28e-08 | 5.13 | [3.12; 8.43] | Xác nhận |
| 52 | なかっ | Logistic +2.142 | 9.34e-11 | 1.99e-08 | 5.08 | [3.08; 8.37] | Xác nhận |
| 61 | 普通 | Logistic +3.007 / Bayes +0.8607 | 2.11e-08 | 4.3e-06 | 4.9 | [2.77; 8.64] | Xác nhận |
| 62 | 残念 | Logistic +2.683 | 3.45e-08 | 7e-06 | 5.29 | [2.89; 9.7] | Xác nhận |
| 68 | た | Logistic +2.672 | 8.6e-07 | 0.000169 | 2.04 | [1.52; 2.74] | Xác nhận |
| 78 | ん | Logistic +1.987 | 2.91e-05 | 0.00544 | 3 | [1.76; 5.14] | Xác nhận |
| 198 | まあ | Logistic +2.171 / Bayes +1.153 | — | — | 9.54 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 199 | まあ まあ | Bayes +1.276 | — | — | 10.5 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 200 | 少ない | Bayes +0.7447 | — | — | 5.96 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 201 | 残念 でし | Bayes +0.634 | — | — | 3.68 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 202 | 残念 でし た | Bayes +0.634 | — | — | 3.68 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 203 | 油 | Logistic +2.062 | — | — | 4.83 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 204 | 漏れ て い | Bayes +1.128 | — | — | 2.52 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 205 | 袋 | Bayes +0.7292 | — | — | 3.79 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 206 | 違い | Bayes +0.6921 | — | — | 1.96 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 207 | 違う | Logistic +2.029 | — | — | 2.96 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |

**ない** · Logistic +2.446. Tỷ lệ mức 3 trên test là 16.5% khi có cụm và 4.7% khi thiếu cụm (+11.8 điểm phần trăm). Có 58 review đúng mức chứa cụm từ 36 quán. TP/FP/FN/TN = 58/293/275/5561.
- Ngữ cảnh đã rút gọn: 量 は 多く ない です / やり取り が あり 良く ない.
- Chênh lệch theo nhóm độ dài: nhóm 1: +9.6 đpt (1543 review, 8 có cụm); nhóm 2: +21.9 đpt (2571 review, 48 có cụm); nhóm 3: +6.7 đpt (2073 review, 295 có cụm).

**なかっ た** · Logistic +2.311 / Bayes +0.5848. Tỷ lệ mức 3 trên test là 21.4% khi có cụm và 5.0% khi thiếu cụm (+16.3 điểm phần trăm). Có 28 review đúng mức chứa cụm từ 20 quán. TP/FP/FN/TN = 28/103/305/5751.
- Ngữ cảnh đã rút gọn: さ れ て い なかっ た ので 他 の 容器 / た もの で は なかっ た です.
- Chênh lệch theo nhóm độ dài: nhóm 2: +13.3 đpt (2571 review, 30 có cụm); nhóm 3: +13.9 đpt (2073 review, 101 có cụm).

**なかっ** · Logistic +2.142. Tỷ lệ mức 3 trên test là 21.2% khi có cụm và 5.0% khi thiếu cụm (+16.2 điểm phần trăm). Có 28 review đúng mức chứa cụm từ 20 quán. TP/FP/FN/TN = 28/104/305/5750.
- Ngữ cảnh đã rút gọn: さ れ て い なかっ た ので 他 の / た もの で は なかっ た です.
- Chênh lệch theo nhóm độ dài: nhóm 2: +13.3 đpt (2571 review, 30 có cụm); nhóm 3: +13.7 đpt (2073 review, 102 có cụm).

**普通** · Logistic +3.007 / Bayes +0.8607. Tỷ lệ mức 3 trên test là 21.2% khi có cụm và 5.2% khi thiếu cụm (+16.0 điểm phần trăm). Có 14 review đúng mức chứa cụm từ 12 quán. TP/FP/FN/TN = 14/52/319/5802.
- Ngữ cảnh đã rút gọn: 普通 盛り 大盛り 特 盛り / 普通 だっ た.
- Chênh lệch theo nhóm độ dài: nhóm 1: +37.2 đpt (1543 review, 5 có cụm); nhóm 2: +11.9 đpt (2571 review, 13 có cụm); nhóm 3: +11.6 đpt (2073 review, 48 có cụm).

**残念** · Logistic +2.683. Tỷ lệ mức 3 trên test là 22.0% khi có cụm và 5.0% khi thiếu cụm (+16.9 điểm phần trăm). Có 27 review đúng mức chứa cụm từ 17 quán. TP/FP/FN/TN = 27/96/306/5758.
- Ngữ cảnh đã rút gọn: なっ て い て 残念 でし た / だ な と 少し 残念 に 思っ て まし.
- Chênh lệch theo nhóm độ dài: nhóm 1: -2.9 đpt (1543 review, 2 có cụm); nhóm 2: +16.5 đpt (2571 review, 10 có cụm); nhóm 3: +13.8 đpt (2073 review, 111 có cụm).

**た** · Logistic +2.672. Tỷ lệ mức 3 trên test là 6.8% khi có cụm và 3.4% khi thiếu cụm (+3.3 điểm phần trăm). Có 244 review đúng mức chứa cụm từ 62 quán. TP/FP/FN/TN = 244/3354/89/2500.
- Ngữ cảnh đã rút gọn: 冷め て い まし た / 潰れ て い まし た.
- Chênh lệch theo nhóm độ dài: nhóm 1: +0.8 đpt (1543 review, 782 có cụm); nhóm 2: +0.9 đpt (2571 review, 1343 có cụm); nhóm 3: +5.9 đpt (2073 review, 1473 có cụm).

**ん** · Logistic +1.987. Tỷ lệ mức 3 trên test là 14.0% khi có cụm và 5.1% khi thiếu cụm (+8.8 điểm phần trăm). Có 25 review đúng mức chứa cụm từ 18 quán. TP/FP/FN/TN = 25/154/308/5700.
- Ngữ cảnh đã rút gọn: 歯 は 欠け ませ ん でし た / て 食べ られ ませ ん でし た.
- Chênh lệch theo nhóm độ dài: nhóm 1: -2.9 đpt (1543 review, 3 có cụm); nhóm 2: +17.6 đpt (2571 review, 19 có cụm); nhóm 3: +4.2 đpt (2073 review, 157 có cụm).

### Tiếng Nhật · rating 4

Kiểm định 16 ứng viên. Xác nhận 7 cụm.

| Hạng Holm | Cụm ứng viên | Model và trọng số | P-value thô | P-value Holm | OR | CI 95% | Quyết định |
|---:|---|---|---:|---:|---:|---|---|
| 25 | 少し | Logistic +2.979 / Bayes +0.7317 | 1.02e-23 | 2.45e-21 | 6.73 | [4.63; 9.79] | Xác nhận |
| 39 | もう少し | Logistic +2.233 / Bayes +0.7407 | 1.07e-12 | 2.42e-10 | 7.38 | [4.23; 12.9] | Xác nhận |
| 44 | か | Logistic +1.904 | 4.65e-12 | 1.03e-09 | 3.6 | [2.49; 5.19] | Xác nhận |
| 45 | 残念 | Logistic +2.122 | 7.77e-12 | 1.71e-09 | 4.88 | [3.08; 7.74] | Xác nhận |
| 72 | か な | Bayes +0.8244 | 1.54e-06 | 0.000297 | 4.61 | [2.43; 8.77] | Xác nhận |
| 75 | まあ | Logistic +2.583 / Bayes +1.054 | 2.5e-06 | 0.000475 | 7.08 | [3.05; 16.4] | Xác nhận |
| 83 | ちょっと | Logistic +2.576 / Bayes +0.7277 | 4.27e-05 | 0.00777 | 3.43 | [1.85; 6.34] | Xác nhận |
| 89 | 感じ | Logistic +2.251 | 0.000456 | 0.0802 | 2.86 | [1.54; 5.33] | Không đạt · p Holm ≥ 0.05 |
| 97 | 普通 | Logistic +2.312 | 0.00221 | 0.371 | 2.78 | [1.37; 5.61] | Không đạt · p Holm ≥ 0.05 |
| 208 | い なかっ | Bayes +0.8544 | — | — | 4.82 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 209 | い なかっ た | Bayes +0.8831 | — | — | 5.19 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 210 | ください | Logistic +1.787 | — | — | 1.19 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 211 | まあ まあ | Bayes +1.079 | — | — | 8.21 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 212 | ソース | Logistic +1.827 | — | — | 1.7 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 213 | 味 は 美味しい | Bayes +1.141 | — | — | 2.58 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |
| 214 | 気 が し | Bayes +0.7332 | — | — | 4.31 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |

**少し** · Logistic +2.979 / Bayes +0.7317. Tỷ lệ mức 4 trên test là 36.1% khi có cụm và 7.7% khi thiếu cụm (+28.4 điểm phần trăm). Có 39 review đúng mức chứa cụm từ 27 quán. TP/FP/FN/TN = 39/69/471/5608.
- Ngữ cảnh đã rút gọn: 今日 の は 少し いつも と 違う 味 / 少し 少なめ の ヨーグルトシェイク に.
- Chênh lệch theo nhóm độ dài: nhóm 2: +24.8 đpt (2571 review, 16 có cụm); nhóm 3: +26.1 đpt (2073 review, 92 có cụm).

**もう少し** · Logistic +2.233 / Bayes +0.7407. Tỷ lệ mức 4 trên test là 39.1% khi có cụm và 8.0% khi thiếu cụm (+31.1 điểm phần trăm). Có 18 review đúng mức chứa cụm từ 15 quán. TP/FP/FN/TN = 18/28/492/5649.
- Ngữ cảnh đã rút gọn: 肉 の 量 が もう少し 多い と より 良い / シャリ が もう少し 大きい 方 が 良かっ.
- Chênh lệch theo nhóm độ dài: nhóm 2: +22.1 đpt (2571 review, 7 có cụm); nhóm 3: +29.6 đpt (2073 review, 39 có cụm).

**か** · Logistic +1.904. Tỷ lệ mức 4 trên test là 23.1% khi có cụm và 7.7% khi thiếu cụm (+15.4 điểm phần trăm). Có 49 review đúng mức chứa cụm từ 29 quán. TP/FP/FN/TN = 49/163/461/5514.
- Ngữ cảnh đã rút gọn: 野菜 から か 麺 を 頼ん だ / が 飲ん だ の か と 心配 に なり.
- Chênh lệch theo nhóm độ dài: nhóm 1: +60.8 đpt (1543 review, 3 có cụm); nhóm 2: +10.2 đpt (2571 review, 18 có cụm); nhóm 3: +12.1 đpt (2073 review, 191 có cụm).

**残念** · Logistic +2.122. Tỷ lệ mức 4 trên test là 29.3% khi có cụm và 7.8% khi thiếu cụm (+21.5 điểm phần trăm). Có 36 review đúng mức chứa cụm từ 25 quán. TP/FP/FN/TN = 36/87/474/5590.
- Ngữ cảnh đã rút gọn: 残念 でし た / 変わっ て しまっ て 残念 でし た ー.
- Chênh lệch theo nhóm độ dài: nhóm 1: +44.1 đpt (1543 review, 2 có cụm); nhóm 2: +23.5 đpt (2571 review, 10 có cụm); nhóm 3: +17.8 đpt (2073 review, 111 có cụm).

**か な** · Bayes +0.8244. Tỷ lệ mức 4 trên test là 28.9% khi có cụm và 8.1% khi thiếu cụm (+20.8 điểm phần trăm). Có 13 review đúng mức chứa cụm từ 10 quán. TP/FP/FN/TN = 13/32/497/5645.
- Ngữ cảnh đã rút gọn: けど 具 が 少ない か な / が 少し 苦かっ た か な.
- Chênh lệch theo nhóm độ dài: nhóm 1: +44.1 đpt (1543 review, 2 có cụm); nhóm 2: +22.1 đpt (2571 review, 7 có cụm); nhóm 3: +16.0 đpt (2073 review, 36 có cụm).

**まあ** · Logistic +2.583 / Bayes +1.054. Tỷ lệ mức 4 trên test là 38.5% khi có cụm và 8.1% khi thiếu cụm (+30.3 điểm phần trăm). Có 10 review đúng mức chứa cụm từ 9 quán. TP/FP/FN/TN = 10/16/500/5661.
- Ngữ cảnh đã rút gọn: まあ まあ / 海 塩 チーズ は まあ まあ おいしい です が.
- Chênh lệch theo nhóm độ dài: nhóm 1: +31.7 đpt (1543 review, 8 có cụm); nhóm 2: +26.8 đpt (2571 review, 6 có cụm); nhóm 3: +29.8 đpt (2073 review, 12 có cụm).

**ちょっと** · Logistic +2.576 / Bayes +0.7277. Tỷ lệ mức 4 trên test là 23.2% khi có cụm và 8.1% khi thiếu cụm (+15.1 điểm phần trăm). Có 13 review đúng mức chứa cụm từ 12 quán. TP/FP/FN/TN = 13/43/497/5634.
- Ngữ cảnh đã rút gọn: 身 の 部分 が ちょっと あまりに 寂し すぎ まし / 唐 揚げ もう ちょっと.
- Chênh lệch theo nhóm độ dài: nhóm 1: +44.1 đpt (1543 review, 2 có cụm); nhóm 2: +26.8 đpt (2571 review, 6 có cụm); nhóm 3: +9.0 đpt (2073 review, 48 có cụm).

### Tiếng Nhật · rating 5

Kiểm định 19 ứng viên. Xác nhận 2 cụm.

| Hạng Holm | Cụm ứng viên | Model và trọng số | P-value thô | P-value Holm | OR | CI 95% | Quyết định |
|---:|---|---|---:|---:|---:|---|---|
| 21 | 美味しかっ た | Logistic +3.223 | 4.7e-28 | 1.15e-25 | 2.86 | [2.37; 3.45] | Xác nhận |
| 57 | いつも | Logistic +3.061 | 4.37e-10 | 9.08e-08 | 3.94 | [2.54; 6.11] | Xác nhận |
| 95 | 美味し | Logistic +2.616 | 0.00186 | 0.317 | 2.27 | [1.3; 3.95] | Không đạt · p Holm ≥ 0.05 |
| 104 | 美味い | Logistic +3.16 | 0.0163 | 1 | 3.88 | [1.12; 13.4] | Không đạt · p Holm ≥ 0.05 |
| 109 | 大 | Logistic +2.668 | 0.0299 | 1 | 2.92 | [0.957; 8.92] | Không đạt · CI chứa 1 hoặc thấp hơn; p Holm ≥ 0.05 |
| 113 | おすすめ | Logistic +2.418 | 0.0534 | 1 | 2.65 | [0.811; 8.68] | Không đạt · CI chứa 1 hoặc thấp hơn; p Holm ≥ 0.05 |
| 119 | 嬉しい | Logistic +2.802 | 0.159 | 1 | 1.36 | [0.741; 2.51] | Không đạt · OR < 1.5; CI chứa 1 hoặc thấp hơn; p Holm ≥ 0.05 |
| 121 | とっても 美味しかっ | Bayes +3.513 | 0.197 | 1 | 1.81 | [0.462; 7.12] | Không đạt · CI chứa 1 hoặc thấp hơn; p Holm ≥ 0.05 |
| 122 | とっても 美味しかっ た | Bayes +3.513 | 0.197 | 1 | 1.81 | [0.462; 7.12] | Không đạt · CI chứa 1 hoặc thấp hơn; p Holm ≥ 0.05 |
| 125 | ここ | Logistic +2.796 | 0.286 | 1 | 1.26 | [0.561; 2.84] | Không đạt · OR < 1.5; CI chứa 1 hoặc thấp hơn; p Holm ≥ 0.05 |
| 215 | いつも おいしい | Bayes +3.908 | — | — | — | — | Chưa đủ bằng chứng · Ô đếm bằng 0 |
| 216 | うま | Logistic +2.354 / Bayes +3.474 | — | — | — | — | Chưa đủ bằng chứng · Ô đếm bằng 0 |
| 217 | バランス 良く | Bayes +3.384 | — | — | — | — | Chưa đủ bằng chứng · Ô đếm bằng 0 |
| 218 | 今日 も 美味しかっ | Bayes +3.491 | — | — | — | — | Chưa đủ bằng chứng · Ô đếm bằng 0 |
| 219 | 今日 も 美味しく | Bayes +4.956 | — | — | — | — | Chưa đủ bằng chứng · Ô đếm bằng 0 |
| 220 | 安く て 美味しい | Bayes +3.406 | — | — | — | — | Chưa đủ bằng chứng · Ô đếm bằng 0 |
| 221 | 最高 | Logistic +4.68 | — | — | — | — | Chưa đủ bằng chứng · Ô đếm bằng 0 |
| 222 | 最高 でし | Bayes +3.554 | — | — | — | — | Chưa đủ bằng chứng · Ô đếm bằng 0 |
| 223 | 最高 でし た | Bayes +3.554 | — | — | — | — | Chưa đủ bằng chứng · Ô đếm bằng 0 |

**美味しかっ た** · Logistic +3.223. Tỷ lệ mức 5 trên test là 91.0% khi có cụm và 78.0% khi thiếu cụm (+13.0 điểm phần trăm). Có 1523 review đúng mức chứa cụm từ 104 quán. TP/FP/FN/TN = 1523/150/3522/992.
- Ngữ cảnh đã rút gọn: 美味しかっ た です / 具 沢山 で 美味しかっ た です.
- Chênh lệch theo nhóm độ dài: nhóm 1: +6.3 đpt (1543 review, 518 có cụm); nhóm 2: +8.7 đpt (2571 review, 744 có cụm); nhóm 3: +18.2 đpt (2073 review, 411 có cụm).

**いつも** · Logistic +3.061. Tỷ lệ mức 5 trên test là 94.1% khi có cụm và 80.2% khi thiếu cụm (+13.9 điểm phần trăm). Có 559 review đúng mức chứa cụm từ 58 quán. TP/FP/FN/TN = 559/35/4486/1107.
- Ngữ cảnh đã rút gọn: いつも お世話 に なっ て / いつも 最高 の ごはん です.
- Chênh lệch theo nhóm độ dài: nhóm 1: +10.2 đpt (1543 review, 59 có cụm); nhóm 2: +13.5 đpt (2571 review, 337 có cụm); nhóm 3: +17.9 đpt (2073 review, 198 có cụm).

### Tiếng Pháp · rating 5

Kiểm định 1 ứng viên. Xác nhận 0 cụm.

| Hạng Holm | Cụm ứng viên | Model và trọng số | P-value thô | P-value Holm | OR | CI 95% | Quyết định |
|---:|---|---|---:|---:|---:|---|---|
| 180 | excellent | Logistic +1.324 / Bayes +1.263 | — | — | 0.75 | — | Chưa đủ bằng chứng · Thiếu review hoặc nhóm quán hỗ trợ |

## 4. Kết luận

Các kết luận dưới đây mô tả liên hệ quan sát giữa cụm từ và rating trong review của dự án. Cơ cấu nền tảng, độ dài review, thời gian và đặc điểm quán có thể ảnh hưởng đến liên hệ.

| Ngôn ngữ | Mức | Cụm xác nhận / ứng viên | Từ khóa xác nhận hoặc lý do |
|---|---:|---:|---|
| vi | 0 | 0/2 | Chưa có cụm được xác nhận |
| vi | 1 | 12/20 | tệ, làm ăn, dở, lừa, chửi, ko, kém, lừa đảo, chém, hôi, thất đức, tẩy chay |
| vi | 2 | 7/20 | ko, chán, nhạt, mong, không ngon, ko ngon, cộc lốc |
| vi | 3 | 13/20 | không ngon, bình thường, mùi vị tuyệt, cho biết, vị tuyệt vời, cho lắm, chật, vị tuyệt, tuyệt vời mềm, vời mềm, tuyệt vời thơm, vời thơm, mùo |
| vi | 4 | 10/20 | lắm, cũng, khá, giá, này, đông, thích, khá ngon, bên này, giá hơi đắt |
| vi | 5 | 6/20 | xỉu, ngon xỉu, gói tốt, đóng gói tốt, tiền sạch, ngonn |
| en | 0 | 0/0 | Thiếu review hoặc quán lớp đích trên train |
| en | 1 | 0/15 | Chưa có cụm được xác nhận |
| en | 2 | 1/11 | not fresh |
| en | 3 | 1/15 | not as |
| en | 4 | 1/17 | overall |
| en | 5 | 4/19 | read more, read, always, best |
| ja | 0 | 0/0 | Thiếu review hoặc quán lớp đích trên train |
| ja | 1 | 9/18 | 時間, ない, れ, 最悪, し, 頼ん, れ た, なかっ た, なかっ |
| ja | 2 | 6/14 | 残念, なかっ た, ない, なかっ, のに, か |
| ja | 3 | 7/17 | ない, なかっ た, なかっ, 普通, 残念, た, ん |
| ja | 4 | 7/16 | 少し, もう少し, か, 残念, か な, まあ, ちょっと |
| ja | 5 | 2/19 | 美味しかっ た, いつも |
| fr | 0 | 0/0 | Thiếu review hoặc quán lớp đích trên train |
| fr | 1 | 0/0 | Thiếu review hoặc quán lớp đích trên train |
| fr | 2 | 0/0 | Thiếu review hoặc quán lớp đích trên train |
| fr | 3 | 0/0 | Thiếu review hoặc quán lớp đích trên train |
| fr | 4 | 0/0 | Thiếu review hoặc quán lớp đích trên train |
| fr | 5 | 0/1 | Chưa có cụm được xác nhận |

## 5. Tệp đối chiếu

- rating_coverage.csv và split_manifest.csv lưu độ phủ và cách chia.
- locked_candidates.csv lưu ứng viên và trọng số trước kiểm định.
- keyword_results.csv lưu đủ bảng 2×2, các metric của quy tắc dùng một cụm, hai tỷ lệ, Wald z, p-value, OR, CI và lý do quyết định.
- test_metrics.csv lưu hiệu năng hai model. keywords_by_language_rating.csv lưu tóm tắt đủ 24 tổ hợp.
