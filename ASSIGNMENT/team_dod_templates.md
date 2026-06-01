# 📑 TÀI LIỆU UNIFIED DoD, FILE TEMPLATE & HƯỚNG DẪN BÀN GIAO CHI TIẾT
*Dự án FSB-NLP501: Rút Gọn & Chuẩn Hóa Tin Đăng Bất Động Sản Bằng Transformers*

Tài liệu này được thiết kế để chuẩn hóa quy trình làm việc độc lập của 6 thành viên, ban hành các file template nhất quán và tự động hóa khâu tổng hợp dữ liệu cuối cùng của **Trang (Leader)**.

---

## 💾 PHẦN 1: CÁC FILE TEMPLATE TIÊU CHUẨN (DELIVERABLE TEMPLATES)
*Tất cả 5 kỹ sư mô hình bắt buộc phải lưu sản phẩm bàn giao theo đúng định dạng cấu trúc dưới đây.*

### 1. Template file kết quả chuẩn hóa: `[Ten]_predictions.json`
Mỗi bạn tạo 1 file JSON chứa đúng 10 đối tượng tương ứng với 10 căn Test (từ ID 1 đến 10).
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
  },
  {
    "id": 10682,
    "raw_input_cleaned": "Mô tả thô lấy từ cột Mô tả chi tiết của đầu chủ Trà Mi (đã được Trang tiền xử lý sạch địa chỉ và SĐT)...",
    "predicted_title": "Lê Văn Sỹ Tân Bình 42m2 4 lầu 3.8x11 - 8.5 tỷ Hẻm ba gác mới tinh",
    "predicted_description": "Nhà mới dọn vào ở ngay đường Lê Văn Sỹ Tân Bình. Kết cấu 4 lầu đúc BTCT chắc chắn gồm 4 phòng ngủ thoáng mát...",
    "extracted_specs": {
      "duong": "Lê Văn Sỹ",
      "phuong": "Phường 1",
      "quan": "Tân Bình",
      "gia_ty": 8.5,
      "dien_tich_m2": 42.0,
      "so_tang": 4,
      "mat_tien_m": 3.8,
      "rong_hem_m": 3.0,
      "phan_loai_hem": "Hẻm ba gác"
    }
  }
]
```

### 2. Template file nhật ký vận hành: `[Ten]_performance.json`
Mỗi bạn lưu 1 file JSON ghi nhận tốc độ và chi phí của mô hình của mình trên 10 căn test.

```json
{
  "model_name": "ViT5-base / GPT-4o-mini / PhoBERT / TextRank",
  "average_latency_seconds": 0.18,
  "estimated_cost_vnd_per_1k": 0,
  "latency_per_sample": [0.15, 0.22, 0.17, 0.19, 0.20, 0.16, 0.18, 0.17, 0.19, 0.21]
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
6. **Tiêu chí 6: User Preference (Độ thỏa dụng - Chị Trang/Chuyên gia ngành chấm)**: [Để trống cho chị Trang điền điểm Elo/Hạng].

## III. PHÂN TÍCH ĐỊNH TÍNH 3 LỖI ĐIỂN HÌNH (3 QUALITATIVE ERRORS)
Mô tả chi tiết 3 lỗi văn phong hoặc lệch thông số mà mô hình của bạn thường gặp phải trên tập Test:

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

---

## 👤 PHẦN 2: ĐỊNH NGHĨA DoD CHI TIẾT CHO TỪNG THÀNH VIÊN (INDIVIDUAL DoD)

---

### 1. DoD cho NHÂN (Người 2) - Kỹ sư mô hình Baseline (TextRank)
> [!NOTE]
> **Nhiệm vụ cốt lõi**: Cài đặt thuật toán TextRank cổ điển để trích xuất câu tóm tắt làm mốc so sánh (Baseline).

*   **[ ] Bước 1**: Nhận tập Test gồm 10 căn thô (đã ẩn thông tin nhạy cảm) từ Trang.
*   **[ ] Bước 2**: Viết script Python sử dụng thư viện `underthesea` (tách từ tiếng Việt) hoặc `sumy` để chạy thuật toán TextRank/LexRank trích xuất tiêu đề và mô tả.
*   **[ ] Bước 3**: Xuất file kết quả đúng định dạng template `Nhan_Baseline_predictions.json` và file hiệu năng `Nhan_Baseline_performance.json`.
*   **[ ] Bước 4**: Tự đọc kết quả của mình và phân tích **3 lỗi định tính điển hình** (ví dụ: câu bị cụt nghĩa, lặp từ, hoặc giữ lại các specs lộn xộn).
*   **[ ] Bước 5**: Soạn nội dung slide báo cáo riêng gửi Trang: mô tả thuật toán TextRank + 3 lỗi phân tích định tính.

---

### 2. DoD cho QUÂN (Người 3) - Kỹ sư mô hình GPT-4o mini API
> [!NOTE]
> **Nhiệm vụ cốt lõi**: Thiết kế Prompt Few-shot tối ưu và gọi API GPT-4o mini để chuẩn hóa tin.

*   **[ ] Bước 1**: Nhận tập Test (10 căn) và tập ví dụ mẫu Train từ Trang.
*   **[ ] Bước 2**: Thiết kế cấu trúc prompt Few-shot chứa 3 ví dụ mẫu tốt nhất của BDS Khang Ngô để làm mồi cho GPT.
*   **[ ] Bước 3**: Viết code Python gọi API `gpt-4o-mini` trên 10 căn Test, đo đạc thời gian chạy (Latency) của từng request và tính toán tổng chi phí token.
*   **[ ] Bước 4**: Xuất file kết quả `Quan_GPT_predictions.json` và file hiệu năng `Quan_GPT_performance.json`.
*   **[ ] Bước 5**: Phân tích định tính **3 lỗi điển hình của GPT** (ví dụ: thỉnh thoảng bị ảo giác thêm địa danh hoặc viết văn phong quá hào nhoáng kiểu dịch thuật).
*   **[ ] Bước 6**: Soạn nội dung slide báo cáo riêng gửi Trang: Cấu trúc prompt mẫu + Bảng thống kê thời gian/chi phí + 3 lỗi phân tích.

---

### 3. DoD cho HỌC (Người 4) - Kỹ sư mô hình Gemini 1.5 Flash API
> [!NOTE]
> **Nhiệm vụ cốt lõi**: Thiết kế Prompt Few-shot tối ưu và gọi API Gemini 1.5 Flash để chuẩn hóa tin.

*   **[ ] Bước 1**: Nhận tập Test (10 căn) và tập ví dụ mẫu Train từ Trang.
*   **[ ] Bước 2**: Thiết kế cấu trúc prompt Few-shot phù hợp nhất với mô hình Gemini Flash.
*   **[ ] Bước 3**: Viết code Python gọi API `gemini-1.5-flash` trên 10 căn Test, đo đạc thời gian chạy (Latency) và tính toán chi phí token thực tế.
*   **[ ] Bước 4**: Xuất file kết quả `Hoc_Gemini_predictions.json` và file hiệu năng `Hoc_Gemini_performance.json`.
*   **[ ] Bước 5**: Phân tích định tính **3 lỗi điển hình của Gemini** (ví dụ: bị lặp từ hoặc thỉnh thoảng bỏ sót thông số ngang/dài).
*   **[ ] Bước 6**: Soạn nội dung slide báo cáo riêng gửi Trang: Prompt mẫu sử dụng + Bảng thống kê hiệu năng + 3 lỗi phân tích.

---

### 4. DoD cho MAI ANH (Người 5) - Kỹ sư học sâu ViT5 Fine-tuning
> [!NOTE]
> **Nhiệm vụ cốt lõi**: Huấn luyện fine-tune mô hình Seq2Seq chuyên dụng ViT5 trên Google Colab T4.

*   **[ ] Bước 1**: Nhận tập Train (60 căn), Val (10 căn), Test (10 căn) từ Trang.
*   **[ ] Bước 2**: Viết code PyTorch/Hugging Face huấn luyện mô hình `vietnamese-t5-base` trên Colab T4. Dùng tập Val để theo dõi loss tránh Overfitting.
*   **[ ] Bước 3**: Tối ưu hóa giải mã sinh chữ bằng kỹ thuật **Beam Search** trên 10 căn Test để ra kết quả mượt nhất. Ghi nhận thời gian inference cục bộ trên GPU.
*   **[ ] Bước 4**: Xuất file kết quả `MaiAnh_ViT5_predictions.json` và file hiệu năng `MaiAnh_ViT5_performance.json`.
*   **[ ] Bước 5**: Phân tích định tính **3 lỗi của ViT5** (ví dụ: thỉnh thoảng bị lỗi lặp cụm từ ngắn hoặc câu bị lấp lửng).
*   **[ ] Bước 6**: Soạn nội dung slide báo cáo riêng gửi Trang: Các tham số huấn luyện (learning rate, epochs) + Biểu đồ Loss Curve + 3 lỗi phân tích.

---

### 5. DoD cho NHÂN (Người 6) - Kỹ sư học sâu PhoBERT/PhoBERT Fine-tuning
> [!NOTE]
> **Nhiệm vụ cốt lõi**: Huấn luyện fine-tune mô hình PhoBERT/PhoBERT Seq2Seq trên Google Colab T4.

*   **[ ] Bước 1**: Nhận tập Train, Val, Test từ Trang.
*   **[ ] Bước 2**: Viết code Hugging Face huấn luyện mô hình Seq2Seq `vinai/phobert-base` hoặc cấu trúc BERT-Seq2Seq tương đương trên Colab T4.
*   **[ ] Bước 3**: Chạy dự đoán (inference) trên 10 căn Test, đo đạc thời gian xử lý cục bộ trên GPU.
*   **[ ] Bước 4**: Xuất file kết quả `Nhan_PhoBERT_predictions.json` và file hiệu năng `Nhan_PhoBERT_performance.json`.
*   **[ ] Bước 5**: Phân tích định tính **3 lỗi của PhoBERT** (ví dụ: mô hình nặng hơn nên trễ cao hơn, hoặc chia sai token từ ghép).
*   **[ ] Bước 6**: Soạn nội dung slide báo cáo riêng gửi Trang: Biểu đồ Loss Curve + 3 lỗi phân tích.

---

### 6. DoD cho TRANG (Người 1) - Leader, Data Curator & Aggregator
> [!IMPORTANT]
> **Nhiệm vụ cốt lõi**: Chuẩn bị dữ liệu đầu vào sạch, ban hành DoD, chạy script đo ROUGE/Specs tự động và ráp slide tổng hợp cuối cùng.

*   **[ ] Bước 1**: Lọc từ sheet **Pool** các tin đăng của đầu chủ **Trà Mi** (đây là các records có sẵn Ground Truth xuất sắc).
*   **[ ] Bước 2**: Thực hiện tiền xử lý dữ liệu thô (lấy từ cột **Mô tả chi tiết** trong sheet Pool), loại bỏ số nhà và SĐT đầu chủ để làm sạch dữ liệu tại nguồn.
*   **[ ] Bước 3**: Gán **SystemID** làm ID định danh thống nhất cho toàn bộ dataset để so khớp đồng bộ sau này.
*   **[ ] Bước 4**: Chia Train (60) / Val (10) / Test (10) và bàn giao cho nhóm kèm file template JSON và DoD này.
*   **[ ] Bước 5**: Thu nhận các file JSON từ 5 thành viên, chạy script Python `aggregate_results.py` dưới đây để tự động chấm điểm ROUGE-L và Specs Accuracy.
*   **[ ] Bước 6**: Ghép slide riêng của các bạn và slide báo cáo tổng hợp để hoàn thiện đề án thuyết trình.

---

## ⚡ PHẦN 3: SCRIPT PYTHON TỰ ĐỘNG HÓA TỔNG HỢP & ĐÁNH GIÁ (TRANG CHẠY)
*Trang chỉ cần lưu mã nguồn dưới đây thành file `aggregate_results.py` trong cùng thư mục với các file predictions của nhóm.*

> [!TIP]
> Cài đặt thư viện hỗ trợ trước khi chạy: `pip install rouge-score`

```python
# -*- coding: utf-8 -*-
"""
Dự án FSB-NLP501: Script Tự Động Hóa Tổng Hợp & Đánh Giá Điểm ROUGE & Specs Accuracy cho Trang (Leader)
"""

import json
import os
import pandas as pd
from rouge_score import rouge_scorer

# 1. Danh sách các thành viên cần thu thập file kết quả
MEMBERS = {
    "Baseline": "Nhan_Baseline",
    "GPT-4o mini": "Quan_GPT",
    "Gemini Flash": "Hoc_Gemini",
    "ViT5": "MaiAnh_ViT5",
    "PhoBERT": "Nhan_PhoBERT"
}

def calculate_rouge_l(prediction: str, reference: str) -> float:
    """Tính điểm ROUGE-L giữa kết quả mô hình và Ground Truth"""
    scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
    scores = scorer.score(reference, prediction)
    return scores['rougeL'].fmeasure * 100  # Trả về phần trăm %

def calculate_specs_accuracy(pred_specs: dict, ref_specs: dict) -> float:
    """So khớp 9 thông số specs kỹ thuật cốt lõi lấy từ Pool của đầu chủ Trà Mi"""
    if not ref_specs or not pred_specs:
        return 0.0
        
    keys = ["duong", "phuong", "quan", "gia_ty", "dien_tich_m2", "so_tang", "mat_tien_m", "rong_hem_m", "phan_loai_hem"]
    match_count = 0
    total_keys = len(keys)
    
    for k in keys:
        p_val = pred_specs.get(k, None)
        r_val = ref_specs.get(k, None)
        
        if p_val is not None and r_val is not None:
            # Nếu là trường text, chuẩn hóa chuỗi viết thường để so sánh
            if isinstance(r_val, str):
                if str(p_val).strip().lower() == str(r_val).strip().lower():
                    match_count += 1
            else:
                # So sánh dạng số với sai số cực nhỏ 0.01
                try:
                    if abs(float(p_val) - float(r_val)) < 0.01:
                        match_count += 1
                except (ValueError, TypeError):
                    if str(p_val).strip() == str(r_val).strip():
                        match_count += 1
                    
    return (match_count / total_keys) * 100

def aggregate_and_evaluate():
    print("=== ĐANG KHỞI CHẠY HỆ THỐNG TỰ ĐỘNG HÓA ĐÁNH GIÁ (TRANG) ===")
    
    # Đọc file Ground Truth thật (Trang giữ)
    gt_file_path = "ground_truth_test.json"
    if not os.path.exists(gt_file_path):
        print(f"[Cảnh báo] Không tìm thấy file nhãn thật '{gt_file_path}'. Tạo file nhãn mẫu giả lập theo SystemID từ Trà Mi...")
        # Tạo file nhãn mẫu để script không bị crash
        mock_gt = []
        system_ids = [10543, 10682, 10731, 10890, 10921, 11043, 11152, 11234, 11391, 11450]
        for idx, sid in enumerate(system_ids):
            mock_gt.append({
                "id": sid,
                "ground_truth_desc": f"Nhà đúc kiên cố {idx+2} lầu đúc đường Lê Văn Sỹ Phường 1 Tân Bình. Diện tích thực tế {40+idx}m2, mặt tiền rộng {3.5+idx*0.1}m, hẻm trước nhà {3.0+idx*0.2}m thông thoáng. Giá bán {6.0+idx} tỷ.",
                "extracted_specs": {
                    "duong": "Lê Văn Sỹ",
                    "phuong": "Phường 1",
                    "quan": "Tân Bình",
                    "gia_ty": float(6.0+idx),
                    "dien_tich_m2": float(40+idx),
                    "so_tang": idx+2,
                    "mat_tien_m": float(3.5+idx*0.1),
                    "rong_hem_m": float(3.0+idx*0.2),
                    "phan_loai_hem": "Hẻm xe hơi"
                }
            })
        with open(gt_file_path, "w", encoding="utf-8") as f:
            json.dump(mock_gt, f, ensure_ascii=False, indent=2)
            
    with open(gt_file_path, "r", encoding="utf-8") as f:
        ground_truths = json.load(f)
        
    gt_desc_dict = {item["id"]: item.get("ground_truth_desc", "") for item in ground_truths}
    gt_specs_dict = {item["id"]: item.get("extracted_specs", {}) for item in ground_truths}
    
    report_rows = []
    
    # Duyệt qua từng mô hình của các bạn gửi về
    for model_name, file_prefix in MEMBERS.items():
        pred_file = f"{file_prefix}_predictions.json"
        perf_file = f"{file_prefix}_performance.json"
        
        if not os.path.exists(pred_file):
            print(f"[Bỏ qua] Chưa có file bàn giao của {model_name} ({pred_file})")
            continue
            
        print(f"[Đang xử lý] Đang nạp file kết quả của {model_name}...")
        
        # Đọc predictions
        with open(pred_file, "r", encoding="utf-8") as f:
            predictions = json.load(f)
            
        # Đọc hiệu năng (nếu có)
        latency = "N/A"
        cost = "0đ"
        if os.path.exists(perf_file):
            with open(perf_file, "r", encoding="utf-8") as f:
                perf_data = json.load(f)
                latency = f"{perf_data.get('average_latency_seconds', 0):.2f}s"
                cost = f"{perf_data.get('estimated_cost_vnd_per_1k', 0):,}đ"
        
        # Tính ROUGE-L và Specs Accuracy trung bình trên 10 căn
        total_rouge_l = 0.0
        total_specs_acc = 0.0
        count = 0
        for pred in predictions:
            sample_id = pred["id"]
            pred_desc = pred.get("predicted_description", "")
            pred_specs = pred.get("extracted_specs", {})
            
            ref_desc = gt_desc_dict.get(sample_id, "")
            ref_specs = gt_specs_dict.get(sample_id, {})
            
            if ref_desc:
                r_score = calculate_rouge_l(pred_desc, ref_desc)
                s_score = calculate_specs_accuracy(pred_specs, ref_specs)
                
                total_rouge_l += r_score
                total_specs_acc += s_score
                count += 1
                
        avg_rouge_l = (total_rouge_l / count) if count > 0 else 0.0
        avg_specs_acc = (total_specs_acc / count) if count > 0 else 0.0
        
        report_rows.append({
            "Mô Hình": model_name,
            "Thành Viên": file_prefix.split('_')[0],
            "ROUGE-L (TB)": f"{avg_rouge_l:.1f}%",
            "Specs Pres. (TB)": f"{avg_specs_acc:.1f}%",
            "Độ trễ (Latency)": latency,
            "Chi phí (Cost/1k)": cost
        })
        
    # Xuất báo cáo đẹp mắt
    if report_rows:
        df_report = pd.DataFrame(report_rows)
        print("\n" + "="*85)
        print("BẢNG TỔNG HỢP HIỆU NĂNG TỰ ĐỘNG (ĐÃ TÍCH HỢP SPECS ACCURACY):")
        print("="*85)
        print(df_report.to_string(index=False))
        print("="*85)
        
        # Xuất ra file Excel/CSV báo cáo tổng hợp
        df_report.to_csv("summary_leaderboard_report.csv", index=False, encoding="utf-8-sig")
        print("\n[Thành công] Đã xuất bảng xếp hạng tổng hợp tại: 'summary_leaderboard_report.csv'")
    else:
        print("\n[Lưu ý] Chưa có thành viên nào nộp file predictions.json. Trang hãy gom file của các bạn về đây rồi chạy lại nhé!")

if __name__ == "__main__":
    aggregate_and_evaluate()
```
