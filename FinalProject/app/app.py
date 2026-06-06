# -*- coding: utf-8 -*-
"""
Dự án FSB-NLP501: Backend Ứng dụng Web Showcase & Đánh giá Bất động sản NLP (Tiếng Việt)
"""

import os
import json
import re
import time
import sys
from flask import Flask, render_template, jsonify, request

# Đảm bảo console và stdout sử dụng UTF-8 để hiển thị tiếng Việt chính xác
sys.stdout.reconfigure(encoding='utf-8')

app = Flask(__name__)

# ══════════════════════════════════════════════════════════════════════════════
# 1. ĐƯỜNG DẪN DỮ LIỆU GỐC CỦA NHÓM
# ══════════════════════════════════════════════════════════════════════════════
# Xác định BASE_DIR động để chạy được trên mọi máy sau khi clone
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)
PM_DIR = os.path.join(BASE_DIR, "01_HuynhTrang_PM")
APP_DIR = os.path.join(BASE_DIR, "app")

PATHS = {
    "Baseline": {
        "pred": os.path.join(BASE_DIR, "02_BachNhan_Baseline/TextRank_TFIDF/Nhan_Baseline_predictions.json"),
        "perf": os.path.join(BASE_DIR, "02_BachNhan_Baseline/TextRank_TFIDF/Nhan_Baseline_performance.json")
    },
    "GPT": {
        "pred": os.path.join(BASE_DIR, "03_MinhQuan_GPT/predictions.json"),
        "perf": os.path.join(BASE_DIR, "03_MinhQuan_GPT/performance.json")
    },
    "Gemini": {
        "pred": os.path.join(BASE_DIR, "04_BaHoc_Gemini/Hoc_Gemini_predictions.json"),
        "perf": os.path.join(BASE_DIR, "04_BaHoc_Gemini/Hoc_Gemini_performance.json")
    },
    "ViT5": {
        "pred": os.path.join(BASE_DIR, "05_MaiAnh_ViT5/MaiAnh_ViT5_predictions_v2.json"),
        "perf": os.path.join(BASE_DIR, "05_MaiAnh_ViT5/MaiAnh_ViT5_performance_v2.json")
    },
    "PhoBERT": {
        "pred": os.path.join(BASE_DIR, "06_HuuHieu_PhoBERT/HuuHieu_PhoBERT_predictions1.json"),
        "perf": os.path.join(BASE_DIR, "06_HuuHieu_PhoBERT/HuuHieu_PhoBERT_performance1.json")
    }
}

TEST_DATASET_PATH = os.path.join(PM_DIR, "test_dataset.json")

# Danh sách 9 mã System ID kiểm thử cốt lõi
TEST_IDS = [
    "SYS-MP75Z7G0-H3",
    "SYS-MP75ZR8R-C4",
    "SYS-MP760LYQ-AC",
    "SYS-MP760YOH-BW",
    "SYS-MP761FGI-DF",
    "SYS-MP762B6J-5",
    "SYS-MP7634YK-9F",
    "SYS-MP7635C7-K7",
    "SYS-MP7637OS-RJ"
]

# File lưu trữ cục bộ của người dùng (nằm tại app/)
USER_GT_FILE = os.path.join(APP_DIR, "user_ground_truth.json")
EXPERT_REVIEWS_FILE = os.path.join(APP_DIR, "expert_reviews.json")

# Đảm bảo thư mục app tồn tại
os.makedirs(APP_DIR, exist_ok=True)

# Khởi tạo các file lưu trữ cục bộ nếu chưa có
if not os.path.exists(USER_GT_FILE):
    with open(USER_GT_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=4)

if not os.path.exists(EXPERT_REVIEWS_FILE):
    with open(EXPERT_REVIEWS_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=4)

# Thử import rouge-score để tự động tính điểm từ vựng
try:
    from rouge_score import rouge_scorer
    HAS_ROUGE = True
except ImportError:
    HAS_ROUGE = False
    print("[Hệ thống] Chưa cài đặt 'rouge-score'. Backend sẽ dùng hàm tính khoảng cách tạm thời.")

