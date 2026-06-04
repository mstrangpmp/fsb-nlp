# 📊 BÁO CÁO SO SÁNH HIỆU NĂNG BASELINE TOÀN DIỆN - NGUYỄN HUỲNH BÁCH NHÂN
*So sánh hiệu năng giữa phương pháp đồ thị cổ điển (TF-IDF) và phương pháp ngữ nghĩa học sâu (Semantic Embedding - BGE-M3) trên hai thuật toán **TextRank** và **LexRank***

---

## I. BẢNG THỐNG KÊ TỔNG HỢP HIỆU NĂNG TRÊN TẬP GROUND TRUTH (11 BẢN GHI)
*(Đánh giá chéo bằng chỉ số tự động ROUGE-L, BERTScore và chấm điểm định tính bằng LLM Judge gemma-4-e4b)*

| Mô Hình Chạy Thử | ROUGE-L (F1) | BERTScore (F1) | LLM Factual Acc. | LLM Coherence | LLM Specs Pres. | Độ Trễ (Latency) | Chi Phí |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **TextRank (TF-IDF)** | 23.17% ± 5.80% | 83.98% ± 1.62% | 3.64 / 5.0 | 2.73 / 5.0 | 3.45 / 5.0 | **~0.008 s** | 0 VNĐ (Local) |
| **LexRank (TF-IDF)** | **23.92% ± 5.79%** | 83.83% ± 1.57% | 3.73 / 5.0 | 2.91 / 5.0 | 3.18 / 5.0 | **~0.007 s** | 0 VNĐ (Local) |
| **TextRank (Embedding)** | 23.21% ± 5.66% | **84.18% ± 1.57%** | **3.82 / 5.0** | **3.09 / 5.0** | 3.45 / 5.0 | ~0.148 s | 0 VNĐ (Local) |
| **LexRank (Embedding)** | 23.59% ± 5.56% | 83.85% ± 1.58% | 3.73 / 5.0 | 3.00 / 5.0 | **3.55 / 5.0** | ~0.139 s | 0 VNĐ (Local) |

---

## II. ĐÁNH GIÁ CHẤT LƯỢNG TRÊN TẬP INFERENCE (26 TIN CHƯA CÓ NHÃN)
*(Chấm điểm tự động bằng LLM Judge gemma-4-e4b so sánh trực tiếp kết quả với Tin Đăng Thô)*

| Mô hình | Factual Accuracy (TB) | Coherence & Readability (TB) | Specs Preservation (TB) |
| :--- | :---: | :---: | :---: |
| **TextRank (TF-IDF)** | 3.42 / 5.0 | 2.77 / 5.0 | 3.19 / 5.0 |
| **LexRank (TF-IDF)** | 3.38 / 5.0 | 2.81 / 5.0 | 3.19 / 5.0 |
| **TextRank (Embedding)** | **3.92 / 5.0** | **3.23 / 5.0** | 3.65 / 5.0 |
| **LexRank (Embedding)** | 3.77 / 5.0 | 3.04 / 5.0 | **3.73 / 5.0** |

---

## III. NHẬN XÉT & PHÂN TÍCH CHUYÊN SÂU

### 1. Sức mạnh vượt trội từ Semantic Embedding (BGE-M3)
* **Chất lượng nội dung vượt bậc:** 
  * Cả hai thuật toán sử dụng ngữ nghĩa học sâu (`TextRank_Embedding` và `LexRank_Embedding`) đều mang lại điểm số LLM Judge vượt trội so với TF-IDF trên cả 3 khía cạnh: **Độ trung thực thông tin (Factual Accuracy)**, **Mạch lạc (Coherence)** và **Bảo toàn thông số (Specs Preservation)**.
  * Nổi bật nhất là `TextRank_Embedding` trên tập Inference đạt **3.92/5.0** Factual Accuracy (so với 3.42 của TF-IDF) và **3.23/5.0** Coherence (so với 2.77 của TF-IDF). 
* **Lý do kỹ thuật:** TF-IDF chỉ tính tần suất từ đơn thuần nên dễ bị nhiễu bởi các từ quảng cáo lặp đi lặp lại của môi giới (ví dụ: *siêu rẻ, chốt bùng nổ, hàng hiếm*). Ngược lại, ma trận tương đồng xây dựng từ BGE-M3 phản ánh chính xác cấu trúc ngữ nghĩa thực tế của câu, giúp thuật toán trích xuất đúng các câu mô tả cốt lõi về vị trí, kết cấu và thông số kỹ thuật.

