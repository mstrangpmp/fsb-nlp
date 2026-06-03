# -*- coding: utf-8 -*-
"""
Dự án FSB-NLP501: Module Đánh Giá Hiệu Năng Mô Hình (Evaluation Utility)
Hỗ trợ đo lường 3 nhóm tiêu chí chính:
  1. ROUGE-L (Precision, Recall, F1)
  2. BERTScore (Precision, Recall, F1 - sử dụng XLM-RoBERTa-base cho tiếng Việt)
  3. Local LLM Judge (Factual Accuracy, Coherence/Readability, Specs Preservation)
"""

import os
import sys
import json
import argparse
import numpy as np
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

# Reconfigure stdout to use utf-8 to avoid encoding issues
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

# ==============================================================================
# Pydantic Schemas for Local LLM Structured Output
# ==============================================================================

class CriteriaEvaluation(BaseModel):
    score: int = Field(..., description="Điểm đánh giá từ 1 đến 5 (5 là tốt nhất)")
    reason: str = Field(..., description="Lý giải chi tiết chấm điểm bằng tiếng Việt, giải thích rõ lỗi nếu có")

class RealEstateEvaluation(BaseModel):
    factual_accuracy: CriteriaEvaluation = Field(
        ..., 
        description="Đánh giá độ chính xác thông tin so với tin đăng thô. Phạt nặng nếu tự bịa thông tin (hallucination)."
    )
    coherence_readability: CriteriaEvaluation = Field(
        ..., 
        description="Đánh giá hành văn ngắn gọn, dễ đọc, mạch lạc, không bị cụt câu, và không chứa tin rác/blacklist môi giới."
    )
    specs_preservation: CriteriaEvaluation = Field(
        ..., 
        description="Đánh giá mức độ bảo toàn đầy đủ và chuẩn xác các thông số chính (diện tích, giá, số tầng, ngang, dài, hẻm, đường, quận) trong tiêu đề hoặc mô tả."
    )

# ==============================================================================
# Main Evaluator Class
# ==============================================================================

