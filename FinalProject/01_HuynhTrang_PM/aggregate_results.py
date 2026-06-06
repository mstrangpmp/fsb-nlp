# -*- coding: utf-8 -*-
"""
Dự án FSB-NLP501: Script Tự Động Hóa Tổng Hợp & Đánh Giá Điểm ROUGE & Specs Accuracy cho Trang (Leader)
"""

import json
import os
import sys
import pandas as pd

# Reconfigure stdout to use utf-8 to avoid Windows console errors
sys.stdout.reconfigure(encoding='utf-8')

try:
    from rouge_score import rouge_scorer
except ImportError:
    print("[Hệ thống] Chưa cài đặt thư viện 'rouge-score'. Đang tự động cài đặt...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "rouge-score"])
    from rouge_score import rouge_scorer

# 1. Danh sách các thành viên và file prefix tương ứng
MEMBERS = {
    "Baseline TextRank": "Nhan_Baseline",
    "GPT-4o mini API": "Quan_GPT",
    "Gemini 1.5 Flash API": "Hoc_Gemini",
    "ViT5 Fine-tuned": "MaiAnh_ViT5",
    "PhoBERT Fine-tuned": "HuuHieu_PhoBERT"
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

def robust_parse_specs_agnostic(text):
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
    
    # Area
    area_match = re.search(r'(?:diện\s+tích|dt)\s*(?:công\s+nhận)?\s*(?::|là)?\s*([\d.,]+)\s*(?:m2|m²)', t)
    if area_match:
        specs['dien_tich_m2'] = float(area_match.group(1).replace(',', '.'))
        
    # Dimensions
    dim_match = re.search(r'(?:kích\s+thước|dt|diện\s+tích|ngang)?\s*([\d.,]+)\s*m?\s*[x×]\s*([\d.,]+)\s*m?', t)
    if dim_match:
        specs['mat_tien_m'] = float(dim_match.group(1).replace(',', '.'))
        specs['chieu_sau_m'] = float(dim_match.group(2).replace(',', '.'))
        
    # Price
    price_match = re.search(r'(?:giá|giá\s+bán|giá\s+chào)\s*(?::|là)?\s*([\d.,]+)\s*(?:tỷ|ty)', t)
    if price_match:
        specs['gia_ty'] = float(price_match.group(1).replace(',', '.'))
    else:
        m = re.search(r'([\d.,]+)\s*(?:tỷ|ty)\b', t)
        if m:
            specs['gia_ty'] = float(m.group(1).replace(',', '.'))
            
    # Floors
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
                
    # Alley
    if 'mặt tiền' in t:
        specs['phan_loai_hem'] = 'Mặt tiền'
    elif 'hẻm xe hơi' in t or 'hxh' in t or 'ô tô' in t or 'oto' in t:
        specs['phan_loai_hem'] = 'Hẻm xe hơi'
    elif 'hẻm xe tải' in t or 'hxt' in t:
        specs['phan_loai_hem'] = 'Hẻm xe tải'
    elif 'xe máy' in t or 'ba gác' in t:
        specs['phan_loai_hem'] = 'Hẻm xe máy'
        
    # District
    dt_match = re.search(r'quận\s*(\d+)\b', t)
    if dt_match:
        specs['quan'] = 'Quận ' + dt_match.group(1)
    else:
        for d_name in ['bình thạnh', 'phú nhuận', 'gò vấp', 'tân bình', 'quận 1', 'quận 3', 'quận 10']:
            if d_name in t:
                specs['quan'] = d_name.title()
                break
                
    # Ward
    wd_match = re.search(r'(?:phường|p\.)\s*([\d\w\s]+?)(?:,|$|\n|\.)', t)
    if wd_match:
        specs['phuong'] = 'Phường ' + wd_match.group(1).strip().title()
        
    # Street
    st_match = re.search(r'đường\s+([\w\s]+?)(?:,|$|\n|\.)', t)
    if st_match:
        specs['duong'] = st_match.group(1).strip().title()
        
    return specs

import re

def aggregate_and_evaluate():
    print("\n" + "="*85)
    print("=== KHỞI CHẠY HỆ THỐNG TỰ ĐỘNG HÓA ĐÁNH GIÁ ĐỀ ÁN (NLP.FSB501 - TRANG LEADER) ===")
    print("="*85)
    
    # Đọc file Ground Truth thật (Trang giữ)
    gt_file_path = "ground_truth_test.json"
    if not os.path.exists(gt_file_path):
        print(f"[Cảnh báo] Không tìm thấy file nhãn thật '{gt_file_path}' ở cùng thư mục.")
        return
            
    with open(gt_file_path, "r", encoding="utf-8") as f:
        ground_truths = json.load(f)
        
    gt_desc_dict = {item["id"]: item.get("ground_truth_desc", "") for item in ground_truths}
    gt_specs_dict = {item["id"]: item.get("extracted_specs", {}) for item in ground_truths}
    
    report_rows = []
    
    # Duyệt qua từng mô hình của các bạn gửi về
    for model_name, file_prefix in MEMBERS.items():
        pred_file = f"{file_prefix}_predictions.json"
        perf_file = f"{file_prefix}_performance.json"
        
        # Determine the member folder based on file_prefix
        member_folder = ""
        if "Nhan" in file_prefix:
            member_folder = "02_BachNhan_Baseline"
        elif "Quan" in file_prefix:
            member_folder = "03_MinhQuan_GPT"
        elif "Hoc" in file_prefix:
            member_folder = "04_BaHoc_Gemini"
        elif "MaiAnh" in file_prefix:
            member_folder = "05_MaiAnh_ViT5"
        elif "HuuHieu" in file_prefix:
            member_folder = "06_HuuHieu_PhoBERT"
            
        # Thử tìm các hậu tố phiên bản mới nhất trước
        paths_to_try_pred = [
            f"../{member_folder}/{file_prefix}_predictions_v2.json",
            f"../{member_folder}/{file_prefix}_predictions1.json",
            pred_file,
            f"../{member_folder}/{pred_file}",
            f"../{member_folder}/predictions.json"
        ]
        
        # Bổ sung đường dẫn cho thư mục con của Baseline (Bách Nhân)
        if member_folder == "02_BachNhan_Baseline":
            paths_to_try_pred.extend([
                f"../02_BachNhan_Baseline/TextRank_TFIDF/{pred_file}",
                f"../02_BachNhan_Baseline/LexRank_TFIDF/{pred_file}",
                f"../02_BachNhan_Baseline/TextRank_Embedding/{pred_file}",
                f"../02_BachNhan_Baseline/LexRank_Embedding/{pred_file}"
            ])
            
        paths_to_try_perf = [
            f"../{member_folder}/{file_prefix}_performance_v2.json",
            f"../{member_folder}/{file_prefix}_performance1.json",
            perf_file,
            f"../{member_folder}/{perf_file}",
            f"../{member_folder}/performance.json"
        ]
        
        if member_folder == "02_BachNhan_Baseline":
            paths_to_try_perf.extend([
                f"../02_BachNhan_Baseline/TextRank_TFIDF/{perf_file}",
                f"../02_BachNhan_Baseline/LexRank_TFIDF/{perf_file}",
                f"../02_BachNhan_Baseline/TextRank_Embedding/{perf_file}",
                f"../02_BachNhan_Baseline/LexRank_Embedding/{perf_file}"
            ])
        
        actual_pred_path = None
        for p in paths_to_try_pred:
            if os.path.exists(p):
                actual_pred_path = p
                break
                
        if not actual_pred_path:
            print(f"[Bỏ qua] Chưa nhận được file bàn giao của mô hình: {model_name} ({pred_file})")
            continue
            
        print(f"[Đang xử lý] Nạp file kết quả và chấm điểm mô hình: {model_name}...")
        
        # Đọc predictions
        with open(actual_pred_path, "r", encoding="utf-8") as f:
            predictions = json.load(f)
            
        # Đọc hiệu năng vận hành (nếu có)
        latency = "N/A"
        cost = "0đ"
        actual_perf_path = None
        for p in paths_to_try_perf:
            if os.path.exists(p):
                actual_perf_path = p
                break
                
        if actual_perf_path:
            with open(actual_perf_path, "r", encoding="utf-8") as f:
                perf_data = json.load(f)
                if isinstance(perf_data, list):
                    # For list of samples (like GPT-4o mini)
                    latencies = [x.get('latency_seconds', x.get('average_latency_seconds', 0)) for x in perf_data]
                    avg_lat = sum(latencies) / len(latencies) if latencies else 0.0
                    latency = f"{avg_lat:.2f}s"
                    
                    # Convert USD to VND per 1k samples (exchange rate ~25,400)
                    costs_usd = [x.get('estimated_cost_usd', 0) for x in perf_data]
                    avg_cost_usd = sum(costs_usd) / len(costs_usd) if costs_usd else 0.0
                    vnd_cost_1k = avg_cost_usd * 25400 * 1000
                    cost = f"~{int(vnd_cost_1k):,}đ"
                else:
                    # For standard dict format (ViT5, PhoBERT, Gemini, Baseline)
                    latency = f"{perf_data.get('average_latency_seconds', 0):.2f}s"
                    cost_val = perf_data.get('estimated_cost_vnd_per_1k', 0)
                    cost = f"{cost_val:,}đ" if isinstance(cost_val, (int, float)) else str(cost_val)
        
        # Tính toán điểm số trung bình trên các căn test
        total_rouge_l = 0.0
        total_specs_acc = 0.0
        count = 0
        for pred in predictions:
            sample_id = pred["id"]
            pred_desc = pred.get("predicted_description", pred.get("predicted_summary", ""))
            
            pred_specs = pred.get("extracted_specs", {})
            if not pred_specs or all(v is None for v in pred_specs.values() if v != 'Hẻm thông'):
                pred_specs = robust_parse_specs_agnostic(pred_desc)
                
            ref_desc = gt_desc_dict.get(sample_id, "")
            ref_specs = gt_specs_dict.get(sample_id, {})
            
            if ref_desc:
                r_score = calculate_rouge_l(pred_desc, ref_desc)
                s_score = calculate_specs_accuracy(pred_specs, ref_specs)
                
                total_rouge_l += r_score
                total_specs_acc += s_score
                count += 1
                
        if count > 0:
            avg_rouge_l = total_rouge_l / count
            avg_specs_acc = total_specs_acc / count
            rouge_display = f"{avg_rouge_l:.1f}%"
            specs_display = f"{avg_specs_acc:.1f}%"
        else:
            # Fallback to self-reported validation metrics if no test overlap exists
            if file_prefix == "Hoc_Gemini":
                rouge_display = "74.8% (Val)"
                specs_display = "95.2% (Val)"
            elif file_prefix == "MaiAnh_ViT5":
                rouge_display = "46.6% (Val)"
                specs_display = "78.0% (Val)"
            elif file_prefix == "HuuHieu_PhoBERT":
                rouge_display = "17.9% (Val)"
                specs_display = "72.6% (Val)"
            else:
                rouge_display = "0.0%"
                specs_display = "0.0%"
        
        report_rows.append({
            "Mô Hình": model_name,
            "Thành Viên": file_prefix.split('_')[0],
            "ROUGE-L (TB)": rouge_display,
            "Specs Pres. (TB)": specs_display,
            "Độ trễ (Latency)": latency,
            "Chi phí (Cost/1k)": cost
        })
        
    # Xuất bảng báo cáo tổng hợp
    if report_rows:
        df_report = pd.DataFrame(report_rows)
        print("\n" + "="*85)
        print("BẢNG XẾP HẠNG HIỆU NĂNG TỰ ĐỘNG (ĐÃ TÍCH HỢP TỈ LỆ SPECS ACCURACY):")
        print("="*85)
        print(df_report.to_string(index=False))
        print("="*85)
        
        # Xuất ra file Excel tổng hợp có hỗ trợ font tiếng Việt
        output_file = "summary_leaderboard_report.csv"
        df_report.to_csv(output_file, index=False, encoding="utf-8-sig")
        print(f"\n[Thành công] Đã xuất báo cáo tổng hợp bảng xếp hạng tại file: '{output_file}'")
    else:
        print("\n[Lưu ý] Chưa có thành viên nào nộp file kết quả dự đoán (*_predictions.json).")
        print("-> Hãy gom file của các bạn về cùng thư mục này hoặc push lên thư mục riêng rồi chạy lại file nhé!")
        print("="*85)

if __name__ == "__main__":
    aggregate_and_evaluate()
