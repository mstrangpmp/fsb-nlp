"""
==============================================================================
02 - Bách Nhân Baseline: TextRank with Local LLM Embeddings for Viet. Real-Estate
==============================================================================
Pipeline:
  1. Pull newest data from Google Sheets (public CSV export)
  2. Run Vietnamese TextRank using dense sentence embeddings from LM Studio (BGE-M3)
  3. Extract specs (price, area, floors, alley type, …) via regex from raw input text
  4. Generate standardised title
  5. Evaluate ROUGE-L against ground truth (when available)
  6. Save:
       - Nhan_TextRank_Embedding_predictions.json
       - Nhan_TextRank_Embedding_performance.json

Usage:
    Start LM Studio with an embedding model (e.g. BGE-M3) loaded on port 1234.
    python baseline_textrank_embedding.py
==============================================================================
"""

import csv
import json
import re
import time
import io
from typing import Optional
from pathlib import Path

import numpy as np
import requests
from tqdm import tqdm

try:
    from underthesea import word_tokenize, sent_tokenize as vi_sent_tokenize
    HAS_UNDERTHESEA = True
    print("✅ underthesea loaded — using Vietnamese word tokenizer")
except ImportError:
    HAS_UNDERTHESEA = False
    print("⚠️  underthesea not found — falling back to simple sentence splitter")

try:
    from rouge_score import rouge_scorer as rs_module
    HAS_ROUGE = True
except ImportError:
    HAS_ROUGE = False
    print("⚠️  rouge-score not found — skipping ROUGE-L evaluation")

from sklearn.metrics.pairwise import cosine_similarity


# ══════════════════════════════════════════════════════════════════════════════
# 0. CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

SHEET_ID   = "1qoyFArLxQJsSYkMf3_fPKFseOfoFcZlJ4jnf3eZLC3w"
GID        = "0"
SHEET_URL  = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

OUTPUT_DIR = Path(__file__).parent        # same folder as this script
N_SUMMARY_SENTENCES = 3                   # how many sentences to extract per listing

LM_STUDIO_API_URL = "http://127.0.0.1:1234"


# ══════════════════════════════════════════════════════════════════════════════
# 1. FETCH DATA FROM GOOGLE SHEETS
# ══════════════════════════════════════════════════════════════════════════════

def fetch_sheet(url: str) -> list:
    print(f"\n📥 Fetching data from Google Sheets …")
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()

    content = resp.content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(content))

    rows = []
    for row in reader:
        raw = row.get("Mô tả thô", "").strip()
        sid = row.get("ID", "").strip()
        gt_title = row.get("Tiêu đề chuẩn", "").strip()
        gt_desc  = row.get("Mô tả chuẩn", "").strip()

        if not sid or not raw:          # skip empty rows
            continue

        rows.append({
            "id":              sid,
            "raw_input":       raw,
            "gt_title":        gt_title,
            "gt_description":  gt_desc,
        })

    print(f"✅ Loaded {len(rows)} listings from Google Sheets")
    return rows


