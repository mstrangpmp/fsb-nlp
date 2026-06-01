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
    "PhoBERT Fine-tuned": "Hieu_PhoBERT"
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
    print("\n" + "="*85)
    print("=== KHỞI CHẠY HỆ THỐNG TỰ ĐỘNG HÓA ĐÁNH GIÁ ĐỀ ÁN (NLP.FSB501 - TRANG LEADER) ===")
    print("="*85)
    
    # Đọc file Ground Truth thật (Trang giữ)
    gt_file_path = "ground_truth_test.json"
    if not os.path.exists(gt_file_path):
        print(f"[Cảnh báo] Không tìm thấy file nhãn thật '{gt_file_path}'.")
        print("-> Đang tự động tạo file nhãn mẫu 'ground_truth_test.json' giả lập theo 9 SystemID tập Test để chạy demo...")
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
            print(f"[Bỏ qua] Chưa nhận được file bàn giao của mô hình: {model_name} ({pred_file})")
            continue
            
        print(f"[Đang xử lý] Nạp file kết quả và chấm điểm mô hình: {model_name}...")
        
        # Đọc predictions
        with open(pred_file, "r", encoding="utf-8") as f:
            predictions = json.load(f)
            
        # Đọc hiệu năng vận hành (nếu có)
        latency = "N/A"
        cost = "0đ"
        if os.path.exists(perf_file):
            with open(perf_file, "r", encoding="utf-8") as f:
                perf_data = json.load(f)
                latency = f"{perf_data.get('average_latency_seconds', 0):.2f}s"
                cost = f"{perf_data.get('estimated_cost_vnd_per_1k', 0):,}đ"
        
        # Tính toán điểm số trung bình trên các căn test
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
        
    # Xuất bảng báo cáo tổng hợp
    if report_rows:
        df_report = pd.DataFrame(report_rows)
        print("\n" + "="*85)
        print("BẢNG XẾP HẠNG HIỆU NĂNG TỰ ĐỘNG (ĐÃ TÍCH HỢP TỈ LỆ specs accuracy):")
        print("="*85)
        print(df_report.to_string(index=False))
        print("="*85)
        
        # Xuất ra file Excel tổng hợp có hỗ trợ font tiếng Việt
        output_file = "summary_leaderboard_report.csv"
        df_report.to_csv(output_file, index=False, encoding="utf-8-sig")
        print(f"\n[Thành công] Đã xuất báo cáo tổng hợp bảng xếp hạng tại file: '{output_file}'")
    else:
        print("\n[Lưu ý] Chưa có thành viên nào nộp file kết quả dự đoán (*_predictions.json).")
        print("-> Trang hãy gom file của các bạn về cùng thư mục này và chạy lại file nhé!")
        print("="*85)

if __name__ == "__main__":
    aggregate_and_evaluate()
