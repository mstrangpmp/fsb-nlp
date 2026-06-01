# 📑 TÀI LIỆU UNIFIED DoD, FILE TEMPLATE & HƯỚNG DẪN BÀN GIAO CHI TIẾT
*Dự án FSB-NLP501: Rút Gọn & Chuẩn Hóa Tin Đăng Bất Động Sản Bằng Transformers*

Tài liệu này được thiết kế để chuẩn hóa quy trình làm việc độc lập của 6 thành viên, ban hành các file template nhất quán và tự động hóa khâu tổng hợp dữ liệu cuối cùng của **Trang (Leader)**.

---

## 💾 PHẦN 1: CÁC FILE TEMPLATE TIÊU CHUẨN (DELIVERABLE TEMPLATES)
*Tất cả 5 kỹ sư mô hình bắt buộc phải lưu sản phẩm bàn giao theo đúng định dạng cấu trúc dưới đây.*

### 1. Template file kết quả chuẩn hóa: `[Ten]_predictions.json`
Mỗi bạn tạo 1 file JSON chứa đúng 9 đối tượng tương ứng với 9 căn Test.
> [!IMPORTANT]
> - `id` bắt buộc phải là **SystemID** lấy từ sheet Pool của đầu chủ **Trà Mi**.
> - File bắt buộc phải lưu bằng mã hóa **UTF-8** (để không bị lỗi font tiếng Việt khi Trang mở trên Excel Windows).

```json
[
  {
    "id": 10543,
    "raw_input_cleaned": "Mô tả thô lấy từ cột Mô tả chi tiết của đầu chủ Trà Mi (đã được Trang tiền xử lý sạch địa chỉ và SĐT)...",
    "predicted_title": "Tô Hiến Thành (gần Trường Sơn) 50.2m2 5 lầu 4x13 - 12.9 tỷ Hẻm xe tải",
    "predicted_description": "Nhà 5 tầng kiên cố, 6 phòng ngủ, 4 WC tọa lạc tại vị trí cực đẹp khu trung tâm Quận 10, gần trục đường lớn Trường Sơn. Sổ nở hậu nhẹ cực kỳ phong thủy...",
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

### 2. Template file nhật ký vận hành: `[Ten]_performance.json`
Mỗi bạn lưu 1 file JSON ghi nhận tốc độ và chi phí của mô hình của mình trên 9 căn test.

```json
{
  "model_name": "ViT5-base / GPT-4o-mini / PhoBERT / TextRank",
  "average_latency_seconds": 0.18,
  "estimated_cost_vnd_per_1k": 0,
  "latency_per_sample": [0.15, 0.22, 0.17, 0.19, 0.20, 0.16, 0.18, 0.17, 0.19]
}
```

### 3. Template file báo cáo chi tiết: `[Ten]_report.md`
Mỗi thành viên bắt buộc phải soạn báo cáo riêng của mình theo đúng cấu trúc tiêu chí đánh giá dưới đây để Trang dễ dàng tổng hợp vào slide lớn.

```markdown
# 📊 BÁO CÁO KẾT QUẢ THỰC NGHIỆM MÔ HÌNH - [TÊN CỦA BẠN]
*Mô hình phụ trách: [ViT5 / PhoBERT / GPT-4o-mini / Gemini Flash / TextRank]*

## I. THÔNG SỐ CẤU HÌNH MÔ HÌNH (MODEL CONFIGURATION)
- **Tên mô hình nền**: [Ví dụ: vietnamese-t5-base / gpt-4o-mini...]
- **Kích thước / Số lượng tham số**: [Ví dụ: 220M params / GPT API...]
- **Thông số kỹ thuật / Hyperparameters**:
  - *Đối với Học sâu (ViT5/PhoBERT)*: Epochs: [X], Learning Rate: [Y], Batch Size: [Z], Beam Size: [W]
  - *Đối với API (GPT/Gemini)*: Temperature: [X], Few-shot Samples: [3 ví dụ]

## II. KẾT QUẢ ĐO LƯỜNG THEO 6 TIÊU CHÍ CHUẨN (6 EVALUATION METRICS)
Dưới đây là kết quả tự đánh giá của mô hình trên **tập Validation** (hoặc kết quả Trang đo trên **tập Test**):

1. **Tiêu chí 1: ROUGE-L (Định lượng từ vựng)**: [Điền số]% (Đo mức độ khớp cấu trúc từ vựng với Ground Truth).
2. **Tiêu chí 2: BERTScore (Định lượng ngữ nghĩa)**: [Điền số]% (Đo độ tương đồng ngữ nghĩa sâu, chấp nhận từ đồng nghĩa).
3. **Tiêu chí 3: Specs Preservation (Độ chính xác thông số)**: [Điền số]% (Tỷ lệ khớp đúng 9 cột thông số trong extracted_specs).
4. **Tiêu chí 4: Latency (Độ trễ xử lý)**: [Điền số] giây (Thời gian inference trung bình trên 1 căn).
5. **Tiêu chí 5: Cost (Chi phí vận hành)**: [Điền số] VNĐ / 1,000 tin đăng.
6. **Tiêu chí 6: User Preference (Độ thỏa dụng - Chuyên gia ngành chấm)**: [Để trống cho chị Trang điền điểm Elo/Hạng].

## III. PHÂN TÍCH ĐỊNH TÍNH 3 LỖI ĐIỂN HÌNH (3 QUALITATIVE ERRORS)
Mô tả chi tiết 3 lỗi văn văn phong hoặc lệch thông số mà mô hình của bạn thường gặp phải trên tập Test:

### Lỗi 1: [Tên lỗi - Ví dụ: Lỗi lặp cụm từ hoặc Ảo giác địa danh]
- **SystemID gặp lỗi**: [Ví dụ: 10543]
- **Mô tả thô đầu vào**: "[Copy đoạn mô tả thô từ Trang]"
- **AI chuẩn hóa đầu ra**: "[Copy đoạn AI viết bị lỗi]"
- **Mô tả chi tiết lỗi & Nguyên nhân**: [Giải thích vì sao lỗi và cách khắc phục]

### Lỗi 2: [Tên lỗi]
- **SystemID gặp lỗi**: [...]
- **Mô tả thô đầu vào**: "..."
- **AI chuẩn hóa đầu ra**: "..."
- **Mô tả chi tiết lỗi & Nguyên nhân**: [...]

### Lỗi 3: [Tên lỗi]
- **SystemID gặp lỗi**: [...]
- **Mô tả thô đầu vào**: "..."
- **AI chuẩn hóa đầu ra**: "..."
- **Mô tả chi tiết lỗi & Nguyên nhân**: [...]

## IV. BẢNG XÁC NHẬN DoD (DoD CHECKLIST STATUS)
| Tiêu chí DoD | Trạng thái | Ghi chú |
| :--- | :---: | :--- |
| Đã gán đúng SystemID | [Đã Đạt / Chưa] | |
| File JSON đầu ra lưu chuẩn mã hóa UTF-8 | [Đã Đạt / Chưa] | |
| Tuyệt đối không chứa số nhà thật & SĐT | [Đã Đạt / Chưa] | |
| Đã tự phân tích đủ 3 lỗi định tính | [Đã Đạt / Chưa] | |
```
