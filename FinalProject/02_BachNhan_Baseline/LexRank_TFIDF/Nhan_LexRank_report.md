# 📊 BÁO CÁO KẾT QUẢ THỰC NGHIỆM MÔ HÌNH - Nguyễn Huỳnh Bách Nhân
*Mô hình phụ trách: **LexRank** (Thresholded Graph-based Extractive Summarization - Baseline)*

---

## I. THÔNG SỐ CẤU HÌNH MÔ HÌNH

| Thông số | Giá trị |
|---|---|
| **Tên mô hình** | Vietnamese LexRank (Custom) |
| **Thư viện** | `underthesea`, `scikit-learn`, `numpy` |
| **Số tham số** | 0 (không học) - Thuật toán không có trọng số |
| **Tokenizer** | `underthesea.word_tokenize` (nhận diện từ ghép tiếng Việt) |
| **Vectorizer** | TF-IDF (`sklearn.TfidfVectorizer`) |
| **Similarity** | Cosine Similarity |
| **Threshold (Ngưỡng)** | $t = 0.1$ (Lọc cạnh yếu trong đồ thị câu) |
| **Ranking** | PageRank (damping=0.85, max_iter=100) trên ma trận kề nhị phân |
| **Top-K câu** | 3 câu/description |
| **Chi phí inference** | 0 VNĐ (chạy offline, không cần API) |

---

## II. KẾT QUẢ ĐO LƯỜNG THEO CÁC TIÊU CHÍ CHUẨN

