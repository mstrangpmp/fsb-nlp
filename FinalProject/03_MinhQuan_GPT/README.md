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
