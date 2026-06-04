# -*- coding: utf-8 -*-
"""
Dự án FSB-NLP501: Chạy đánh giá chất lượng tự động bằng Local LLM Gemma 4
cho các mô hình tóm tắt sử dụng Embedding (TextRank và LexRank Embedding).
"""

import json
import time
import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Thêm thư mục cha vào sys.path để nhận diện thư mục evaluation và subfolders
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent / "TextRank_Embedding"))
sys.path.append(str(Path(__file__).parent / "LexRank_Embedding"))
from evaluation import RealEstateEvaluator
from TextRank_Embedding import baseline_textrank_embedding

def evaluate_model_predictions(model_name: str, sheet_data_map: dict):
    subfolder_path = Path(__file__).parent / model_name
    pred_file_name = f"Nhan_{model_name}_predictions.json"
    pred_path = subfolder_path / pred_file_name

    if not pred_path.exists():
        print(f"❌ Không tìm thấy file dự đoán: {pred_path}")
        return

    print(f"\n📂 Đang đọc file dự đoán: {pred_file_name}")
    with open(pred_path, "r", encoding="utf-8") as f:
        predictions = json.load(f)

    # Ghép thông tin Ground Truth và Raw Input gốc từ Google Sheets
    predictions_with_gt = []
    for p in predictions:
        sid = p["id"]
        sheet_row = sheet_data_map.get(sid, {})
        
        # Đảm bảo có đầy đủ dữ liệu phục vụ đánh giá ROUGE-L / BERTScore / LLM Judge
        p_eval = p.copy()
        p_eval["raw_input_cleaned"] = sheet_row.get("raw_input", p.get("raw_input_cleaned", ""))
        p_eval["gt_title"] = sheet_row.get("gt_title", "")
        p_eval["gt_description"] = sheet_row.get("gt_description", "")
        predictions_with_gt.append(p_eval)

    # Khởi chạy bộ đánh giá
    evaluator = RealEstateEvaluator()
    print(f"👑 Đang gọi Local LLM Judge (google/gemma-4-e4b) để chấm điểm cho {model_name}...")
    eval_results = evaluator.evaluate_dataset(predictions_with_gt, model_local="google/gemma-4-e4b")

    # Ghép kết quả chấm điểm của LLM vào từng bản ghi để xuất bản mẫu chuyên gia
    llm_evals = eval_results.get("llm_judge", {}).get("sample_evaluations", [])
    eval_dict = {item["id"]: item["evaluation"] for item in llm_evals}

    for p in predictions:
        sid = p["id"]
        if sid in eval_dict:
            p["llm_evaluation"] = eval_dict[sid]

    # Lưu lại file predictions kèm theo thông tin đánh giá của LLM
    with open(pred_path, "w", encoding="utf-8") as f:
        json.dump(predictions, f, ensure_ascii=False, indent=2)
    print(f"💾 Đã cập nhật kết quả đánh giá LLM vào file dự đoán tại: {pred_path}")

    # Cập nhật file báo cáo hiệu năng (performance report)
    perf_file_name = f"Nhan_{model_name}_performance.json"
    perf_path = subfolder_path / perf_file_name
    
    performance = {}
    if perf_path.exists():
        with open(perf_path, "r", encoding="utf-8") as f:
            performance = json.load(f)
            
    performance["evaluation_results"] = eval_results
    if "note" in performance:
        del performance["note"] # Xóa ghi chú bỏ qua đánh giá trước đó
        
    with open(perf_path, "w", encoding="utf-8") as f:
        json.dump(performance, f, ensure_ascii=False, indent=2)
    print(f"💾 Đã cập nhật báo cáo hiệu năng đầy đủ tại: {perf_path}")

    # Tạo bảng biểu CSV chuyên nghiệp cho Chuyên gia đánh giá thủ công
    csv_rows = []
    for p in predictions:
        llm_eval = p.get("llm_evaluation", {})
        
        fact_score = llm_eval.get("factual_accuracy", {}).get("score", "N/A")
        fact_reason = llm_eval.get("factual_accuracy", {}).get("reason", "")
        
        coh_score = llm_eval.get("coherence_readability", {}).get("score", "N/A")
        coh_reason = llm_eval.get("coherence_readability", {}).get("reason", "")
        
        spec_score = llm_eval.get("specs_preservation", {}).get("score", "N/A")
        spec_reason = llm_eval.get("specs_preservation", {}).get("reason", "")
        
        csv_rows.append({
            "SystemID": p["id"],
            "Mô tả thô (Raw Input)": p["raw_input_cleaned"].replace("\n", " "),
            "Tiêu đề dự đoán (Pred Title)": p["predicted_title"],
            "Mô tả dự đoán (Pred Desc)": p["predicted_description"].replace("\n", " "),
            "Thông số trích xuất (Specs)": json.dumps(p["extracted_specs"], ensure_ascii=False),
            
            # Điểm số tự động của Local LLM Judge làm tham chiếu
            "LLM_Accuracy_Score": fact_score,
            "LLM_Accuracy_Reason": fact_reason,
            "LLM_Coherence_Score": coh_score,
            "LLM_Coherence_Reason": coh_reason,
            "LLM_Specs_Score": spec_score,
            "LLM_Specs_Reason": spec_reason,
            
            # Các cột trống để Chuyên gia chấm điểm thủ công & sửa đổi
            "Expert_Accuracy_Score (1-5)": "",
            "Expert_Coherence_Score (1-5)": "",
            "Expert_Specs_Score (1-5)": "",
            "Expert_Corrected_Description (Viết lại chuẩn nếu cần)": "",
            "Expert_Notes (Ghi chú lỗi)": ""
        })
        
    df_expert = pd.DataFrame(csv_rows)
    csv_path = subfolder_path / f"Nhan_{model_name}_Expert_Evaluation_Form.csv"
    df_expert.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"📊 Đã tạo biểu mẫu đánh giá của chuyên gia tại: {csv_path}")

def main():
    print("\n" + "="*80)
    print("🚀 BẮT ĐẦU PIPELINE ĐÁNH GIÁ MÔ HÌNH EMBEDDING BẰNG GEMMA 4 JUDGE")
    print("="*80)

    # 1. Tải dữ liệu từ Google Sheets để làm dữ liệu chuẩn (Ground Truth)
    rows = baseline_textrank_embedding.fetch_sheet(baseline_textrank_embedding.SHEET_URL)
    sheet_data_map = {r["id"]: r for r in rows}

    # 2. Đánh giá cho mô hình TextRank_Embedding
    evaluate_model_predictions("TextRank_Embedding", sheet_data_map)

    # 3. Đánh giá cho mô hình LexRank_Embedding
    evaluate_model_predictions("LexRank_Embedding", sheet_data_map)

    print("\n✅ Hoàn thành toàn bộ quy trình đánh giá! Báo cáo hiệu năng và file đánh giá chuyên gia đã sẵn sàng.")

if __name__ == "__main__":
    main()
