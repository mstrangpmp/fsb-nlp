# 🤖 03 - Dư Trọng Minh Quân (GPT Specialist)

## 📌 Vai trò & Nhiệm vụ cốt lõi
- Nghiên cứu và tối ưu cấu trúc **Prompt Few-shot** (kèm 3 ví dụ mẫu) phù hợp nhất với dữ liệu BDS Khang Ngô.
- Viết mã nguồn Python gọi API `gpt-4o-mini` để sinh kết quả chuẩn hóa tin đăng cho tập Test.
- Ghi nhận thời gian phản hồi (Latency) và thống kê chi phí API thực tế dựa trên số lượng Token sử dụng.

## 📦 Sản phẩm cần bàn giao (DoD Deliverables)
Hãy đặt các file sau vào thư mục này khi hoàn thành:
1. `Quan_GPT_predictions.json` - File chứa kết quả chuẩn hóa (tuân thủ định dạng SystemID).
2. `Quan_GPT_performance.json` - File ghi nhận tốc độ và tài nguyên xử lý (Latency/Cost).
3. `Quan_GPT_report.md` - Báo cáo phân tích định tính 3 lỗi ảo giác điển hình và prompt mẫu đã sử dụng.
4. Source code Python / Notebook gọi API.

## 🔗 Tích hợp hệ thống và Chạy lại (System Integration & Re-running)

- **Vị trí tệp bàn giao thực tế để hiển thị trên App**:
  - predictions JSON: `FinalProject/03_MinhQuan_GPT/predictions.json` (được lưu theo định dạng cấu trúc SystemID).
  - performance JSON: `FinalProject/03_MinhQuan_GPT/performance.json` (ghi nhận thời gian phản hồi và ước tính chi phí USD).
- **Cách cập nhật kết quả dự đoán của mô hình**:
  - Khi gọi lại API GPT-4o mini và sinh kết quả mới, hãy lưu đè kết quả định dạng JSON vào 2 tệp trên.
  - **Với Flask App**: Flask app sẽ tự động nạp dữ liệu mới từ các tệp trên và tính lại các chỉ số đối chiếu ngay lập tức.
  - **Với Trang tĩnh (`app/index.html`)**: Chạy generator script để biên dịch dữ liệu mới nhúng vào trang tĩnh:
    ```bash
    cd FinalProject/app
    python generate_static_index.py
    ```

