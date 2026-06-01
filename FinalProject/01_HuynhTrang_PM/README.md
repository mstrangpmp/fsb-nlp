# 👑 01 - Lê Huỳnh Trang (PM / Data Curator & Aggregator)

## 📌 Vai trò & Nhiệm vụ cốt lõi
- Chuẩn bị dữ liệu đầu vào sạch, ban hành Definition of Done (DoD).
- Thực hiện tiền xử lý dữ liệu thô (loại bỏ số nhà, SĐT đầu chủ) để làm sạch tại nguồn.
- Gán `SystemID` làm mã định danh duy nhất thống nhất toàn bộ dataset.
- Chia dữ liệu Train (51 tin) / Val (8 tin) / Test (9 tin) và bàn giao cho nhóm.
- Thu nhận các file bàn giao từ 5 thành viên, chạy script Python `aggregate_results.py` để chấm điểm ROUGE-L và Specs Accuracy.
- Ghép slide và viết báo cáo đề án tổng hợp để hoàn thiện tài liệu thuyết trình.

## 📦 Sản phẩm bàn giao (Deliverables)
- `ground_truth_test.json` - File nhãn chuẩn dùng để đánh giá.
- `aggregate_results.py` - Kịch bản tổng hợp hiệu năng tự động.
- `summary_leaderboard_report.csv` - Bảng xếp hạng hiệu năng thực tế của cả 5 mô hình.
