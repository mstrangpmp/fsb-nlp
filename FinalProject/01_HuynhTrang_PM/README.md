# 👑 01 - Lê Huỳnh Trang (PM / Data Curator & Aggregator)

## 📌 Vai trò & Nhiệm vụ cốt lõi
- Chuẩn bị dữ liệu đầu vào sạch, ban hành Definition of Done (DoD).
- Thực hiện tiền xử lý dữ liệu thô (loại bỏ số nhà, SĐT đầu chủ) để làm sạch tại nguồn.
- Gán `SystemID` làm mã định danh duy nhất thống nhất toàn bộ dataset.
- Chia dữ liệu Train (51 tin) / Val (8 tin) / Test (9 tin) và bàn giao cho nhóm.
- Thu nhận các file bàn giao từ 5 thành viên, chạy script Python `aggregate_results.py` để chấm điểm ROUGE-L và Specs Accuracy.
- Ghép slide và viết báo cáo đề án tổng hợp để hoàn thiện tài liệu thuyết trình.

## 📦 Sản phẩm bàn giao (Deliverables)
- **Các tập dữ liệu đầu vào bàn giao cho nhóm (Train 51 / Val 8 / Test 9):**
  - `train_dataset.json` – Dữ liệu 51 tin đăng dùng để huấn luyện mô hình (chứa đầy đủ thông tin chuẩn hóa và nhãn specs).
  - `val_dataset.json` – Dữ liệu 8 tin đăng dùng để đánh giá trong quá trình huấn luyện mô hình.
  - `test_dataset.json` – Dữ liệu 9 tin đăng thô dùng để chạy thử nghiệm thu sản phẩm của nhóm (đã được ẩn nhãn để đảm bảo chấm điểm khách quan).
- **Dữ liệu đánh giá & Script tổng hợp:**
  - `ground_truth_test.json` – File nhãn chuẩn thật của 9 căn test dùng để đối chiếu hiệu năng (chỉ do Trang nắm giữ).
  - `aggregate_results.py` – Kịch bản Python chấm điểm ROUGE-L và Specs Accuracy tự động.
  - `summary_leaderboard_report.csv` – Bảng xếp hạng hiệu năng tổng hợp của cả 5 mô hình sau khi chạy đánh giá.

## 🔗 Tích hợp hệ thống và Chạy lại (System Integration & Re-running)

- **Vị trí tập dữ liệu thô kiểm thử**:
  - `FinalProject/01_HuynhTrang_PM/test_dataset.json` (chứa 9 tin kiểm thử cốt lõi đăng ký qua trường `id` / `ID`).
- **Cách cập nhật dữ liệu đầu vào**:
  - Nếu có sự thay đổi về nội dung tin đăng thô đầu vào hoặc danh sách 9 căn nhà mẫu trong tập kiểm thử, chỉ cần sửa đổi nội dung tệp `test_dataset.json` này.
  - **Với Flask App**: Flask app sẽ tự động nạp lại dữ liệu tin đăng thô mới nhất từ tệp này qua API `/get_test_samples` và `/get_sample_data`.
  - **Với Trang tĩnh (`app/index.html`)**: Chạy generator script để biên dịch dữ liệu mới từ tệp này nhúng vào trang tĩnh:
    ```bash
    cd FinalProject/app
    python generate_static_index.py
    ```