# ══════════════════════════════════════════════════════════════════════════════
# 2. CÁC HÀM XỬ LÝ TOÁN HỌC & LOGIC ĐỐI CHIẾU
# ══════════════════════════════════════════════════════════════════════════════

def robust_parse_specs_agnostic(text):
    """Trích xuất 9 trường thông số từ văn bản mô tả nếu mô hình bị thiếu specs"""
    if not text or not isinstance(text, str):
        return {
            'duong': None, 'phuong': None, 'quan': None,
            'gia_ty': None, 'dien_tich_m2': None, 'so_tang': None,
            'mat_tien_m': None, 'chieu_sau_m': None, 'phan_loai_hem': 'Hẻm thông'
        }
        
    t = text.lower().replace('*', '').replace('#', '')
    specs = {
        'duong': None, 'phuong': None, 'quan': None,
        'gia_ty': None, 'dien_tich_m2': None, 'so_tang': None,
        'mat_tien_m': None, 'chieu_sau_m': None, 'phan_loai_hem': 'Hẻm thông'
    }
    
    # 1. Diện tích (dien_tich_m2)
    area_match = re.search(r'(?:diện\s+tích|dt|dt\s+đất|công\s+nhận)\s*(?::|là)?\s*([\d.,]+)\s*(?:m2|m²)', t)
    if area_match:
        try:
            specs['dien_tich_m2'] = float(area_match.group(1).replace(',', '.'))
        except ValueError:
            pass
            
    # 2. Kích thước (ngang x dài)
    dim_match = re.search(r'(?:kích\s+thước|ngang|dài)?\s*([\d.,]+)\s*m?\s*[x×]\s*([\d.,]+)\s*m?', t)
    if dim_match:
        try:
            specs['mat_tien_m'] = float(dim_match.group(1).replace(',', '.'))
            specs['chieu_sau_m'] = float(dim_match.group(2).replace(',', '.'))
        except ValueError:
            pass
            
    # 3. Giá bán (gia_ty)
    price_match = re.search(r'(?:giá|giá\s+bán|giá\s+chào)\s*(?::|là)?\s*([\d.,]+)\s*(?:tỷ|ty)', t)
    if price_match:
        try:
            specs['gia_ty'] = float(price_match.group(1).replace(',', '.'))
        except ValueError:
            pass
    else:
        m = re.search(r'([\d.,]+)\s*(?:tỷ|ty)\b', t)
        if m:
            try:
                specs['gia_ty'] = float(m.group(1).replace(',', '.'))
            except ValueError:
                pass
                
    # 4. Số tầng (so_tang)
    floors_match = re.search(r'(?:kết\s+cấu|quy\s+mô|nhà)?\s*(?::|là)?\s*(\d+)\s*(?:tầng|lầu)', t)
    if floors_match:
        specs['so_tang'] = int(floors_match.group(1))
    else:
        m = re.search(r'(\d+)\s*trệt\s*(?:và|[,+])?\s*(\d+)\s*(?:lầu|lửng)', t)
        if m:
            specs['so_tang'] = int(m.group(1)) + int(m.group(2))
        else:
            m = re.search(r'trệt\s*(?:và|[,+])?\s*(\d+)\s*lầu', t)
            if m:
                specs['so_tang'] = 1 + int(m.group(1))
                
    # 5. Phân loại hẻm (phan_loai_hem)
    if 'mặt tiền' in t:
        specs['phan_loai_hem'] = 'Mặt tiền'
    elif 'hẻm xe hơi' in t or 'hxh' in t or 'ô tô' in t or 'oto' in t:
        specs['phan_loai_hem'] = 'Hẻm xe hơi'
    elif 'hẻm xe tải' in t or 'hxt' in t:
        specs['phan_loai_hem'] = 'Hẻm xe tải'
    elif 'xe máy' in t or 'ba gác' in t:
        specs['phan_loai_hem'] = 'Hẻm xe máy'
        
    # 6. Quận (quan)
    dt_match = re.search(r'quận\s*(\d+)\b', t)
    if dt_match:
        specs['quan'] = 'Quận ' + dt_match.group(1)
    else:
        for d_name in ['bình thạnh', 'phú nhuận', 'gò vấp', 'tân bình', 'quận 1', 'quận 3', 'quận 10']:
            if d_name in t:
                specs['quan'] = d_name.title()
                break
                
    # 7. Phường (phuong)
    wd_match = re.search(r'(?:phường|p\.)\s*([\d\w\s]+?)(?:,|$|\n|\.)', t)
    if wd_match:
        specs['phuong'] = 'Phường ' + wd_match.group(1).strip().title()
        
    # 8. Tên đường (duong)
    st_match = re.search(r'đường\s+([\w\s]+?)(?:,|$|\n|\.)', t)
    if st_match:
        specs['duong'] = st_match.group(1).strip().title()
        
    return specs


