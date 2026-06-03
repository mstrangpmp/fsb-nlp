# 📊 BÁO CÁO SO SÁNH HIỆU NĂNG BASELINE - NGUYỄN HUỲNH BÁCH NHÂN
*So sánh hai thuật toán trích xuất đồ thị cổ điển: **TextRank** và **LexRank***

---

## I. BẢNG THỐNG KÊ TỔNG HỢP HIỆU NĂNG TOÀN DIỆN
*(Đánh giá trên tập dữ liệu thử nghiệm 11 bản ghi có nhãn Ground Truth & Đánh giá chất lượng tự động bằng LLM evaluation)*

| Mô Hình Chạy Thử | ROUGE-L (TB) | BERTScore (TB) | Specs Pres. (TB) | Độ Trễ (Latency) | Chi Phí (Cost/1k) | Trạng Thái |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **TextRank** | 23.17% ± 5.80% | 83.98% ± 1.62% | 3.27 / 5.0 (65.4%) | ~0.007 s/listing | 0 VNĐ | Hoàn thành |
| **LexRank** | 23.92% ± 5.79% | 83.83% ± 1.57% | 3.19 / 5.0 (63.8%) | ~0.007 s/listing | 0 VNĐ | Hoàn thành |

---

## II. ĐÁNH GIÁ CHẤT LƯỢNG TRÊN TẬP INFERENCE (26 TIN CHƯA CÓ NHÃN)
*(Chấm điểm tự động bằng LLM evaluation so sánh trực tiếp kết quả với Tin Đăng Thô)*

| Mô hình | Factual Accuracy (TB) | Coherence & Readability (TB) | Specs Preservation (TB) |
| :--- | :---: | :---: | :---: |
| **TextRank** | **3.42 / 5.0** | 2.77 / 5.0 | **3.19 / 5.0** |
| **LexRank** | 3.38 / 5.0 | **2.81 / 5.0** | **3.19 / 5.0** |

### Nhận xét & Đánh giá định tính:
1. **Thay đổi lớn về tiêu chí Bảo toàn thông số (Specs Preservation):**
   - Điểm số Specs Preservation của cả hai mô hình giảm mạnh (từ mức ~4.1 xuống **3.19/5.0**). Nguyên nhân là do hệ thống đã chuyển đổi logic: chạy Regex trích xuất Specs trực tiếp **trên bản tóm tắt đầu ra** thay vì văn bản thô ban đầu. 
   - Điều này mang lại sự khách quan và thực chất tuyệt đối: Nếu thuật toán tóm tắt (TextRank/LexRank) lọc bỏ các câu chứa diện tích/giá tiền thì Specs và Tiêu đề sinh ra sẽ bị khuyết các trường đó.
2. **Độ mạch lạc (Coherence) & Độ trung thực (Factual Accuracy):**
   - **LexRank** tiếp tục cho thấy độ mạch lạc nhỉnh hơn một chút (**2.81/5.0** so với **2.77/5.0** của TextRank) nhờ cơ chế lọc ngưỡng tương đồng ($t=0.1$) giúp gạt bỏ bớt các câu nhiễu bị cô lập trong đồ thị câu.
   - **TextRank** đạt độ trung thực thực tế nhỉnh hơn (**3.42/5.0** so với **3.38/5.0** của LexRank) trên tập 26 dòng thử nghiệm.
3. **Độ trễ và Chi phí:** Cả hai mô hình đều chạy hoàn toàn offline trên CPU/Local GPU, cho độ trễ cực thấp (~7 ms/listing) và chi phí vận hành bằng 0.

---

## III. TỔNG HỢP KIỂM TRA CHUYÊN GIA (EXPERT VERIFICATION FORM)
Để phục vụ việc đánh giá độ ưu tiên của chuyên gia (**Expert Preference**), toàn bộ dữ liệu văn bản thô đầu vào và văn bản tóm tắt đầu ra của cả hai mô hình đã được trích xuất và lưu riêng biệt tại:

1. **TextRank Expert Form:** [Nhan_TextRank_Expert_Evaluation_Form.csv](file:///Users/cation/fsb-nlp/FinalProject/02_BachNhan_Baseline/Nhan_TextRank_Expert_Evaluation_Form.csv)
2. **LexRank Expert Form:** [Nhan_LexRank_Expert_Evaluation_Form.csv](file:///Users/cation/fsb-nlp/FinalProject/02_BachNhan_Baseline/Nhan_LexRank_Expert_Evaluation_Form.csv)

### Cấu trúc bảng kiểm thử của Chuyên gia:
- **Mô tả thô (Raw Input):** Nội dung tin đăng bất động sản ban đầu chưa qua xử lý.
- **Mô tả dự đoán (Pred Desc):** Kết quả tóm tắt trích xuất từ mô hình TextRank hoặc LexRank.
- **Tiêu đề dự đoán (Pred Title):** Tiêu đề chuẩn hóa sinh ra từ thông số trích xuất.
- **Thông số trích xuất (Specs):** JSON chứa các thông số được bóc tách bằng regex.
- **LLM Judge Scores/Reasons:** Điểm số tự động của LLM evaluation làm mốc tham chiếu cho chuyên gia.
- **Cột trống cho Chuyên gia điền:** `Expert_Accuracy_Score (1-5)`, `Expert_Coherence_Score (1-5)`, `Expert_Specs_Score (1-5)`, `Expert_Corrected_Description` (văn bản viết lại chuẩn), và `Expert_Notes` (ghi chú lỗi định tính).
