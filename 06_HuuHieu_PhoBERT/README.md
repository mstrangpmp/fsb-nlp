# ⚡ 06 - Nguyễn Hữu Hiệu (PhoBERT Specialist)

## 📌 Vai trò & Nhiệm vụ cốt lõi
- Xây dựng mã nguồn fine-tune mô hình Seq2Seq dựa trên **PhoBERT (vinai/phobert-base)** trên Google Colab T4.
- Thiết lập pipeline mã hóa/giải mã (Encoder-Decoder) tối ưu cho cấu trúc ngôn ngữ tiếng Việt của PhoBERT.
- Thực hiện dự đoán trên tập Test và đo đạc thời gian inference thực tế trên GPU.

## 📦 Sản phẩm cần bàn giao (DoD Deliverables)
Hãy đặt các file sau vào thư mục này khi hoàn thành:
1. `HuuHieu_PhoBERT_predictions.json` - File chứa kết quả chuẩn hóa (tuân thủ định dạng SystemID). (Lưu ý: Tên file dùng tiếp đầu ngữ `HuuHieu_PhoBERT` để đồng bộ).
2. `HuuHieu_PhoBERT_performance.json` - File ghi nhận hiệu năng trễ xử lý thực tế trên GPU.
3. `HuuHieu_PhoBERT_report.md` - Báo cáo phân tích siêu tham số huấn luyện, Loss Curve và phân tích 3 lỗi định tính (như tách sai từ ghép tiếng Việt).
4. Link Google Colab fine-tuning và file Notebook `.ipynb` thực thi.