1. **Tiêu chí 1 - ROUGE-L (Định lượng từ vựng)**: **23.92% ± 5.79%** *(đo trên 11 căn có Ground Truth — cao hơn TextRank 0.75% nhờ lọc câu nhiễu tốt hơn)*
2. **Tiêu chí 2 - BERTScore (Định lượng ngữ nghĩa)**: **83.83% ± 1.57%** *(đo trên 11 căn bằng XLM-RoBERTa-base)*
3. **Tiêu chí 3 - Specs Preservation (Độ chính xác thông số)**: **4.19 / 5.0 (83.8%)** *(đo trên 11 căn bằng LLM evaluation)*
4. **Tiêu chí 4 - Latency (Độ trễ xử lý)**: **0.00731 s/tin** trung bình *(~150× nhanh hơn LLM API)*
5. **Tiêu chí 5 - Cost (Chi phí)**: **0 VNĐ / 1,000 tin** *(Chạy offline miễn phí)*
6. **Tiêu chí 6 - Expert Preference (Kiểm thử chuyên gia)**: Đã tổng hợp văn bản thô (trước) và văn bản tóm tắt (sau) để chuyên gia đánh giá thủ công tại [Nhan_LexRank_Expert_Evaluation_Form.csv](file:///Users/cation/fsb-nlp/FinalProject/02_BachNhan_Baseline/Nhan_LexRank_Expert_Evaluation_Form.csv)
7. **Đánh giá tự động bằng LLM evaluation (trên tập 37 căn)**:
   - Factual Accuracy: **4.00 / 5.0**
   - Coherence & Readability: **3.14 / 5.0** *(Tốt hơn TextRank nhờ loại bỏ câu rác biệt lập)*
   - Specs Preservation: **4.19 / 5.0**

---

## III. PHÂN TÍCH ĐỊNH TÍNH 3 LỖI ĐIỂN HÌNH

### Lỗi 1: Lỗi trích xuất câu thiếu tính liên kết do loại bỏ cạnh quá đà (Thresholding Over-filtering)

- **Loại lỗi**: Extractive bị cô lập câu do cấu trúc thưa của đồ thị.
- **SystemID gặp lỗi**: [SYS-20264727-938]
- **Mô tả thô đầu vào**: `"...Nhà xây kiên cố. Gần chợ Hòa Hưng. Sổ hồng riêng..."` (các câu quá ngắn và độc lập từ vựng)
- **LexRank đầu ra**: Trích xuất câu đầu tiên rời rạc, bỏ qua câu về pháp lý do các câu này không có từ khóa trùng lặp để vượt qua ngưỡng $t = 0.1$.
- **Nguyên nhân**: LexRank thiết lập ngưỡng $t = 0.1$ để chuyển ma trận tương đồng thành ma trận kề nhị phân (0 hoặc 1). Đối với tin đăng quá ngắn hoặc câu từ đa dạng không lặp từ, các câu quan trọng bị cô lập (độ kết nối = 0) nên PageRank score cực thấp.
- **Hướng khắc phục**: Sử dụng ngưỡng tương đồng động dựa trên độ dài văn bản hoặc giảm ngưỡng xuống $0.05$ đối với văn bản ngắn dưới 5 câu.

---

### Lỗi 2: Lỗi lặp lại thông tin tương đương (Redundant Extraction)

- **Loại lỗi**: Trích trùng nội dung ngữ nghĩa (semantic redundancy)
- **SystemID gặp lỗi**: [SYS-MP766I2E-45]
- **Mô tả thô đầu vào**: chứa nhiều câu cùng mô tả dòng tiền cho thuê 25 triệu/tháng và 25-30 triệu/tháng ở đầu và cuối tin đăng.
- **LexRank đầu ra**: Trích xuất cả 2 câu cùng nói về dòng tiền cho thuê do cả hai đều ở vị trí trung tâm trong đồ thị tương đồng.
- **Nguyên nhân**: Khi các câu có độ tương đồng cosine rất cao, chúng tạo thành một clique mạnh trong đồ thị, khiến cả hai đều nhận được điểm số PageRank cao nhất và cùng được đưa vào kết quả tóm tắt.
- **Hướng khắc phục**: Áp dụng thuật toán chọn câu bằng MMR (Maximal Marginal Relevance) để phạt điểm các câu có độ tương đồng cao với những câu đã được chọn trước đó.

---

### Lỗi 3: Title sinh ra bị sai lệch thông tin địa lý do regex

- **Loại lỗi**: Bóc tách regex địa danh bị trượt hoặc sai ngữ cảnh
- **SystemID gặp lỗi**: [SYS-MP769MZL-CW]
- **Mô tả thô**: `"rạch bùng binh 52 2 4.1 12 7.8 tỷ Nhiêu Lộc Quận 3..."`
- **Title sinh ra**: `"Phú Nhuận - 52.0m² - 7.8 Tỷ - Mặt tiền"` ← **Nhận diện sai Quận thành Phú Nhuận thay vì Quận 3**
- **Nguyên nhân**: Do tin đăng có cấu trúc không chuẩn hóa, regex quét trúng từ khóa định danh quận lân cận hoặc bị sai lệch lookahead do chuỗi kí tự đặc biệt của tin đăng thô.
- **Hướng khắc phục**: Bổ sung bộ từ điển địa chính (Quận/Huyện/Đường phố TP.HCM) để đối soát từ vựng trước khi gán cứng vào Title.

---

## IV. BẢNG XÁC NHẬN DoD

| Tiêu chí DoD | Trạng thái | Ghi chú |
| :--- | :---: | :--- |
| Đã gán đúng SystemID | ✅ Đã Đạt | ID lấy từ `TEST_DATA[*].id` |
| File JSON đầu ra lưu chuẩn mã hóa UTF-8 | ✅ Đã Đạt | `json.dump(..., ensure_ascii=False)` |
| Tuyệt đối không chứa số nhà thật & SĐT | ✅ Đã Đạt | Dữ liệu đầu vào đã được ẩn từ trước |
| Đã tự phân tích đủ 3 lỗi định tính | ✅ Đã Đạt | Mục III ở trên |
| Source code Python | ✅ Đã Đạt | `baseline_lexrank.py` |

---

## V. KẾT LUẬN & VỊ TRÍ BASELINE

LexRank cho thấy hiệu năng cao hơn TextRank một chút ở cả mặt định lượng (ROUGE-L tăng từ 23.17% lên 23.92%) lẫn định tính (Coherence tăng từ 2.97 lên 3.14). Việc lọc ngưỡng tương đồng giúp loại bỏ bớt các câu nhiễu, câu rác biệt lập vốn thường làm suy giảm điểm mạch lạc trong TextRank truyền thống.

Tuy nhiên, là thuật toán trích xuất extractive, LexRank vẫn không thể viết lại câu tự nhiên hay tóm tắt theo phong cách viết quảng cáo sáng tạo như các mô hình sinh (Generative) hay Fine-tuned. Đây vẫn là một mốc baseline quan trọng thứ hai để so sánh với các mô hình học sâu.

> [!NOTE]
> **Chú thích về Specs & Title:** Toàn bộ thông số kỹ thuật (Specs) và tiêu đề (Title) được trích xuất/lập công thức bằng Regular Expressions (Regex) chạy trực tiếp trên **văn bản đã được tóm tắt (Summarized Description)**, chứ không chạy trên văn bản thô gốc. Điều này giúp phản ánh chính xác năng lực bảo toàn thông tin cốt lõi của thuật toán tóm tắt (nếu thuật toán bỏ sót câu chứa diện tích/giá, phần specs và title cũng sẽ không có các thông số đó).


