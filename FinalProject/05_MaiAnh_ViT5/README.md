# 🚀 Hướng Dẫn Chạy Fine-tune ViT5 — Đinh Thị Mai Anh

## 📋 Tổng quan
- **Model:** `VietAI/vit5-base` (220M params, Seq2Seq T5 tiếng Việt)  
- **Task:** Chuẩn hóa & rút gọn tin đăng BĐS (ẩn thông tin nhạy cảm)
- **Môi trường:** Google Colab + GPU T4 (miễn phí)
- **File code:** `MaiAnh_ViT5_Finetune.py`

---

## 📂 Cấu trúc thư mục (sau khi hoàn thành)

```
05_MaiAnh_ViT5/
├── MaiAnh_ViT5_Finetune.py         ← Code fine-tuning (file này)
├── MaiAnh_ViT5_predictions.json    ← OUTPUT: Kết quả 9 căn Test
├── MaiAnh_ViT5_performance.json    ← OUTPUT: Latency & metrics
├── MaiAnh_ViT5_report.md           ← OUTPUT: Báo cáo chi tiết
├── loss_curve.png                   ← OUTPUT: Biểu đồ loss
└── README.md                        ← File này
```

---

## 🔧 Hướng dẫn từng bước

### Bước 1: Mở Google Colab
1. Truy cập: https://colab.research.google.com
2. Tạo notebook mới: **File → New notebook**
3. Đổi runtime: **Runtime → Change runtime type → GPU (T4)**
4. Xác nhận đang có GPU: chạy `!nvidia-smi`

### Bước 2: Copy code vào Colab
- Mở file `MaiAnh_ViT5_Finetune.py`
- Mỗi đoạn ngăn cách bởi `# %%` là **1 cell** trong Colab
- Copy từng đoạn vào Colab theo thứ tự từ trên xuống

### Bước 3: Upload dữ liệu (từ Trang)
Khi chạy đến **Cell 4 (Bước 4)**, sẽ có nút Upload — chọn 3 file:
- `train.json` — 51 căn huấn luyện
- `val.json` — 8 căn kiểm định  
- `test.json` — 9 căn kiểm thử cuối

### Bước 4: Chạy tuần tự
Chạy từ Cell 1 đến Cell 17. **KHÔNG bỏ cell nào.**

### Bước 5: Download kết quả
Cell 17 sẽ tự động download 3 file về máy:
- `MaiAnh_ViT5_predictions.json`
- `MaiAnh_ViT5_performance.json`
- `loss_curve.png`

---

## ⚙️ Điều chỉnh Hyperparameters

Tất cả tham số đều nằm ở **Cell 3**. Các giá trị gợi ý:

| Tham số | Mặc định | Thử thêm |
|---|---|---|
| `LEARNING_RATE` | `3e-4` | `1e-4`, `5e-4` |
| `EPOCHS` | `20` | Tăng nếu loss chưa hội tụ |
| `BATCH_SIZE` | `4` | `8` nếu VRAM đủ |
| `BEAM_SIZE` | `4` | Thử 1→5 ở Cell 16 |
| `PATIENCE` | `5` | Giảm nếu muốn dừng sớm hơn |

---

## 🔍 Định dạng dữ liệu đầu vào (train/val/test.json)

File JSON phải là array các object. Code tự động nhận diện nhiều tên field:

```json
[
  {
    "id": 10543,
    "raw_input_cleaned": "163.24.80 Tô Hiến Thành 50.2 5 4 13 12.9 tỷ...",
    "clean_title": "Tô Hiến Thành (gần Trường Sơn) 50.2m2 5 lầu 4x13 - 12.9 tỷ",
    "clean_description": "Nhà 5 tầng kiên cố...",
    "extracted_specs": {
      "duong": "Tô Hiến Thành",
      "phuong": "Phường 15",
      "quan": "Quận 10",
      "gia_ty": 12.9,
      "dien_tich_m2": 50.2,
      "so_tang": 5,
      "mat_tien_m": 4.0,
      "rong_hem_m": 4.0,
      "phan_loai_hem": "Hẻm xe tải"
    }
  }
]
```

> Nếu Trang dùng tên field khác, báo để điều chỉnh hàm `parse_sample()`.

---

## 🆘 Xử lý lỗi thường gặp

| Lỗi | Nguyên nhân | Cách xử lý |
|---|---|---|
| `CUDA out of memory` | VRAM không đủ | Giảm `BATCH_SIZE` xuống 2 |
| `KeyError: 'raw_input_cleaned'` | Tên field khác | Điều chỉnh `parse_sample()` |
| `UnicodeDecodeError` | File không phải UTF-8 | Xin Trang lưu lại file UTF-8 |
| Loss không giảm | LR quá cao/thấp | Thử `LEARNING_RATE = 1e-4` |
| Loss giảm rồi tăng | Overfitting | Giảm `PATIENCE`, tăng `WEIGHT_DECAY` |
| Colab disconnect | Session timeout | Bật Google Colab Pro hoặc giữ tab mở |

---

## 📊 Kết quả kỳ vọng

Dựa theo tài liệu dự án, ViT5 được kỳ vọng đạt:
- **ROUGE-L:** ~82% trên tập Test
- **Latency:** ~0.18 giây/căn
- **Chi phí:** 0đ (hoàn toàn offline)
- **Hạng:** #1 trong 5 mô hình

---

## 📝 Sau khi có kết quả

Điền vào `MaiAnh_ViT5_report.md` (template ở `TEMPLATES/`):
1. Hyperparameters đã dùng
2. ROUGE-L score từ Cell 15
3. Latency từ `performance.json`
4. Phân tích 3 lỗi điển hình bạn quan sát
5. Đính kèm ảnh `loss_curve.png`
