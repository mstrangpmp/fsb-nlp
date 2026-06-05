# ⚡ 06 - Nguyễn Hữu Hiệu (PhoBERT Specialist)

## 📌 Vai trò & Nhiệm vụ cốt lõi
- Xây dựng pipeline fine-tune mô hình Seq2Seq dựa trên **PhoBERT (vinai/phobert-base)** trên Google Colab T4.
- Thiết lập kiến trúc **EncoderDecoderModel** (PhoBERT làm cả encoder lẫn decoder).
- Thực hiện dự đoán trên tập Test (9 căn không có nhãn) và đo đạc thời gian inference.
- Nguồn dữ liệu duy nhất: `NLP.FSB Pool.xlsx`.

---

## 📦 Sản phẩm bàn giao (Deliverables)
```
06_HuuHieu_PhoBERT/
├── HuuHieu_PhoBERT_FineTuning.ipynb   ← Notebook Colab đầy đủ
├── HuuHieu_PhoBERT_predictions.json   ← Kết quả 9 căn test
├── HuuHieu_PhoBERT_performance.json   ← Hiệu năng & điểm đánh giá
├── loss_curve.png                     ← Biểu đồ Loss & ROUGE-L
└── README.md                          ← File này
```

---

## I. THÔNG SỐ CẤU HÌNH MÔ HÌNH

| Thông số | Giá trị |
|:---|:---|
| **Mô hình nền** | `vinai/phobert-base` |
| **Kiến trúc** | `EncoderDecoderModel` (phobert-base × 2) |
| **Tổng tham số** | ~270M |
| **Max input tokens** | 256 (PhoBERT hard limit) |
| **Max target tokens** | 256 |
| **Epochs** | 50 (dừng sớm ở epoch 9) |
| **Learning Rate** | 3e-5 |
| **Batch size** | 2 (grad accumulation 4 → effective 8) |
| **Beam Search** | `num_beams = 4` |
| **Weight Decay** | 0.01 |
| **Early Stopping** | patience = 8 (theo ROUGE-L trên val) |
| **Môi trường** | Google Colab T4 GPU |

---

## II. DỮ LIỆU SỬ DỤNG

**Nguồn duy nhất:** `NLP.FSB Pool.xlsx`

| Split | Số mẫu | Mô tả |
|:---|:---:|:---|
| Train | 9 | 9 hàng đầu có cột D (Mô tả chuẩn) |
| Val | 2 | 2 hàng cuối có cột D |
| Test | 9 | 9 hàng không có cột D (chỉ có cột A) |

**Mapping dữ liệu:**
- **Input (Cột A):** Mô tả thô của môi giới — có emoji, jargon, SĐT, spam
- **Target (Cột D):** Mô tả chuẩn do chuyên gia viết — format: `{Title} | {Use case}` + các section: Vị trí, Hẻm, Kết cấu, Diện tích, Pháp lý, Giá

---

## III. KẾT QUẢ ĐO LƯỜNG

### Kết quả training
| Metric | Giá trị |
|:---|:---|
| Best ROUGE-L (Val) | **20.28%** (Epoch 1) |
| Final Train Loss | 24.93 (dừng ở epoch 9) |
| Training time | ~20 phút (T4 GPU) |
| Early stopping | Dừng tại epoch 9/50 |

### Kết quả đánh giá (trên Val set — 2 mẫu)
| Tiêu chí | Điểm | Ghi chú |
|:---|:---:|:---|
| **ROUGE-L F1** | 17.88% | Đo khớp từ vựng với ground truth |
| **BERTScore F1** | 72.63% | Đo tương đồng ngữ nghĩa (xlm-roberta-base) |
| **LLM Judge** | N/A | Bỏ qua (LM Studio không chạy được trên Colab) |
| **Latency** | 0.855s/căn | Thời gian inference trung bình trên T4 |
| **Cost/1k** | 0đ | Không tốn API cost |

### Đánh giá tổng quan
| Metric | **PhoBERT** | Ghi chú |
|:---|:---:|:---|
| ROUGE-L F1 | **17.88%** | Thấp do dataset quá nhỏ (9 mẫu) |
| BERTScore F1 | **72.63%** | Ở mức trung bình |
| Latency | **0.855s/căn** | Chạy trên T4 GPU |
| Cost/1k | **0đ** | Không tốn API cost |

---

## IV. PHÂN TÍCH ĐỊNH TÍNH 3 LỖI ĐIỂN HÌNH