def calculate_rouge_l(pred_text: str, ref_text: str) -> float:
    """Tính điểm tương đồng từ vựng ROUGE-L"""
    if not pred_text or not ref_text:
        return 0.0
    if not HAS_ROUGE:
        # Fallback đơn giản nếu không cài rouge-score
        w_pred = set(pred_text.lower().split())
        w_ref = set(ref_text.lower().split())
        intersection = w_pred.intersection(w_ref)
        if not w_pred or not w_ref:
            return 0.0
        r = len(intersection) / len(w_ref)
        p = len(intersection) / len(w_pred)
        if r + p == 0:
            return 0.0
        return (2 * r * p / (r + p)) * 100
        
    scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
    scores = scorer.score(ref_text, pred_text)
    return scores['rougeL'].fmeasure * 100


def normalize_vietnamese(s):
    if not s or not isinstance(s, str):
        return ""
    import unicodedata
    s = unicodedata.normalize("NFC", s.lower().strip())
    replacements = {
        "òe": "oè", "óe": "oé", "ỏe": "oẻ", "õe": "oẽ", "ọe": "oẹ",
        "òa": "oà", "óa": "oá", "ỏa": "oả", "õa": "oã", "ọa": "oạ",
        "ùy": "uỳ", "úy": "uý", "ủy": "uỷ", "ũy": "uỹ", "ụy": "uỵ"
    }
    for k, v in replacements.items():
        s = s.replace(k, v)
    return s


def calculate_specs_accuracy(pred_specs: dict, ref_specs: dict) -> float:
    """Tính điểm Specs Accuracy bằng cách so khớp chính xác 9 thông số kỹ thuật"""
    if not ref_specs or not pred_specs:
        return 0.0
        
    keys = ["duong", "phuong", "quan", "gia_ty", "dien_tich_m2", "so_tang", "mat_tien_m", "chieu_sau_m", "phan_loai_hem"]
    match_count = 0
    total_keys = len(keys)
    
    for k in keys:
        p_val = pred_specs.get(k, None)
        r_val = ref_specs.get(k, None)
        
        # Nếu cả hai đều là rỗng thì tính là khớp
        if p_val is None and r_val is None:
            match_count += 1
            continue
            
        if p_val is not None and r_val is not None:
            if isinstance(r_val, str):
                if normalize_vietnamese(str(p_val)) == normalize_vietnamese(str(r_val)):
                    match_count += 1
            else:
                try:
                    if abs(float(p_val) - float(r_val)) < 0.01:
                        match_count += 1
                except (ValueError, TypeError):
                    if str(p_val).strip() == str(r_val).strip():
                        match_count += 1
                        
    return (match_count / total_keys) * 100


# ══════════════════════════════════════════════════════════════════════════════
# 3. ROUTE ĐIỀU HƯỚNG VÀ APIS
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/')
def index():
    """Renders trang giao diện chính của ứng dụng"""
    return render_template('index.html')


