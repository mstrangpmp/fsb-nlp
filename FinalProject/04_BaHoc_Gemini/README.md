# 🌟 04 - Nguyễn Bá Học (Gemini Specialist)

## 📌 Vai trò & Nhiệm vụ cốt lõi
- Xây dựng cấu trúc **Prompt Few-shot** hiệu năng cao tương thích với API Gemini Flash.
- Viết kịch bản Python gọi API `gemini-1.5-flash` để chuẩn hóa các tin đăng bất động sản trong tập Test.
- Đo lường và tối ưu hóa thời gian xử lý (Latency) và tính toán chi phí vận hành thực tế.

## 📦 Sản phẩm cần bàn giao (DoD Deliverables)
Hãy đặt các file sau vào thư mục này khi hoàn thành:
1. `Hoc_Gemini_predictions.json` - File chứa kết quả chuẩn hóa (tuân thủ định dạng SystemID).
2. `Hoc_Gemini_performance.json` - File ghi nhận tốc độ và tài nguyên xử lý (Latency/Cost).
3. `Hoc_Gemini_report.md` - Báo cáo phân tích định tính 3 lỗi điển hình và cấu trúc prompt tối ưu.
4. Source code Python / Notebook gọi API.

## 🔗 Tích hợp hệ thống và Chạy lại (System Integration & Re-running)

- **Vị trí tệp bàn giao thực tế để hiển thị trên App**:
  - predictions JSON: `FinalProject/04_BaHoc_Gemini/Hoc_Gemini_predictions.json`
  - performance JSON: `FinalProject/04_BaHoc_Gemini/Hoc_Gemini_performance.json`
- **Cách cập nhật kết quả dự đoán của mô hình**:
  - Khi chạy lại API Gemini và có kết quả dự đoán mới, hãy lưu đè kết quả định dạng JSON vào 2 tệp trên.
  - **Với Flask App**: Flask app sẽ tự động nạp dữ liệu mới từ các tệp trên và tính lại các chỉ số đối chiếu ngay lập tức.
  - **Với Trang tĩnh (`app/index.html`)**: Chạy generator script để biên dịch dữ liệu mới nhúng vào trang tĩnh:
    ```bash
    cd FinalProject/app
    python generate_static_index.py
    ```

