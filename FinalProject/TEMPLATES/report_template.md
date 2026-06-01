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