@app.route('/get_test_samples', methods=['GET'])
def get_test_samples():
    """Lấy danh sách 9 căn nhà mẫu trong tập kiểm thử"""
    if not os.path.exists(TEST_DATASET_PATH):
        return jsonify({"status": "error", "message": "Không tìm thấy file test_dataset.json"}), 404
        
    with open(TEST_DATASET_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    samples = []
    for item in data:
        iid = item.get("id") or item.get("ID")
        if iid in TEST_IDS:
            raw = item.get("raw_input_cleaned", "")
            first_line = raw.strip().splitlines()[0] if raw.strip() else iid
            # Cắt ngắn tiêu đề nếu quá dài
            label = f"{iid} - {first_line[:55]}..." if len(first_line) > 55 else f"{iid} - {first_line}"
            samples.append({
                "id": iid,
                "label": label,
                "raw_input": raw
            })
            
    # Sắp xếp đúng theo thứ tự TEST_IDS đã định nghĩa
    samples.sort(key=lambda x: TEST_IDS.index(x["id"]))
    return jsonify(samples)


@app.route('/get_sample_data/<sample_id>', methods=['GET'])
def get_sample_data(sample_id):
    """Trả về kết quả, hiệu năng và Ground Truth của 5 mô hình cho căn nhà được chọn"""
    if sample_id not in TEST_IDS:
        return jsonify({"status": "error", "message": "Mã ID không hợp lệ trong tập kiểm thử"}), 400

    # 1. Đọc tin thô
    raw_input = ""
    with open(TEST_DATASET_PATH, 'r', encoding='utf-8') as f:
        test_data = json.load(f)
        for item in test_data:
            if (item.get("id") or item.get("ID")) == sample_id:
                raw_input = item.get("raw_input_cleaned", "")
                break

    # 2. Đọc Ground Truth đã lưu của người dùng
    user_gt = {}
    if os.path.exists(USER_GT_FILE):
        with open(USER_GT_FILE, 'r', encoding='utf-8') as f:
            all_gt = json.load(f)
            user_gt = all_gt.get(sample_id, {
                "ground_truth_title": "",
                "ground_truth_desc": "",
                "extracted_specs": {
                    "duong": None, "phuong": None, "quan": None,
                    "gia_ty": None, "dien_tich_m2": None, "so_tang": None,
                    "mat_tien_m": None, "chieu_sau_m": None, "phan_loai_hem": "Hẻm thông"
                }
            })

    # 3. Trích xuất kết quả dự đoán của 5 mô hình
    model_data = {}
    for model_name, files in PATHS.items():
        if not os.path.exists(files["pred"]) or not os.path.exists(files["perf"]):
            continue
            
        with open(files["pred"], 'r', encoding='utf-8') as f:
            preds = json.load(f)
        with open(files["perf"], 'r', encoding='utf-8') as f:
            perf = json.load(f)
            
        # Tìm index tương ứng của sample_id
        pred_idx = -1
        pred_item = None
        for i, item in enumerate(preds):
            if (item.get("id") or item.get("ID")) == sample_id:
                pred_idx = i
                pred_item = item
                break
                
        if pred_item is None:
            continue

        # Phân tích tiêu đề và mô tả
        title = pred_item.get("predicted_title", "").strip()
        desc = pred_item.get("predicted_description", pred_item.get("predicted_summary", "")).strip()
        
        # Nếu là GPT-4o mini, chia tiêu đề và mô tả từ predicted_summary
        if model_name == "GPT" and "Mô tả chuẩn:" in desc:
            # Tách tiêu đề từ hàng đầu tiên
            lines = desc.splitlines()
            title_candidate = ""
            desc_lines = []
            for line in lines:
                clean_l = line.strip().replace("**", "").replace("#", "")
                if not title_candidate and clean_l and clean_l != "Mô tả chuẩn:":
                    title_candidate = clean_l
                elif title_candidate or (clean_l and clean_l != "Mô tả chuẩn:"):
                    desc_lines.append(line)
            title = title_candidate
            desc = "\n".join(desc_lines).strip()

        # Trích xuất thông số
        specs = pred_item.get("extracted_specs", {})
        if not specs or all(v is None for v in specs.values() if v != 'Hẻm thông'):
            specs = robust_parse_specs_agnostic(desc)
            
        # Lấy độ trễ (latency) và chi phí
        latency = 0.0
        cost = "0đ"
        
        if model_name == "Baseline":
            latencies = perf.get("latency_per_sample", [])
            if pred_idx != -1 and pred_idx < len(latencies):
                latency = latencies[pred_idx]
            cost = "0đ (Offline)"
        elif model_name == "GPT":
            for p_item in perf:
                if (p_item.get("id") or p_item.get("ID")) == sample_id:
                    latency = p_item.get("latency_seconds", 0.0)
                    cost_usd = p_item.get("estimated_cost_usd", 0.0)
                    cost = f"~{int(cost_usd * 25400):,}đ"
                    break
        elif model_name == "Gemini":
            latencies = perf.get("latency_per_sample", [])
            if pred_idx != -1 and pred_idx < len(latencies):
                latency = latencies[pred_idx]
            cost_val = perf.get("estimated_cost_vnd_per_1k", 0)
            cost = f"~{int(cost_val / 1000)}đ"
        elif model_name in ["ViT5", "PhoBERT"]:
            latencies = perf.get("latency_per_sample", [])
            if pred_idx != -1 and pred_idx < len(latencies):
                latency = latencies[pred_idx]
            cost = "0đ (Offline/Colab)"

        # BERTScore tham khảo (lấy từ báo cáo trung bình của nhóm)
        bertscore = 83.98  # Baseline
        if model_name == "GPT":
            bertscore = 92.40
        elif model_name == "Gemini":
            bertscore = 90.15
        elif model_name == "ViT5":
            bertscore = 82.50
        elif model_name == "PhoBERT":
            bertscore = 80.12

        # Tính toán điểm động ROUGE-L và Specs Accuracy nếu đã có Ground Truth của người dùng
        rouge_l = 0.0
        specs_acc = 0.0
        if user_gt and user_gt.get("ground_truth_desc"):
            rouge_l = calculate_rouge_l(desc, user_gt["ground_truth_desc"])
            specs_acc = calculate_specs_accuracy(specs, user_gt["extracted_specs"])

        model_data[model_name] = {
            "model_name": model_name,
            "title": title,
            "description": desc,
            "specs": specs,
            "latency": latency,
            "cost": cost,
            "bertscore": bertscore,
            "rouge_l": rouge_l,
            "specs_acc": specs_acc
        }

    # Đọc xếp hạng Winner đã lưu cho căn này (nếu có)
    saved_review = {}
    if os.path.exists(EXPERT_REVIEWS_FILE):
        with open(EXPERT_REVIEWS_FILE, 'r', encoding='utf-8') as f:
            reviews = json.load(f)
            for rev in reviews:
                if rev.get("id") == sample_id:
                    saved_review = rev
                    break

    return jsonify({
        "id": sample_id,
        "raw_input": raw_input,
        "ground_truth": user_gt,
        "models": model_data,
        "review": saved_review
    })


@app.route('/calculate_metrics', methods=['POST'])
def calculate_metrics():
    """Lưu Ground Truth của người dùng và tính lại các chỉ số ROUGE-L & Specs Acc cho 5 mô hình"""
    req_data = request.get_json()
    sample_id = req_data.get("id")
    gt_title = req_data.get("ground_truth_title", "").strip()
    gt_desc = req_data.get("ground_truth_desc", "").strip()
    gt_specs = req_data.get("extracted_specs", {})
    
    if not sample_id or sample_id not in TEST_IDS:
        return jsonify({"status": "error", "message": "ID không hợp lệ"}), 400

    # 1. Lưu Ground Truth mới
    with open(USER_GT_FILE, 'r', encoding='utf-8') as f:
        all_gt = json.load(f)
        
    all_gt[sample_id] = {
        "ground_truth_title": gt_title,
        "ground_truth_desc": gt_desc,
        "extracted_specs": gt_specs
    }
    
    with open(USER_GT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_gt, f, ensure_ascii=False, indent=4)

    # 2. Tính lại các chỉ số cho từng mô hình
    updated_metrics = {}
    for model_name, files in PATHS.items():
        if not os.path.exists(files["pred"]):
            continue
        with open(files["pred"], 'r', encoding='utf-8') as f:
            preds = json.load(f)
            
        pred_item = None
        for item in preds:
            if (item.get("id") or item.get("ID")) == sample_id:
                pred_item = item
                break
                
        if not pred_item:
            continue
            
        desc = pred_item.get("predicted_description", pred_item.get("predicted_summary", "")).strip()
        # Đối với GPT-4o mini, bỏ tiền tố tiêu đề nếu có
        if model_name == "GPT" and "Mô tả chuẩn:" in desc:
            lines = desc.splitlines()
            desc_lines = []
            title_candidate = ""
            for line in lines:
                clean_l = line.strip().replace("**", "").replace("#", "")
                if not title_candidate and clean_l and clean_l != "Mô tả chuẩn:":
                    title_candidate = clean_l
                elif title_candidate or (clean_l and clean_l != "Mô tả chuẩn:"):
                    desc_lines.append(line)
            desc = "\n".join(desc_lines).strip()

        specs = pred_item.get("extracted_specs", {})
        if not specs or all(v is None for v in specs.values() if v != 'Hẻm thông'):
            specs = robust_parse_specs_agnostic(desc)
            
        rouge_l = calculate_rouge_l(desc, gt_desc)
        specs_acc = calculate_specs_accuracy(specs, gt_specs)
        
        updated_metrics[model_name] = {
            "rouge_l": rouge_l,
            "specs_acc": specs_acc
        }
        
    return jsonify({
        "status": "success",
        "message": "Đã cập nhật Ground Truth và tính lại chỉ số!",
        "metrics": updated_metrics
    })


@app.route('/save_review', methods=['POST'])
def save_review():
    """Lưu đánh giá xếp hạng Winner 1, 2, 3 của chuyên gia"""
    req_data = request.get_json()
    sample_id = req_data.get("id")
    winner_1 = req_data.get("winner_1", "")
    winner_2 = req_data.get("winner_2", "")
    winner_3 = req_data.get("winner_3", "")
    comment = req_data.get("comment", "").strip()
    
    if not sample_id or sample_id not in TEST_IDS:
        return jsonify({"status": "error", "message": "ID mẫu không hợp lệ"}), 400

    # Đọc danh sách đánh giá cũ
    with open(EXPERT_REVIEWS_FILE, 'r', encoding='utf-8') as f:
        reviews = json.load(f)

    # Cập nhật hoặc thêm mới đánh giá
    found = False
    for rev in reviews:
        if rev.get("id") == sample_id:
            rev["winner_1"] = winner_1
            rev["winner_2"] = winner_2
            rev["winner_3"] = winner_3
            rev["comment"] = comment
            rev["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
            found = True
            break
            
    if not found:
        reviews.append({
            "id": sample_id,
            "winner_1": winner_1,
            "winner_2": winner_2,
            "winner_3": winner_3,
            "comment": comment,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        })

    # Lưu lại
    with open(EXPERT_REVIEWS_FILE, 'w', encoding='utf-8') as f:
        json.dump(reviews, f, ensure_ascii=False, indent=4)

    return jsonify({"status": "success", "message": "Đã lưu đánh giá của chuyên gia thành công!"})


@app.route('/get_reviews_summary', methods=['GET'])
def get_reviews_summary():
    """Tổng hợp điểm số xếp hạng và điểm tự động của 5 mô hình để vẽ bảng xếp hạng"""
    # Khởi tạo bảng tổng hợp
    summary = {
        "Baseline": {"points": 0, "rank_1": 0, "rank_2": 0, "rank_3": 0, "reviews_count": 0, "rouge_sum": 0.0, "specs_sum": 0.0, "bert_sum": 83.98, "latency_sum": 0.0, "cost_sum": 100.0},
        "GPT": {"points": 0, "rank_1": 0, "rank_2": 0, "rank_3": 0, "reviews_count": 0, "rouge_sum": 0.0, "specs_sum": 0.0, "bert_sum": 92.40, "latency_sum": 0.0, "cost_sum": 85.0},
        "Gemini": {"points": 0, "rank_1": 0, "rank_2": 0, "rank_3": 0, "reviews_count": 0, "rouge_sum": 0.0, "specs_sum": 0.0, "bert_sum": 90.15, "latency_sum": 0.0, "cost_sum": 90.0},
        "ViT5": {"points": 0, "rank_1": 0, "rank_2": 0, "rank_3": 0, "reviews_count": 0, "rouge_sum": 0.0, "specs_sum": 0.0, "bert_sum": 82.50, "latency_sum": 0.0, "cost_sum": 100.0},
        "PhoBERT": {"points": 0, "rank_1": 0, "rank_2": 0, "rank_3": 0, "reviews_count": 0, "rouge_sum": 0.0, "specs_sum": 0.0, "bert_sum": 80.12, "latency_sum": 0.0, "cost_sum": 100.0}
    }

    # 1. Đọc xếp hạng của chuyên gia để tính điểm tích lũy
    with open(EXPERT_REVIEWS_FILE, 'r', encoding='utf-8') as f:
        reviews = json.load(f)
        
    for rev in reviews:
        w1 = rev.get("winner_1")
        w2 = rev.get("winner_2")
        w3 = rev.get("winner_3")
        
        if w1 in summary:
            summary[w1]["points"] += 3
            summary[w1]["rank_1"] += 1
        if w2 in summary:
            summary[w2]["points"] += 2
            summary[w2]["rank_2"] += 1
        if w3 in summary:
            summary[w3]["points"] += 1
            summary[w3]["rank_3"] += 1

    # 2. Đọc Ground Truth của người dùng để tính trung bình ROUGE-L và Specs Acc động
    with open(USER_GT_FILE, 'r', encoding='utf-8') as f:
        all_gt = json.load(f)

    # Tìm các mẫu đã có Ground Truth hợp lệ (có phần mô tả khác rỗng)
    evaluated_ids = [iid for iid, gt in all_gt.items() if gt.get("ground_truth_desc") and iid in TEST_IDS]
    evaluated_count = len(evaluated_ids)

    # Đọc tất cả predictions và performance để tính trung bình cộng ROUGE-L, Specs Accuracy, Latency
    for model_name, files in PATHS.items():
        if not os.path.exists(files["pred"]) or not os.path.exists(files["perf"]):
            continue
            
        with open(files["pred"], 'r', encoding='utf-8') as f:
            preds = json.load(f)
        with open(files["perf"], 'r', encoding='utf-8') as f:
            perf = json.load(f)

        # Xây dựng index mapping
        id_to_idx = {}
        for i, item in enumerate(preds):
            id_to_idx[item.get("id") or item.get("ID")] = i

        latency_total = 0.0
        count_lat = 0
        
        # Lấy latency trung bình trên 9 căn kiểm thử
        for tid in TEST_IDS:
            idx = id_to_idx.get(tid, -1)
            if idx == -1:
                continue
            
            # Tính độ trễ từng căn
            if model_name == "Baseline":
                latencies = perf.get("latency_per_sample", [])
                if idx < len(latencies):
                    latency_total += latencies[idx]
                    count_lat += 1
            elif model_name == "GPT":
                for p_item in perf:
                    if (p_item.get("id") or p_item.get("ID")) == tid:
                        latency_total += p_item.get("latency_seconds", 0.0)
                        count_lat += 1
                        break
            elif model_name in ["Gemini", "ViT5", "PhoBERT"]:
                latencies = perf.get("latency_per_sample", [])
                if idx < len(latencies):
                    latency_total += latencies[idx]
                    count_lat += 1

        avg_latency = latency_total / count_lat if count_lat > 0 else 1.0
        # Chuẩn hóa tốc độ Latency về thang điểm 100: Latency = 0s -> 100đ, Latency >= 10s -> 0đ
        summary[model_name]["latency_sum"] = max(0.0, 100.0 - avg_latency * 10.0)

        # Tính ROUGE-L và Specs Acc trung bình cộng trên các căn đã biên tập Ground Truth
        for tid in evaluated_ids:
            idx = id_to_idx.get(tid, -1)
            if idx == -1:
                continue
            pred_item = preds[idx]
            desc = pred_item.get("predicted_description", pred_item.get("predicted_summary", "")).strip()
            
            # Trích xuất tiêu đề cho GPT
            if model_name == "GPT" and "Mô tả chuẩn:" in desc:
                lines = desc.splitlines()
                desc_lines = []
                title_candidate = ""
                for line in lines:
                    clean_l = line.strip().replace("**", "").replace("#", "")
                    if not title_candidate and clean_l and clean_l != "Mô tả chuẩn:":
                        title_candidate = clean_l
                    elif title_candidate or (clean_l and clean_l != "Mô tả chuẩn:"):
                        desc_lines.append(line)
                desc = "\n".join(desc_lines).strip()

            specs = pred_item.get("extracted_specs", {})
            if not specs or all(v is None for v in specs.values() if v != 'Hẻm thông'):
                specs = robust_parse_specs_agnostic(desc)
                
            gt_item = all_gt[tid]
            r_score = calculate_rouge_l(desc, gt_item["ground_truth_desc"])
            s_score = calculate_specs_accuracy(specs, gt_item["extracted_specs"])
            
            summary[model_name]["rouge_sum"] += r_score
            summary[model_name]["specs_sum"] += s_score

    # 3. Tạo báo cáo tổng hợp chuẩn hóa
    report = []
    total_reviews = len(reviews)
    
    for model_name, data in summary.items():
        avg_rouge = data["rouge_sum"] / evaluated_count if evaluated_count > 0 else 0.0
        avg_specs = data["specs_sum"] / evaluated_count if evaluated_count > 0 else 0.0
        
        # Điểm thỏa dụng của anh Khang chuẩn hóa về thang điểm 100
        # Nếu tổng số căn được anh Khang xếp hạng > 0, chuẩn hóa tổng điểm
        # (Tổng điểm tối đa của 1 căn là 3 điểm cho giải nhất)
        points_denominator = total_reviews * 3
        s_expert = (data["points"] / points_denominator * 100) if points_denominator > 0 else 0.0
        
        s_specs = avg_specs
        s_bert = data["bert_sum"] # Dùng giá trị trung bình lịch sử
        s_rouge = avg_rouge
        s_latency = data["latency_sum"]
        s_cost = data["cost_sum"]
        
        # Công thức tính Điểm Tổng Hợp:
        # Overall = 35% Expert + 25% Specs + 15% BERTScore + 15% ROUGE-L + 5% Latency + 5% Cost
        overall_score = (
            0.35 * s_expert +
            0.25 * s_specs +
            0.15 * s_bert +
            0.15 * s_rouge +
            0.05 * s_latency +
            0.05 * s_cost
        )
        
        # Lấy latency trung bình thực tế để hiển thị
        real_latency = 0.0
        if model_name == "Baseline":
            real_latency = 0.007
        elif model_name == "GPT":
            real_latency = 6.22
        elif model_name == "Gemini":
            real_latency = 1.85
        elif model_name == "ViT5":
            real_latency = 2.31
        elif model_name == "PhoBERT":
            real_latency = 0.88

        report.append({
            "model_name": model_name,
            "points": data["points"],
            "rank_1": data["rank_1"],
            "rank_2": data["rank_2"],
            "rank_3": data["rank_3"],
            "avg_rouge": round(avg_rouge, 2),
            "avg_specs": round(avg_specs, 2),
            "avg_bert": round(s_bert, 2),
            "latency": f"{real_latency:.3f}s",
            "overall_score": round(overall_score, 2)
        })
        
    # Sắp xếp bảng xếp hạng theo Điểm Tổng Hợp giảm dần
    report.sort(key=lambda x: x["overall_score"], reverse=True)
    
    return jsonify({
        "evaluated_count": evaluated_count,
        "total_reviews": total_reviews,
        "leaderboard": report
    })

@app.after_request
def add_header(r):
    """
    Thêm headers để vô hiệu hóa cache trình duyệt đối với các API response,
    đảm bảo dữ liệu mới nhất được nạp lại sau mỗi lần lưu Ground Truth.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    return r

if __name__ == '__main__':
    app.run(debug=True, port=5000)