class RealEstateEvaluator:
    def __init__(self):
        """
        Khởi tạo Evaluator.
        Hỗ trợ đánh giá bằng Local LLM (LM Studio) qua endpoint http://127.0.0.1:1234
        """
        # Cấu hình Local LLM (LM Studio)
        self.local_url = "http://127.0.0.1:1234/v1/chat/completions"
        self.use_response_format = True
        print("✅ [Evaluator] Đã khởi tạo bộ đánh giá. Sẵn sàng kết nối Local LLM (LM Studio) tại http://127.0.0.1:1234")

    def evaluate_rouge_l(self, predictions: List[str], references: List[str]) -> Dict[str, float]:
        """
        Tính điểm ROUGE-L trung bình giữa danh sách dự đoán và nhãn tham chiếu.
        """
        try:
            from rouge_score import rouge_scorer
        except ImportError:
            print("Installing 'rouge-score' library...")
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "rouge-score"])
            from rouge_score import rouge_scorer

        scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
        
        p_scores, r_scores, f_scores = [], [], []
        for pred, ref in zip(predictions, references):
            scores = scorer.score(ref, pred)['rougeL']
            p_scores.append(scores.precision)
            r_scores.append(scores.recall)
            f_scores.append(scores.fmeasure)
            
        return {
            "rouge_l_precision": round(float(np.mean(p_scores)) * 100, 2),
            "rouge_l_recall": round(float(np.mean(r_scores)) * 100, 2),
            "rouge_l_f1": round(float(np.mean(f_scores)) * 100, 2),
            "rouge_l_f1_std": round(float(np.std(f_scores)) * 100, 2)
        }

    def evaluate_bert_score(self, predictions: List[str], references: List[str], model_type: str = "xlm-roberta-base") -> Dict[str, float]:
        """
        Tính điểm BERTScore sử dụng mô hình multilingual transformer (mặc định xlm-roberta-base).
        """
        try:
            from bert_score import score
        except ImportError:
            print("Installing 'bert-score' library...")
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "bert-score"])
            from bert_score import score

        # Tính toán điểm BERTScore sử dụng XLM-RoBERTa (thích hợp cho tiếng Việt)
        P, R, F1 = score(predictions, references, lang="vi", model_type=model_type)
        return {
            "bert_score_precision": round(float(P.mean().item()) * 100, 2),
            "bert_score_recall": round(float(R.mean().item()) * 100, 2),
            "bert_score_f1": round(float(F1.mean().item()) * 100, 2),
            "bert_score_f1_std": round(float(F1.std().item()) * 100, 2)
        }

    def evaluate_llm_judge_single(self, raw_input: str, predicted_title: str, predicted_description: str, ref_title: Optional[str] = None, ref_description: Optional[str] = None, model: str = "google/gemma-4-e4b") -> Dict[str, Any]:
        """
        Sử dụng giám khảo Local LLM (LM Studio) để đánh giá chi tiết chất lượng 1 tin đăng dự đoán.
        """
        prompt = f"""Bạn là một chuyên gia kiểm định chất lượng văn bản NLP giàu kinh nghiệm trong lĩnh vực Bất động sản tại Việt Nam.
Hãy phân tích và chấm điểm (từ 1 đến 5 điểm, với 5 là tối đa) cho kết quả rút gọn tin đăng dưới đây:

[TIN ĐĂNG THÔ ĐẦU VÀO]
{raw_input}

[TIÊU ĐỀ DỰ ĐOÁN]
{predicted_title}

[MÔ TẢ RÚT GỌN DỰ ĐOÁN]
{predicted_description}
"""
        if ref_title or ref_description:
            prompt += "\n[THÔNG TIN THAM KHẢO CHUẨN (GROUND TRUTH)]\n"
            if ref_title:
                prompt += f"- Tiêu đề chuẩn: {ref_title}\n"
            if ref_description:
                prompt += f"- Mô tả chuẩn: {ref_description}\n"

        prompt += """
Tiêu chí chấm điểm:
1. Factual Accuracy (Độ chính xác thực tế & Không bịa đặt):
   - 5 điểm: Tất cả số liệu, tên đường, tên quận, giá, diện tích trong tiêu đề và mô tả dự đoán đều chính xác và có nguồn gốc trực tiếp từ tin đăng thô. Không chứa bất kỳ thông tin bịa đặt nào (No hallucinations).
   - 1 điểm: Bất kỳ thông số nào bị sai lệch nghiêm trọng hoặc tự chế ra số liệu (ví dụ: đổi giá 12.8 tỷ thành 27.5 tỷ, đổi ngang 4.6m thành 5.5m).

2. Coherence & Readability (Độ mạch lạc, hành văn tự nhiên & Sạch tin rác):
   - 5 điểm: Tiêu đề rõ ràng, mô tả rút gọn mạch lạc, viết câu hoàn chỉnh có chủ vị, đọc trơn tru và đặc biệt là ĐÃ BỊ LOẠI BỎ hoàn toàn các thông tin liên hệ rác (số điện thoại, link facebook, yêu cầu báo trước đầu chủ, hoa hồng, chúc ace chốt bùng nổ, ký phiếu YCCCDV).
   - 1 điểm: Lủng củng, câu cụt không rõ nghĩa, hoặc chứa nguyên văn số điện thoại và thông tin giao dịch nội bộ của môi giới.

3. Specs Preservation (Bảo toàn các thông số kỹ thuật quan trọng):
   - 5 điểm: Trích xuất chính xác và bảo toàn đầy đủ các thông số kỹ thuật cốt lõi: Tên đường, Quận, Diện tích, Ngang x Dài (nếu có), Số tầng, Hẻm/Mặt tiền, Giá. Các thông số này phải xuất hiện đầy đủ trong tiêu đề hoặc phần mô tả.
   - 1 điểm: Bỏ sót hầu hết thông số kỹ thuật cốt lõi hoặc trích xuất sai lệch hoàn toàn.

YÊU CẦU ĐỊNH DẠNG ĐẦU RA:
Bạn phải trả về một đối tượng JSON duy nhất theo định dạng chính xác sau đây:
{
  "factual_accuracy": {
    "score": <số nguyên từ 1 đến 5>,
    "reason": "<lý giải cực kỳ ngắn gọn dưới 15 từ bằng tiếng Việt>"
  },
  "coherence_readability": {
    "score": <số nguyên từ 1 đến 5>,
    "reason": "<lý giải cực kỳ ngắn gọn dưới 15 từ bằng tiếng Việt>"
  },
  "specs_preservation": {
    "score": <số nguyên từ 1 đến 5>,
    "reason": "<lý giải cực kỳ ngắn gọn dưới 15 từ bằng tiếng Việt>"
  }
}
Chỉ trả về JSON, không thêm bất kỳ văn bản giải thích nào khác ngoài khối JSON này.
"""

        # Gọi Local LLM (LM Studio)
        import requests
        max_retries = 3
        import time

        for attempt in range(max_retries):
            try:
                headers = {"Content-Type": "application/json"}
                payload = {
                    "model": model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "Bạn là chuyên gia kiểm định chất lượng văn bản NLP tiếng Việt. Bạn phải luôn trả về dữ liệu định dạng JSON duy nhất khớp với cấu trúc được yêu cầu, không thêm bất kỳ từ ngữ nào bên ngoài."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.0,
                    "max_tokens": 250
                }
                
                if self.use_response_format:
                    payload["response_format"] = {
                        "type": "json_schema",
                        "json_schema": {
                            "name": "RealEstateEvaluation",
                            "schema": RealEstateEvaluation.model_json_schema()
                        }
                    }
                
                response = requests.post(
                    self.local_url,
                    headers=headers,
                    json=payload,
                    timeout=60
                )
                
                # Nếu lỗi do model không hỗ trợ response_format, bỏ nó đi ở lượt thử kế tiếp và đặt cờ
                if response.status_code != 200 and self.use_response_format and attempt == 0:
                    print("\n⚠️  [Evaluator] Local LLM không hỗ trợ response_format json_schema. Đang chuyển sang chế độ text fallback...")
                    self.use_response_format = False
                    payload.pop("response_format", None)
                    response = requests.post(
                        self.local_url,
                        headers=headers,
                        json=payload,
                        timeout=60
                    )
                    
                if response.status_code == 200:
                    content = response.json()["choices"][0]["message"]["content"].strip()
                    
                    # Loại bỏ markdown code block fences ```json và ``` nếu có
                    if content.startswith("```"):
                        lines = content.splitlines()
                        if len(lines) > 2:
                            if lines[0].startswith("```"):
                                lines = lines[1:]
                            if lines[-1].startswith("```"):
                                lines = lines[:-1]
                            content = "\n".join(lines).strip()
                            
                    return json.loads(content)
                else:
                    if attempt < max_retries - 1:
                        time.sleep(1.0)
                    else:
                        return {"error": f"LM Studio trả về mã lỗi: {response.status_code} - {response.text}"}
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(1.0)
                else:
                    return {"error": f"Lỗi gọi Local LLM (LM Studio): {str(e)}"}
        return {"error": "Thất bại kết nối tới LM Studio sau tối đa số lần thử."}

    def evaluate_dataset(self, predictions_list: List[Dict[str, Any]], model_local: str = "google/gemma-4-e4b") -> Dict[str, Any]:
        """
        Đánh giá toàn bộ tập dữ liệu dự đoán bằng ROUGE, BERTScore và Local LLM.
        """
        print(f"\n📊 Bắt đầu đánh giá tập dữ liệu ({len(predictions_list)} mẫu)...")
        
        preds_desc = []
        refs_desc = []
        preds_title = []
        refs_title = []
        
        # Lọc ra các mẫu có Ground Truth để tính điểm tương quan từ vựng
        eval_samples = []
        for item in predictions_list:
            pred_d = item.get("predicted_description", "").strip()
            gt_d = item.get("gt_description", "").strip()
            pred_t = item.get("predicted_title", "").strip()
            gt_t = item.get("gt_title", "").strip()
            
            if gt_d and pred_d:
                preds_desc.append(pred_d)
                refs_desc.append(gt_d)
            if gt_t and pred_t:
                preds_title.append(pred_t)
                refs_title.append(gt_t)
            
            if gt_d or gt_t:
                eval_samples.append(item)

        results = {}

        # 1. ROUGE-L
        if refs_desc:
            print("📝 Đang tính toán ROUGE-L cho Mô tả...")
            results["desc_rouge"] = self.evaluate_rouge_l(preds_desc, refs_desc)
        if refs_title:
            print("📝 Đang tính toán ROUGE-L cho Tiêu đề...")
            results["title_rouge"] = self.evaluate_rouge_l(preds_title, refs_title)
        
        # 2. BERTScore
        if refs_desc:
            print("🤖 Đang tính toán BERTScore cho Mô tả (XLM-RoBERTa-base)...")
            try:
                results["desc_bert_score"] = self.evaluate_bert_score(preds_desc, refs_desc)
            except Exception as e:
                print(f"⚠️  Không thể tính BERTScore cho Mô tả: {str(e)}")
                results["desc_bert_score"] = {"error": str(e)}
        if refs_title:
            print("🤖 Đang tính toán BERTScore cho Tiêu đề (XLM-RoBERTa-base)...")
            try:
                results["title_bert_score"] = self.evaluate_bert_score(preds_title, refs_title)
            except Exception as e:
                print(f"⚠️  Không thể tính BERTScore cho Tiêu đề: {str(e)}")
                results["title_bert_score"] = {"error": str(e)}

        # 3. Local LLM Judge
        print(f"👑 Đang chạy LLM Judge ({model_local}) trên tất cả mẫu...")
        llm_results = []
        factual_scores = []
        coherence_scores = []
        specs_scores = []
        
        import time
        for item in predictions_list:
            raw = item.get("raw_input_cleaned") or item.get("raw_input") or ""
            pred_t = item.get("predicted_title") or ""
            pred_d = item.get("predicted_description") or ""
            ref_t = item.get("gt_title")
            ref_d = item.get("gt_description")
            
            # Giản thời gian đối với Local LLM chạy trên localhost
            time.sleep(0.05)
            
            print(f"⌛ Đang đánh giá mẫu {len(llm_results)+1}/{len(predictions_list)} (ID: {item.get('id')})...", flush=True)
            
            judge_eval = self.evaluate_llm_judge_single(
                raw_input=raw,
                predicted_title=pred_t,
                predicted_description=pred_d,
                ref_title=ref_t,
                ref_description=ref_d,
                model=model_local
            )
            
            sample_res = {
                "id": item.get("id"),
                "evaluation": judge_eval
            }
            llm_results.append(sample_res)
            
            if "error" not in judge_eval:
                factual_scores.append(judge_eval["factual_accuracy"]["score"])
                coherence_scores.append(judge_eval["coherence_readability"]["score"])
                specs_scores.append(judge_eval["specs_preservation"]["score"])

        results["llm_judge"] = {
            "factual_accuracy_mean": round(float(np.mean(factual_scores)), 2) if factual_scores else 0.0,
            "coherence_readability_mean": round(float(np.mean(coherence_scores)), 2) if coherence_scores else 0.0,
            "specs_preservation_mean": round(float(np.mean(specs_scores)), 2) if specs_scores else 0.0,
            "sample_evaluations": llm_results
        }
        
        print(f"   - Factual Accuracy: {results['llm_judge']['factual_accuracy_mean']}/5.0")
        print(f"   - Coherence & Readability: {results['llm_judge']['coherence_readability_mean']}/5.0")
        print(f"   - Specs Preservation: {results['llm_judge']['specs_preservation_mean']}/5.0")

        return results

# ==============================================================================
# CLI Entry Point
# ==============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FSB-NLP501 Real Estate Evaluation System")
    parser.add_argument("--predictions", type=str, required=True, help="Đường dẫn tới file predictions.json")
    parser.add_argument("--output", type=str, default="evaluation_results.json", help="Đường dẫn lưu kết quả đánh giá")
    parser.add_argument("--model", type=str, default="google/gemma-4-e4b", help="Model Local LLM dùng làm giám khảo")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.predictions):
        print(f"❌ File '{args.predictions}' không tồn tại.")
        sys.exit(1)
        
    with open(args.predictions, "r", encoding="utf-8") as f:
        preds = json.load(f)
        
    evaluator = RealEstateEvaluator()
    eval_results = evaluator.evaluate_dataset(preds, model_local=args.model)
    
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(eval_results, f, ensure_ascii=False, indent=2)
        
    print(f"\n💾 Đã lưu báo cáo đánh giá chi tiết tại: {args.output}")
