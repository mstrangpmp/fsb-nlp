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