### Lỗi 1: Decoder không hội tụ — Output lặp token vô nghĩa
- **Nguyên nhân:** Fine-tune mô hình 270M tham số trên chỉ 9 mẫu huấn luyện. Decoder (cross-attention layers khởi tạo ngẫu nhiên) không có đủ dữ liệu để học.
- **Biểu hiện:** Model sinh ra chuỗi lặp vô nghĩa như `"phần phần để phần phần phụ_giúp phần..."` với tỷ lệ lặp 37–68%.
- **Giải pháp đã áp dụng:** Thay thế bằng template description sinh từ regex extraction. Kết quả vẫn có cấu trúc đúng nhưng không phải output thực sự của AI.
- **Khắc phục thực sự:** Cần ít nhất 200+ mẫu huấn luyện có nhãn.

### Lỗi 2: Trích xuất quận bị sai (Regex bug)
- **SystemID gặp lỗi:** `SYS-MP75Z7G0-H3`, `SYS-MP75ZR8R-C4`, `SYS-MP760LYQ-AC`
- **Mô tả thô đầu vào:** `"Cao Thắng ... Hòa Hưng Quận 10 ..."`
- **Output bị lỗi:** `"quan": "Quận 1"` (sai) thay vì `"Quận 10"` (đúng)
- **Nguyên nhân:** Regex pattern `quận\s*(\d+)` match số `10` nhưng chỉ đọc được `1` vì pattern không đủ chính xác với số 2 chữ số.
- **Khắc phục:** Dùng `quận\s*(\d{1,2})` thay vì `(\d+)`.

### Lỗi 3: Early Stopping quá sớm do Val set quá nhỏ
- **Nguyên nhân:** Chỉ có 2 mẫu validation → ROUGE-L nhảy loạn (4.54% → 13.07% → 7.51%) chỉ vì ngẫu nhiên trong beam search, không phản ánh thực sự chất lượng model.
- **Biểu hiện:** Model đạt ROUGE-L 20.28% ở epoch 1, sau đó early stopping dừng ở epoch 9 vì val metric không ổn định, mặc dù train loss vẫn đang giảm (28 → 19).
- **Khắc phục:** Cần ít nhất 10–20 mẫu validation để ROUGE-L có ý nghĩa thống kê.

---

## V. KẾT LUẬN

| Phát hiện | Ý nghĩa |
|:---|:---|
| PhoBERT (270M params) + 9 mẫu → không hội tụ | Data quantity > Model complexity với dataset nhỏ |
| ROUGE-L 17.88%, BERTScore 72.63% | Kết quả chấp nhận được trong bối cảnh hạn chế dữ liệu |
| Cần 200+ mẫu để PhoBERT thực sự học được | Đây là hướng cải thiện rõ ràng nhất |

> **Kết luận cốt lõi:** *"Bottleneck chính của PhoBERT trong bài toán này là số lượng dữ liệu có nhãn quá ít (9 mẫu), không phải kiến trúc mô hình. Với 200+ mẫu huấn luyện, PhoBERT có tiềm năng đạt kết quả tốt hơn đáng kể."*

---

## VI. BẢNG XÁC NHẬN DoD

| Tiêu chí DoD | Trạng thái |
|:---|:---:|
| Nguồn dữ liệu chỉ từ `NLP.FSB Pool.xlsx` | ✅ |
| File `HuuHieu_PhoBERT_predictions.json` (9 records, đúng format) | ✅ |
| File `HuuHieu_PhoBERT_performance.json` | ✅ |
| Mã hóa UTF-8, không chứa SĐT & địa chỉ thật | ✅ |
| ROUGE-L đo trên val set | ✅ |
| BERTScore đo trên val set | ✅ |
| Loss curve & ROUGE-L curve (`loss_curve.png`) | ✅ |
| Beam Search với `num_beams=4` | ✅ |
| Kiến trúc `EncoderDecoderModel` với `vinai/phobert-base` | ✅ |
| Phân tích 3 lỗi định tính | ✅ |
| Google Colab Notebook `.ipynb` | ✅ |

## 🔗 Tích hợp hệ thống và Chạy lại (System Integration & Re-running)

- **Vị trí tệp bàn giao thực tế để hiển thị trên App**:
  - predictions JSON: `FinalProject/06_HuuHieu_PhoBERT/HuuHieu_PhoBERT_predictions1.json`
  - performance JSON: `FinalProject/06_HuuHieu_PhoBERT/HuuHieu_PhoBERT_performance1.json`
- **Cách cập nhật kết quả dự đoán của mô hình**:
  - Khi chạy lại và download kết quả mới từ Colab, hãy lưu đè kết quả định dạng JSON vào 2 tệp trên (`HuuHieu_PhoBERT_predictions1.json` và `HuuHieu_PhoBERT_performance1.json`).
  - **Với Flask App**: Flask app sẽ tự động nạp dữ liệu mới từ các tệp trên và tính lại các chỉ số đối chiếu ngay lập tức.
  - **Với Trang tĩnh (`app/index.html`)**: Chạy generator script để biên dịch dữ liệu mới nhúng vào trang tĩnh:
    ```bash
    cd FinalProject/app
    python generate_static_index.py
    ```

