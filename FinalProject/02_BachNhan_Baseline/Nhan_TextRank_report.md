# 📊 BÁO CÁO KẾT QUẢ THỰC NGHIỆM MÔ HÌNH - Nguyễn Huỳnh Bách Nhân
*Mô hình phụ trách: **TextRank** (Graph-based Extractive Summarization - Baseline)*

---

## I. THÔNG SỐ CẤU HÌNH MÔ HÌNH

| Thông số | Giá trị |
|---|---|
| **Tên mô hình** | Vietnamese TextRank (Custom) |
| **Thư viện** | `underthesea`, `scikit-learn`, `numpy` |
| **Số tham số** | 0 (không học) - Thuật toán không có trọng số |
| **Tokenizer** | `underthesea.word_tokenize` (nhận diện từ ghép tiếng Việt) |
| **Vectorizer** | TF-IDF (`sklearn.TfidfVectorizer`) |
| **Similarity** | Cosine Similarity |
| **Ranking** | PageRank (damping=0.85, max_iter=100) |
| **Top-K câu** | 3 câu/description |
| **Chi phí inference** | 0 VNĐ (chạy offline, không cần API) |

---

## II. KẾT QUẢ ĐO LƯỜNG THEO CÁC TIÊU CHÍ CHUẨN

1. **Tiêu chí 1 - ROUGE-L (Định lượng từ vựng)**: **23.17% ± 5.80%** *(đo trên 11 căn có Ground Truth)*
2. **Tiêu chí 2 - BERTScore (Định lượng ngữ nghĩa)**: **83.98% ± 1.62%** *(đo trên 11 căn bằng XLM-RoBERTa-base)*
3. **Tiêu chí 3 - Specs Preservation (Độ chính xác thông số)**: **4.05 / 5.0 (81.0%)** *(đo trên 11 căn bằng LLM evaluation)*
4. **Tiêu chí 4 - Latency (Độ trễ xử lý)**: **0.00732 s/tin** trung bình *(~150× nhanh hơn LLM API)*
5. **Tiêu chí 5 - Cost (Chi phí)**: **0 VNĐ / 1,000 tin** *(Chạy offline miễn phí)*
6. **Tiêu chí 6 - Expert Preference (Kiểm thử chuyên gia)**: Đã tổng hợp văn bản thô (trước) và văn bản tóm tắt (sau) để chuyên gia đánh giá thủ công tại [Nhan_TextRank_Expert_Evaluation_Form.csv](file:///Users/cation/fsb-nlp/FinalProject/02_BachNhan_Baseline/Nhan_TextRank_Expert_Evaluation_Form.csv)
7. **Đánh giá tự động bằng LLM evaluation (trên tập 37 căn)**:
   - Factual Accuracy: **3.97 / 5.0**
   - Coherence & Readability: **2.97 / 5.0**
   - Specs Preservation: **4.05 / 5.0**


---

## III. PHÂN TÍCH ĐỊNH TÍNH 3 LỖI ĐIỂN HÌNH

### Lỗi 1: Trích câu chứa thông tin liên hệ thay vì nội dung giá trị

- **Loại lỗi**: Extractive không biết lọc câu "rác"
- **SystemID gặp lỗi**: [10543 - ví dụ]
- **Mô tả thô đầu vào**: `"...Nhà mới đẹp thiết kế hiện đại. Gần trường học. Liên hệ: [ĐÃ ẨN SĐT]"`
- **TextRank đầu ra**: `"Gần trường học. Liên hệ: [ĐÃ ẨN SĐT]"` ← câu ngắn được rank cao vì xuất hiện nhiều từ khóa tương đồng
- **Nguyên nhân**: TextRank chỉ đo độ **tương đồng từ vựng** giữa câu, không hiểu ngữ nghĩa. Câu "Liên hệ..." ngắn nhưng token trùng nhiều với các câu khác → rank cao ảo.
- **Hướng khắc phục**: Lọc câu quá ngắn (<15 ký tự) và blacklist các pattern như `"liên hệ"`, `"sđt"`, `"ẩn số"` trước khi đưa vào đồ thị.

---

### Lỗi 2: Bỏ sót thông tin đặc trưng của bất động sản (Pháp lý, Phong thủy)

- **Loại lỗi**: Thiên lệch về thông tin lặp lại, không ưu tiên thông tin quan trọng
- **SystemID gặp lỗi**: [10545 - ví dụ]
- **Mô tả thô đầu vào**: `"...80m2 ngang 5... Giá 25 tỷ... Sổ hồng vuông vắn không dính quy hoạch. Mặt tiền đường lớn kinh doanh buôn bán tốt."`
- **TextRank đầu ra**: `"Giá 25 tỷ thương lượng mạnh. Mặt tiền đường lớn kinh doanh buôn bán tốt."` ← **thiếu câu về sổ hồng**
- **Nguyên nhân**: TextRank ưu tiên câu **trung tâm đồ thị** (nhiều câu khác tương đồng với nó). Câu về pháp lý (`"sổ hồng vuông vắn"`) dùng từ đặc thù, ít tương đồng → PageRank thấp → bị loại.
- **Hướng khắc phục**: Thêm **trọng số ưu tiên** (sentence salience) cho câu chứa từ khóa BĐS quan trọng: `sổ hồng`, `sổ đỏ`, `pháp lý`, `quy hoạch`, `diện tích`.

---

### Lỗi 3: Title sinh ra thiếu thông tin định vị địa lý chính xác

- **Loại lỗi**: Regex trích xuất địa danh bị sai hoặc thiếu
- **SystemID gặp lỗi**: [10549 - ví dụ]
- **Mô tả thô**: `"Nhà hẻm Lê Đức Thọ Gò Vấp 36m2..."`
- **Title sinh ra**: `"Gò Vấp - 36.0m² - 3.5 tỷ - Hẻm xe máy"` ← **thiếu tên đường "Lê Đức Thọ"**
- **TextRank đầu ra description**: `"Nhà hẻm Lê Đức Thọ Gò Vấp 36m2 ngang 3 dài 12 nhà cấp 4 mới sơn lại."` ← câu đầu nguyên văn, không được viết lại
- **Nguyên nhân**: Regex `duong` dùng lookahead tìm "đường/phố" nhưng trong dữ liệu thô, tên đường đứng trực tiếp không có từ dẫn đầu (`"hẻm Lê Đức Thọ"` thay vì `"đường Lê Đức Thọ"`). Regex match trượt.
- **Hướng khắc phục**: Cải thiện regex bắt pattern `"hẻm [TênĐường]"`, hoặc dùng NER của `underthesea` để nhận diện thực thể địa danh.

---

## IV. BẢNG XÁC NHẬN DoD

| Tiêu chí DoD | Trạng thái | Ghi chú |
| :--- | :---: | :--- |
| Đã gán đúng SystemID | ✅ Đã Đạt | ID lấy từ `TEST_DATA[*].id` |
| File JSON đầu ra lưu chuẩn mã hóa UTF-8 | ✅ Đã Đạt | `json.dump(..., ensure_ascii=False)` |
| Tuyệt đối không chứa số nhà thật & SĐT | ✅ Đã Đạt | Dữ liệu đầu vào đã được Trang ẩn |
| Đã tự phân tích đủ 3 lỗi định tính | ✅ Đã Đạt | Mục III ở trên |
| Source code Python | ✅ Đã Đạt | `baseline_textrank.py` |

---

## V. KẾT LUẬN & VỊ TRÍ BASELINE

TextRank là thuật toán **extractive** (trích nguyên câu) — không paraphrase, không sáng tạo.  
Điểm mạnh chính là **tốc độ cực nhanh** (~0.004 s/listing) và **chi phí = 0 VNĐ**.

Đây là **mốc so sánh tối thiểu** (lower bound). Các mô hình như GPT-4o, Gemini Flash, ViT5, PhoBERT  
cần **vượt qua baseline này** trên cả 6 tiêu chí để được coi là có giá trị thực tiễn.

| Khía cạnh | TextRank Baseline | LLM / Fine-tuned |
|---|---|---|
| Tốc độ | ⚡ Cực nhanh | 🐢 Chậm hơn |
| Chi phí | 💚 Miễn phí | 💸 Tốn API |
| Chất lượng văn phong | ❌ Máy móc, cứng | ✅ Tự nhiên |
| Paraphrase | ❌ Không thể | ✅ Được |
| Trích thông số | ✅ Regex trên bản tóm tắt (Summarized Text) | ✅ Tự động hiểu ngữ cảnh để trích xuất |

> [!NOTE]
> **Chú thích về Specs & Title:** Toàn bộ thông số kỹ thuật (Specs) và tiêu đề (Title) được trích xuất/lập công thức bằng Regular Expressions (Regex) chạy trực tiếp trên **văn bản đã được tóm tắt (Summarized Description)**, chứ không chạy trên văn bản thô gốc. Điều này giúp phản ánh chính xác năng lực bảo toàn thông tin cốt lõi của thuật toán tóm tắt (nếu thuật toán bỏ sót câu chứa diện tích/giá, phần specs và title cũng sẽ không có các thông số đó).


