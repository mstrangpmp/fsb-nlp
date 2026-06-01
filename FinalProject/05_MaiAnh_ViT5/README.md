# 🚀 05 - Đinh Thị Mai Anh (ViT5 Specialist)

## 📌 Vai trò & Nhiệm vụ cốt lõi
- Xây dựng mã nguồn PyTorch/Hugging Face để fine-tune mô hình Seq2Seq **ViT5 (vietnamese-t5-base)** trên môi trường Google Colab (sử dụng GPU T4).
- Theo dõi biểu đồ Loss huấn luyện, sử dụng tập Validation để chống Overfitting.
- Áp dụng kỹ thuật giải mã **Beam Search** khi inference tập Test để sinh câu mượt mà, đầy đủ thông số nhất.

## 📦 Sản phẩm cần bàn giao (DoD Deliverables)
Hãy đặt các file sau vào thư mục này khi hoàn thành:
1. `MaiAnh_ViT5_predictions.json` - File chứa kết quả chuẩn hóa (tuân thủ định dạng SystemID).
2. `MaiAnh_ViT5_performance.json` - File ghi nhận hiệu năng (độ trễ GPU cục bộ).
3. `MaiAnh_ViT5_report.md` - Báo cáo chi tiết: Siêu tham số (Hyperparameters), Loss Curve, và phân tích 3 lỗi định tính (như lặp từ hay đứt câu).
4. Link Google Colab fine-tuning và file Notebook `.ipynb` thực thi.
