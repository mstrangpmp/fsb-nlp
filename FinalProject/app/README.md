# Ứng Trực Quan & Đánh Giá Bất Động Sản NLP (Nhóm 2 - FSB)

Đây là ứng dụng Web Showcase phục vụ cho Đề án tốt nghiệp NLP (Nhóm 2 - FSB). Ứng dụng được thiết kế nhằm mục đích so sánh trực quan kết quả tóm tắt và trích xuất thông số của 5 mô hình (Baseline TextRank, GPT-4o mini, Gemini 1.5 Flash, ViT5, PhoBERT) trên tập 9 căn nhà kiểm thử cốt lõi.

Đồng thời, ứng dụng cung cấp giao diện cho chuyên gia biên tập nhãn Ground Truth động, tự động tính điểm từ vựng (ROUGE-L) & thông số (Specs Accuracy) và ghi nhận xếp hạng Winner trực tiếp để xây dựng bảng xếp hạng (Live Leaderboard).

## 🌟 Các Tính Năng Chính
1. **Trực quan hóa 5 mô hình**: Hiển thị song song tiêu đề, mô tả và bảng thông số trích xuất của cả 5 mô hình trên cùng một giao diện.
2. **Hiển thị hiệu năng thực tế (Real Performance)**: Đọc trực tiếp độ trễ (latency) và chi phí thực tế của riêng căn đang được chọn từ dữ liệu hiệu năng của nhóm.
3. **Biên tập Ground Truth trực quan**: Cho phép chuyên gia chỉnh sửa mô tả chuẩn và 9 trường thông số kỹ thuật. Hệ thống sẽ tự động gọi backend tính lại ROUGE-L và Specs Accuracy theo thời gian thực.
4. **Specs Highlight**: So sánh tự động và tô màu xanh lá cây (nếu khớp đúng Ground Truth) hoặc màu đỏ (nếu sai lệch/thiếu) đối với từng thông số của mô hình.
5. **Xếp hạng Winner (Anh Khang chấm)**: Chuyên gia trực tiếp chọn Winner 1, 2, 3 cho mỗi căn. Điểm số được tích lũy theo tỷ trọng đã được phê duyệt để tự động cập nhật Bảng xếp hạng trực tuyến.

## 📁 Cấu Trúc Thư Mục Ứng Dụng
```text
FinalProject/app/
├── app.py                     # Source code Backend Flask chính
├── .gitignore                 # Cấu hình bỏ qua các file thừa của Python
├── README.md                  # Hướng dẫn sử dụng dự án (Tiếng Việt)
├── user_ground_truth.json     # Dữ liệu Ground Truth của người dùng (tự động tạo)
├── expert_reviews.json        # Dữ liệu đánh giá xếp hạng của chuyên gia (tự động tạo)
└── templates/
    └── index.html             # Giao diện Frontend Glassmorphism tối màu (HTML/CSS/JS)
```

## 🚀 Hướng Dẫn Cài Đặt & Chạy Ứng Dụng

### 1. Cài đặt thư viện yêu cầu
Ứng dụng chạy trên Python 3.8+ và chỉ yêu cầu 2 thư viện chính để vận hành:
```bash
pip install flask rouge-score
```

### 2. Khởi chạy máy chủ nội bộ
Chạy lệnh sau tại thư mục chứa file `app.py`:
```bash
python app.py
```
Máy chủ sẽ được khởi chạy tại địa chỉ: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

### 3. Đưa lên Git Repository
Anh có thể khởi tạo Git tại thư mục này hoặc thư mục gốc `FinalProject` và push lên GitHub/GitLab:
```bash
git init
git add .
git commit -m "Initialize NLP Showcase Web Application"
git remote add origin <link_repo_cua_anh>
git branch -M main
git push -u origin main
```
*(File `.gitignore` đã được cấu hình sẵn để tránh push các file cache `__pycache__` lên repo).*

## 🔄 Cập Nhật Hệ Thống Gần Đây (System Updates)

Hệ thống ứng dụng đánh giá (`app/`) đã được tối ưu hóa và cập nhật các tính năng quan trọng sau:
1. **Đồng bộ hóa Chuẩn hóa Tiếng Việt (Unicode Tone Normalization)**:
   - Tích hợp hàm `normalize_vietnamese` (ở backend Python) và `normalizeVietnamese` (ở frontend JS) để tự động quy đổi và thống nhất các nguyên âm ghép có cách đặt dấu thanh khác nhau (ví dụ: `Hòa` kiểu mới và `Hoà` kiểu cũ đều được chuẩn hóa về cùng một chuỗi).
   - Khắc phục triệt để lỗi so khớp thông số trích xuất (`Specs Accuracy`), giúp giao diện chuyển sang **màu xanh lá cây** chính xác khi người dùng chỉnh sửa specs trùng khớp ngữ nghĩa.
2. **Biên tập Tiêu đề chuẩn nhãn**:
   - Bổ sung trường nhập liệu `Tiêu đề chuẩn nhãn` (Title) trong Ground Truth Editor và đồng bộ lưu trữ/tính điểm.
3. **Sửa lỗi Layout Overlap & Đè nút**:
   - Chuyển cấu trúc Header từ tuyệt đối sang Flexbox responsive, sửa hoàn toàn lỗi các nút chức năng bị đè lên tiêu đề trang trên các màn hình có độ phân giải nhỏ.
   - Thêm nút liên kết trực tiếp để quay trở lại trang Đề xuất Đề án nhóm (`📄 Đề Xuất Đề Án`).
4. **Định dạng Chi phí Gemini**:
   - Điều chỉnh hiển thị chi phí sử dụng mô hình Gemini Flash từ số thực (`~15.00đ`) thành số nguyên (`~15đ`) để tối ưu giao diện trực quan và tránh gây nhầm lẫn hiển thị cho người dùng.
5. **Generator trang tĩnh (`generate_static_index.py`)**:
   - Đồng bộ hóa toàn bộ các cải tiến giao diện, chức năng và chuẩn hóa tiếng Việt vào generator tĩnh để sinh lại tệp tĩnh `app/index.html` tự động mà không gặp lỗi giật lùi giao diện.

