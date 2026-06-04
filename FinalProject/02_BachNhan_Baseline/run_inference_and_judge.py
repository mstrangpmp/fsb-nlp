# -*- coding: utf-8 -*-
"""
Dự án FSB-NLP501: Script chạy dự đoán (Inference) trên 26 dòng chưa có nhãn
cho CẢ HAI mô hình TextRank và LexRank, sau đó đánh giá tự động bằng Local LLM Gemma 4 e4b
và xuất file chấm điểm cho chuyên gia.
"""

import csv
import json
import time
import os
import sys
from pathlib import Path
from tqdm import tqdm
import numpy as np
import pandas as pd

# Thêm đường dẫn để nhận diện gói evaluation
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent / "TextRank_TFIDF"))
sys.path.append(str(Path(__file__).parent / "LexRank_TFIDF"))
from evaluation import RealEstateEvaluator
from TextRank_TFIDF import baseline_textrank
from LexRank_TFIDF import baseline_lexrank

def run_model_pipeline(model_name: str, inference_rows: list, train_rows: list):
    print(f"\n🔮 Đang tiến hành rút gọn {len(inference_rows)} tin đăng bằng {model_name}...")
    
    predictions = []
    latency_log = []
    
    for row in tqdm(inference_rows, desc=f"{model_name} Rút gọn"):
        raw = row["raw_input"]
        sid = row["id"]
        
        t0 = time.perf_counter()
        if model_name == "TextRank":
            description = baseline_textrank.textrank_summarize(raw, n_sentences=3)
            specs = baseline_textrank.extract_specs(description)
            title = baseline_textrank.generate_title(specs)
        else: # LexRank
            description = baseline_lexrank.lexrank_summarize(raw, n_sentences=3, threshold=0.1)
            specs = baseline_lexrank.extract_specs(description)
            title = baseline_lexrank.generate_title(specs)
        elapsed = time.perf_counter() - t0
        latency_log.append(elapsed)
        
        predictions.append({
            "id": sid,
            "raw_input_cleaned": raw,
            "predicted_title": title,
            "predicted_description": description,
            "extracted_specs": specs
        })

    # 4. Sử dụng Local LLM (LM Studio) làm giám khảo đánh giá chất lượng 26 dòng dự đoán
    evaluator = RealEstateEvaluator()
    print(f"👑 Đang gọi Local LLM Judge (google/gemma-4-e4b) để chấm điểm 26 dòng cho {model_name}...")
    eval_results = evaluator.evaluate_dataset(predictions, model_local="google/gemma-4-e4b")
    
    # Ghép kết quả đánh giá của Local LLM vào từng bản ghi
    llm_evals = eval_results.get("llm_judge", {}).get("sample_evaluations", [])
    eval_dict = {item["id"]: item["evaluation"] for item in llm_evals}
    
    for p in predictions:
        sid = p["id"]
        if sid in eval_dict:
            p["llm_evaluation"] = eval_dict[sid]

    # 5. Lưu kết quả dự đoán và hiệu năng dạng JSON
    subfolder_path = Path(__file__).parent / f"{model_name}_TFIDF"
    pred_path = subfolder_path / f"Nhan_{model_name}_Inference_predictions.json"
    with open(pred_path, "w", encoding="utf-8") as f:
        json.dump(predictions, f, ensure_ascii=False, indent=2)
    print(f"💾 Đã lưu dự đoán của 26 dòng tại: {pred_path}")
    
    perf_path = subfolder_path / f"Nhan_{model_name}_Inference_performance.json"
    performance = {
        "model_name": f"{model_name} (Vietnamese Real-Estate Baseline)",
        "n_inference_records": len(predictions),
        "average_latency_seconds": round(float(np.mean(latency_log)), 5) if latency_log else 0,
        "total_time_seconds": round(float(sum(latency_log)), 3) if latency_log else 0,
        "evaluation_results": eval_results
    }
    with open(perf_path, "w", encoding="utf-8") as f:
        json.dump(performance, f, ensure_ascii=False, indent=2)
    print(f"💾 Đã lưu báo cáo hiệu năng tại: {perf_path}")

    # 6. Xuất bảng biểu CSV chuyên nghiệp cho Chuyên gia chấm điểm thủ công
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
    print("🚀 KHỞI CHẠY PIPELINE INFERENCE & EVALUATION TRÊN 26 DÒNG CHƯA CÓ NHÃN")
    print("="*80)

    # 1. Tải dữ liệu từ Google Sheets
    rows = baseline_textrank.fetch_sheet(baseline_textrank.SHEET_URL)
    
    # 2. Phân chia dữ liệu: 11 dòng đã có nhãn (Train) và 26 dòng chưa có nhãn (Inference)
    train_rows = []
    inference_rows = []
    for r in rows:
        if r.get("gt_description"):
            train_rows.append(r)
        else:
            inference_rows.append(r)
            
    print(f"\n📌 Phát hiện {len(train_rows)} dòng có nhãn dùng làm dữ liệu mẫu (Train)")
    print(f"📌 Phát hiện {len(inference_rows)} dòng chưa có nhãn cần rút gọn (Inference)")
    
    if not inference_rows:
        print("❌ Không tìm thấy dòng cần dự đoán nào.")
        return

    # Lưu tập Train riêng để tiện theo dõi
    train_path = Path(__file__).parent / "Nhan_Train_11_records.json"
    with open(train_path, "w", encoding="utf-8") as f:
        json.dump(train_rows, f, ensure_ascii=False, indent=2)
    print(f"💾 Đã lưu 11 dòng Train tại: {train_path}")

    # Chạy pipeline cho cả TextRank và LexRank
    run_model_pipeline("TextRank", inference_rows, train_rows)
    run_model_pipeline("LexRank", inference_rows, train_rows)

    print("\n✅ Hoàn thành toàn bộ pipeline cho cả 2 mô hình! Dữ liệu đã sẵn sàng để chuyên gia đánh giá thủ công.")

if __name__ == "__main__":
    main()