# ══════════════════════════════════════════════════════════════════════════════
# 2. LOCAL EMBEDDING HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def get_loaded_model_name() -> str:
    """Query LM Studio to detect the name of the currently loaded model."""
    try:
        resp = requests.get(f"{LM_STUDIO_API_URL}/v1/models", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if "data" in data and len(data["data"]) > 0:
                model_id = data["data"][0]["id"]
                print(f"🤖 Detected loaded model in LM Studio: {model_id}")
                return model_id
    except Exception as e:
        print(f"⚠️ Could not auto-detect model from LM Studio /v1/models: {e}")
    print("ℹ️ Using default model ID: 'bge-m3'")
    return "bge-m3"


def get_embeddings_batch(sentences: list[str], model_name: str) -> list[list[float]]:
    """Fetch dense embedding vectors in batch from LM Studio."""
    try:
        payload = {
            "input": sentences,
            "model": model_name
        }
        resp = requests.post(f"{LM_STUDIO_API_URL}/v1/embeddings", json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        
        results = data.get("data", [])
        # Sort by index to preserve order of input sentences
        results_sorted = sorted(results, key=lambda x: x.get("index", 0))
        return [item["embedding"] for item in results_sorted]
    except Exception as e:
        print(f"❌ Error fetching embeddings from LM Studio: {e}")
        return []


# ══════════════════════════════════════════════════════════════════════════════
# 3. SEMANTIC TEXTRANK WITH EMBEDDINGS
# ══════════════════════════════════════════════════════════════════════════════

def _extract_sentences(text: str) -> list[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    sents = []
    for line in lines:
        if HAS_UNDERTHESEA:
            sents.extend(vi_sent_tokenize(line))
        else:
            parts = re.split(r'(?<=[.!?])\s+', line)
            sents.extend(parts)
    return [s.strip() for s in sents if len(s.strip()) > 12]


def _pagerank(sim: np.ndarray, d: float = 0.85, max_iter: int = 100) -> np.ndarray:
    n = sim.shape[0]
    row_sum = sim.sum(axis=1, keepdims=True)
    row_sum[row_sum == 0] = 1
    trans = sim / row_sum
    scores = np.ones(n) / n
    for _ in range(max_iter):
        new_s = (1 - d) / n + d * trans.T @ scores
        if np.linalg.norm(new_s - scores) < 1e-6:
            break
        scores = new_s
    return scores


_BLACKLIST_RE = re.compile(
    r'(liên hệ|sđt|alo|zalo|facebook|inbox|báo trước|dẫn khách'
    r'|ký phiếu|quy trình|đầu chủ|thiên khôi|hoa hồng|chúc ace'
    r'|chốt bùng|thu bông|hỗ trợ tốt nhất|khảo sát)',
    re.IGNORECASE
)

_PRIORITY_TERMS = (
    "diện tích", "kết cấu", "hẻm", "mặt tiền", "sổ hồng",
    "pháp lý", "hoàn công", "giá", "tầng", "phòng ngủ",
    "vị trí", "phường", "quận",
)


def textrank_summarize_embedding(text: str, model_name: str, n_sentences: int = 3) -> str:
    """
    Vietnamese TextRank using dense sentence embeddings from LM Studio.
    Returns top-N sentences in original order.
    """
    sentences = _extract_sentences(text)

    # Filter out boilerplate / agent-instructions
    sentences = [s for s in sentences if not _BLACKLIST_RE.search(s)]

    if not sentences:
        return text.strip()[:400]
    if len(sentences) <= n_sentences:
        return " ".join(sentences)

    # Get dense embeddings from local model
    embeddings = get_embeddings_batch(sentences, model_name)
    if not embeddings or len(embeddings) != len(sentences):
        print("⚠️ Embedding retrieval failed or mismatched length. Falling back to default top sentences.")
        return " ".join(sentences[:n_sentences])

    embeddings_arr = np.array(embeddings)
    
    # Compute similarity using cosine similarity on embeddings
    sim = cosine_similarity(embeddings_arr, embeddings_arr).astype(float)
    np.fill_diagonal(sim, 0)

    # Clean similarity: cosine similarity can sometimes be slightly negative, clamp to >= 0
    sim = np.clip(sim, 0, None)

    scores = _pagerank(sim)

    # Priority boost: sentences mentioning key real-estate terms
    for i, sent in enumerate(sentences):
        sl = sent.lower()
        bonus = sum(0.05 for term in _PRIORITY_TERMS if term in sl)
        scores[i] += bonus

    top_idx = sorted(np.argsort(scores)[-n_sentences:].tolist())
    return " ".join(sentences[i] for i in top_idx)


# ══════════════════════════════════════════════════════════════════════════════
# 4. REGEX SPEC EXTRACTION & TITLE GENERATION
# ══════════════════════════════════════════════════════════════════════════════

def extract_specs_from_header(line: str) -> dict:
    specs = {}
    lower_line = line.lower().strip()
    street_name = None
    rest = line

    if lower_line.startswith("cách mạng tháng 8") or lower_line.startswith("cmt8") or lower_line.startswith("cách mạng tháng tám"):
        street_name = "Cách Mạng Tháng 8"
        m = re.match(r'^(cách mạng tháng 8|cmt8|cách mạng tháng tám)', line, re.IGNORECASE)
        if m:
            rest = line[m.end():]
    elif lower_line.startswith("3 tháng 2") or lower_line.startswith("3/2") or lower_line.startswith("ba tháng hai"):
        street_name = "3 Tháng 2"
        m = re.match(r'^(3 tháng 2|3/2|ba tháng hai)', line, re.IGNORECASE)
        if m:
            rest = line[m.end():]
    else:
        m = re.match(r'^([A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝĂĐƠƯẠẶẤẦẨẪẬẮẰẲẴẶẸẼẾỀỂỄỆỈỊỌỎỐỒỔỖỘỚỜỞỠỢỤỦỨỪỬỮỰỲỴỶỸ][a-zA-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝĂĐƠƯẠẶẤẦẨẪẬẮẰẲẴẶẸẼẾỀỂỄỆỈỊỌỎỐỒỔỖỘỚỜỞỠỢỤỦỨỪỬỮỰỲỴỶỸa-zàáâãèéêìíòóôõùúýăđơưạặấầẩẫậắằẳẵặẹẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ\s\-\,\.]+?)(?=\s+\d)', line)
        if m:
            street_name = m.group(1).strip().rstrip(',')
            rest = line[m.end():]

    if street_name:
        specs["duong"] = street_name

    num_matches = re.findall(r'\d+(?:[.,/]\d+)*', rest)
    if len(num_matches) >= 5:
        if "tỷ" in lower_line or "ty" in lower_line or "tỷ" in rest.lower() or "ty" in rest.lower():
            area_str = num_matches[0]
            if "/" in area_str:
                area_str = area_str.split("/")[0]
            try:
                specs["dien_tich_m2"] = float(area_str.replace(',', '.'))
            except ValueError:
                pass

            try:
                specs["so_tang"] = int(num_matches[1])
            except ValueError:
                pass

            width_str = num_matches[2]
            if "/" in width_str:
                width_str = width_str.split("/")[0]
            try:
                specs["mat_tien_m"] = float(width_str.replace(',', '.'))
            except ValueError:
                pass

            try:
                specs["chieu_sau_m"] = float(num_matches[3].replace(',', '.'))
            except ValueError:
                pass

            try:
                specs["gia_ty"] = float(num_matches[4].replace(',', '.'))
            except ValueError:
                pass

    return specs


def extract_specs(text: str) -> dict:
    t = text.lower()
    first_line = text.strip().splitlines()[0] if text.strip() else ""

    dt_matches = re.findall(r'(\d+\.?\d*)\s*m2', t)
    dien_tich = float(dt_matches[0]) if dt_matches else None

    gia = None
    m = re.search(r'(\d+[,.]?\d*)\s*(?:tỷ|ty)(?:\s*(?:tl|thương lượng))?', t)
    if m:
        gia = float(m.group(1).replace(',', '.'))

    so_tang = None
    m = re.search(r'(\d+)\s*trệt.{0,80}?(\d+)\s*(?:lầu|lửng)', t)
    if m:
        so_tang = int(m.group(1)) + int(m.group(2))
    else:
        m = re.search(r'(\d+)\s*(?:tầng|lầu)', t)
        if m:
            so_tang = int(m.group(1))

    ngang = None
    m = re.search(r'ngang\s*(\d+\.?\d*)', t)
    if not m:
        m = re.search(r'(\d+\.?\d*)\s*m?\s*[x×]\s*\d', t)
    if m:
        ngang = float(m.group(1))

    sau = None
    m = re.search(r'(?:dài|sâu)\s*(\d+\.?\d*)', t)
    if not m:
        m = re.search(r'[x×]\s*(\d+\.?\d*)', t)
    if m:
        sau = float(m.group(1))

    if "hẻm" in t or "hxh" in t or "xe hơi" in t or "ô tô" in t or "oto" in t or "hxt" in t or "xe tải" in t or "xe máy" in t or "ba gác" in t:
        if "xe hơi" in t or "ô tô" in t or "oto" in t or "hxh" in t:
            hem = "Hẻm xe hơi"
        elif "xe tải" in t or "hxt" in t:
            hem = "Hẻm xe tải"
        elif "xe máy" in t or "ba gác" in t:
            hem = "Hẻm xe máy"
        else:
            hem = "Hẻm thông"
    elif "mặt tiền" in t:
        hem = "Mặt tiền"
    else:
        hem = "Hẻm thông"

    quan = None
    for name in ["bình thạnh", "phú nhuận", "gò vấp", "tân bình",
                 "tân phú", "bình tân", "thủ đức", "nhà bè", "hóc môn", "củ chi", "bình chánh"]:
        if name in t:
            quan = name.title()
            break
    if not quan:
        m = re.search(r'quận\s*(\d+)', t)
        if m:
            quan = f"Quận {m.group(1)}"
        else:
            m = re.search(r'quận\s*(\w+)', t)
            if m:
                quan = f"Quận {m.group(1).title()}"

    phuong = None
    m = re.search(r'(?:phường|p\.)\s*([\w\s]+?)(?:\s+(?:quận|hcm|tp|,|\.|$))', t)
    if m:
        phuong = f"Phường {m.group(1).strip().title()}"

    duong = _extract_street_name(text)

    header_specs = extract_specs_from_header(first_line)

    return {
        "duong":          header_specs.get("duong") or duong,
        "phuong":         phuong,
        "quan":           quan,
        "gia_ty":         header_specs.get("gia_ty") if header_specs.get("gia_ty") is not None else gia,
        "dien_tich_m2":   header_specs.get("dien_tich_m2") if header_specs.get("dien_tich_m2") is not None else dien_tich,
        "so_tang":        header_specs.get("so_tang") if header_specs.get("so_tang") is not None else so_tang,
        "mat_tien_m":     header_specs.get("mat_tien_m") if header_specs.get("mat_tien_m") is not None else ngang,
        "chieu_sau_m":    header_specs.get("chieu_sau_m") if header_specs.get("chieu_sau_m") is not None else sau,
        "phan_loai_hem":  hem,
    }


def _extract_street_name(text: str) -> Optional[str]:
    first_line = text.strip().splitlines()[0] if text.strip() else ""
    m = re.match(
        r'^([A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝĂĐƠƯẠẶẤẦẨẪẬẮẰẲẴẶẸẼẾỀỂỄỆỈỊỌỎỐỒỔỖỘỚỜỞỠỢỤỦỨỪỬỮỰỲỴỶỸ]'
        r'[^\d\n]{3,50}?)\s+\d',
        first_line.strip()
    )
    if m:
        candidate = m.group(1).strip().rstrip(',')
        candidate = re.sub(r'\s+(tỷ|tầng|lầu|m2|ngang|dài|sâu).*$', '', candidate, flags=re.I)
        if 3 < len(candidate) < 60:
            return candidate
    return None


def generate_title(specs: dict) -> str:
    parts = []
    loc = " ".join(filter(None, [specs.get("duong"), specs.get("quan")]))
    if loc:
        parts.append(loc)

    dt = specs.get("dien_tich_m2")
    ngang = specs.get("mat_tien_m")
    sau = specs.get("chieu_sau_m")
    if dt:
        dim = f"{dt}m2"
        if ngang and sau:
            dim += f" ({ngang}x{sau})"
        elif ngang:
            dim += f" ({ngang}m ngang)"
        parts.append(dim)

    hem = specs.get("phan_loai_hem")
    if hem:
        parts.append(hem)

    tang = specs.get("so_tang")
    if tang:
        parts.append(f"{tang} tầng")

    gia = specs.get("gia_ty")
    if gia:
        parts.append(f"{gia} Tỷ")

    return " - ".join(parts) if parts else "Bất động sản cần bán"


def compute_rouge(predictions: list) -> Optional[dict]:
    if not HAS_ROUGE:
        return None

    scorer = rs_module.RougeScorer(["rougeL"], use_stemmer=False)
    scores = []
    for pred in predictions:
        gt = pred.get("gt_description", "")
        hyp = pred.get("predicted_description", "")
        if gt and hyp:
            s = scorer.score(gt, hyp)["rougeL"].fmeasure
            scores.append(s)

    if not scores:
        return None
    return {
        "rouge_l_mean":  round(float(np.mean(scores)), 4),
        "rouge_l_std":   round(float(np.std(scores)),  4),
        "n_evaluated":   len(scores),
    }


# ══════════════════════════════════════════════════════════════════════════════
# 5. MAIN PIPELINE
# ══════════════════════════════════════════════════════════════════════════════

def run_pipeline():
    # ── Step 1: Detect Model & Fetch Data ──────────────────────────────────────
    model_name = get_loaded_model_name()
    rows = fetch_sheet(SHEET_URL)

    # ── Step 2: Inference ──────────────────────────────────────────────────────
    predictions = []
    latency_log = []

    print(f"\n🚀 Running TextRank with Dense Embeddings on {len(rows)} listings …")
    for row in tqdm(rows, desc="TextRank-Embedding"):
        raw = row["raw_input"]
        sid = row["id"]

        t0 = time.perf_counter()

        description = textrank_summarize_embedding(raw, model_name, N_SUMMARY_SENTENCES)
        specs       = extract_specs(description)
        title       = generate_title(specs)

        elapsed = time.perf_counter() - t0
        latency_log.append(round(elapsed, 5))

        predictions.append({
            "id":                   sid,
            "raw_input_cleaned":    raw,
            "predicted_title":      title,
            "predicted_description":description,
            "extracted_specs":      specs,
            "gt_title":             row["gt_title"],
            "gt_description":       row["gt_description"],
        })

    print(f"\n⏱️  Average latency : {np.mean(latency_log):.4f} s/listing")
    print(f"⏱️  Total time      : {sum(latency_log):.3f} s")

    # ── Step 3: Compute ROUGE-L locally ─────────────────────────────────────────
    rouge_results = compute_rouge(predictions)
    print(f"📊 ROUGE-L score: {rouge_results}")

    # ── Step 4: Save predictions ──────────────────────────────────────────────
    # Clean output by removing ground truth fields
    output_predictions = []
    for p in predictions:
        output_predictions.append({
            "id":                    p["id"],
            "raw_input_cleaned":     p["raw_input_cleaned"],
            "predicted_title":       p["predicted_title"],
            "predicted_description": p["predicted_description"],
            "extracted_specs":       p["extracted_specs"],
        })

    pred_path = OUTPUT_DIR / "Nhan_TextRank_Embedding_predictions.json"
    with open(pred_path, "w", encoding="utf-8") as f:
        json.dump(output_predictions, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Saved predictions to: {pred_path}")

    # ── Step 5: Save performance metadata (skipping LLM judge for now) ────────
    performance = {
        "model_name":                 f"TextRank (Semantic Embedding: {model_name})",
        "algorithm":                  "Graph-based Semantic Extractive Summarization",
        "n_listings_processed":       len(predictions),
        "average_latency_seconds":    round(float(np.mean(latency_log)), 5),
        "total_time_seconds":         round(float(sum(latency_log)), 3),
        "underthesea_available":      HAS_UNDERTHESEA,
        "local_evaluation_results":   {
            "rouge_l": rouge_results
        },
        "note":                       "LLM Judge scoring skipped to allow fair scoring using Gemma 4 after script runs completed."
    }
    
    perf_path = OUTPUT_DIR / "Nhan_TextRank_Embedding_performance.json"
    with open(perf_path, "w", encoding="utf-8") as f:
        json.dump(performance, f, ensure_ascii=False, indent=2)
    print(f"💾 Saved performance report to: {perf_path}")

    # ── Step 6: Preview first 3 results ──────────────────────────────────────
    print("\n" + "═" * 68)
    print("📋 SAMPLE PREDICTIONS (first 3)")
    print("═" * 68)
    for p in predictions[:3]:
        print(f"\n🆔  {p['id']}")
        print(f"📌  TITLE : {p['predicted_title']}")
        print(f"📝  DESC  : {p['predicted_description'][:200]}…")
        print(f"📊  SPECS : {p['extracted_specs']}")
        print("─" * 68)

    print("\n✅ Pipeline complete!\n")
    return predictions, performance


if __name__ == "__main__":
    run_pipeline()