### 2. Bảo toàn thông số kỹ thuật (Specs Preservation)
* Khảo sát điểm số bảo toàn thông số trên tập Inference cho thấy bước nhảy lớn:
  * TF-IDF: **3.19 / 5.0**
  * Embedding: **3.65 / 5.0** (TextRank) và **3.73 / 5.0** (LexRank)
* **Giải thích:** Nhờ không gian vector embedding, các câu chứa thông số kích thước (ngang x sâu), số tầng hay tình trạng hẻm được liên kết ngữ nghĩa chặt chẽ với nhau và với từ khóa bất động sản chủ chốt. Do đó, thuật toán đồ thị ngữ nghĩa ưu tiên trích xuất các câu mang tính mô tả kỹ thuật cao này vào văn bản tóm tắt, giúp tiêu đề sinh ra từ regex có đầy đủ tham số hơn.

### 3. Đánh giá ROUGE-L và BERTScore
* Điểm số **ROUGE-L** của cả 4 mô hình khá tương đồng (~23.1% đến ~23.9%). Điều này chứng minh ROUGE-L (so khớp từ ngữ chính xác) bị hạn chế đối với văn phong quảng cáo tự do của môi giới bất động sản Việt Nam.
* Tuy nhiên, **BERTScore** của `TextRank_Embedding` đạt mức cao nhất (**84.18% ± 1.57%**), cho thấy độ tương đồng về mặt vector ngữ nghĩa giữa văn bản tóm tắt tự động và Ground Truth do chuyên gia viết là lớn nhất.

### 4. Đánh giá Thương mại & Hiệu năng (Latency vs. Cost)
* **Chi phí:** Hoàn toàn bằng **0 VNĐ** cho cả 4 phương pháp do chạy offline trên phần cứng nội bộ (Local CPU / Local GPU) sử dụng LM Studio.
* **Tốc độ xử lý:**
  * **TF-IDF:** Tốc độ kinh ngạc (~7-8 ms/listing), thích hợp cho việc xử lý hàng triệu tin đăng theo thời gian thực (Real-time Pipeline) trên cấu hình máy chủ tối giản.
  * **Embedding:** Độ trễ tăng lên ~138-148 ms/listing (do quá trình tạo vector embedding của mô hình BGE-M3 cục bộ). Dù chậm hơn TF-IDF nhưng thời gian này vẫn cực kỳ nhanh (xử lý ~7 tin đăng mỗi giây) và hoàn toàn đáp ứng được môi trường production thực tế.

---

## IV. TỔNG HỢP BIỂU MẪU ĐÁNH GIÁ CỦA CHUYÊN GIA (EXPERT EVALUATION FORMS)
Để phục vụ việc kiểm thử mù (blind test) và đánh giá độ ưu tiên thực tế của chuyên gia (Expert Preference), biểu mẫu CSV chuyên nghiệp cho từng mô hình đã được chuẩn bị đầy đủ tại các đường dẫn sau:

1. **TextRank (TF-IDF) Expert Form:** [Nhan_TextRank_Expert_Evaluation_Form.csv](file:///Users/cation/fsb-nlp/FinalProject/02_BachNhan_Baseline/TextRank_TFIDF/Nhan_TextRank_Expert_Evaluation_Form.csv)
2. **LexRank (TF-IDF) Expert Form:** [Nhan_LexRank_Expert_Evaluation_Form.csv](file:///Users/cation/fsb-nlp/FinalProject/02_BachNhan_Baseline/LexRank_TFIDF/Nhan_LexRank_Expert_Evaluation_Form.csv)
3. **TextRank (Embedding) Expert Form:** [Nhan_TextRank_Embedding_Expert_Evaluation_Form.csv](file:///Users/cation/fsb-nlp/FinalProject/02_BachNhan_Baseline/TextRank_Embedding/Nhan_TextRank_Embedding_Expert_Evaluation_Form.csv)
4. **LexRank (Embedding) Expert Form:** [Nhan_LexRank_Embedding_Expert_Evaluation_Form.csv](file:///Users/cation/fsb-nlp/FinalProject/02_BachNhan_Baseline/LexRank_Embedding/Nhan_LexRank_Embedding_Expert_Evaluation_Form.csv)

*Mỗi file chứa đầy đủ 26 tin chưa có nhãn kèm kết quả dự đoán (Tiêu đề, Mô tả, Specs), điểm số tham chiếu của LLM Judge, và các cột trống để chuyên gia ghi nhận điểm thực tế.*
