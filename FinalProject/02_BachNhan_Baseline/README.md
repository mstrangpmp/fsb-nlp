# 📊 02 - Nguyễn Huỳnh Bách Nhân (Baseline Specialist)

## 📌 Vai trò & Nhiệm vụ cốt lõi
- Xây dựng thuật toán **TextRank** (hoặc LexRank) cổ điển để trích xuất câu tóm tắt làm mốc so sánh (Baseline).
- Viết kịch bản Python sử dụng thư viện tiếng Việt như `underthesea` hoặc `sumy` để xử lý văn bản thô.
- Dự đoán kết quả chuẩn hóa cho 9 căn trong tập Test.

## 📦 Sản phẩm cần bàn giao (DoD Deliverables)
Hãy đặt các file sau vào thư mục này khi hoàn thành:
1. `Nhan_Baseline_predictions.json` - File chứa kết quả chuẩn hóa (tuân thủ định dạng SystemID).
2. `Nhan_Baseline_performance.json` - File ghi nhận tốc độ và tài nguyên xử lý (Latency/Cost).
3. `Nhan_Baseline_report.md` - Báo cáo phân tích định tính ít nhất 3 lỗi điển hình của thuật toán.
4. Source code Python / Notebook huấn luyện và inference.

## 🔗 Tích hợp hệ thống và Chạy lại (System Integration & Re-running)

- **Vị trí tệp bàn giao thực tế để hiển thị trên App**:
  - predictions JSON: `FinalProject/02_BachNhan_Baseline/TextRank_TFIDF/Nhan_Baseline_predictions.json`
  - performance JSON: `FinalProject/02_BachNhan_Baseline/TextRank_TFIDF/Nhan_Baseline_performance.json`
- **Cách cập nhật kết quả dự đoán của mô hình**:
  - Khi chạy lại mô hình TextRank/TF-IDF và có kết quả dự đoán mới, hãy lưu đè kết quả định dạng JSON vào 2 tệp trên.
  - **Với Flask App**: Flask app sẽ tự động nạp dữ liệu mới từ các tệp trên và tính lại các chỉ số đối chiếu ngay lập tức.
  - **Với Trang tĩnh (`app/index.html`)**: Chạy generator script để biên dịch dữ liệu mới nhúng vào trang tĩnh:
    ```bash
    cd FinalProject/app
    python generate_static_index.py
    ```

