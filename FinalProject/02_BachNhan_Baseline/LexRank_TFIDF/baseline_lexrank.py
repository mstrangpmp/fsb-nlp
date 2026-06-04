"""
==============================================================================
02 - Bách Nhân Baseline: LexRank for Vietnamese Real-Estate Summarization
==============================================================================
Pipeline:
  1. Pull newest data from Google Sheets (public CSV export)
  2. Run Vietnamese LexRank on raw descriptions
  3. Extract specs (price, area, floors, alley type, …) via regex directly from raw input text (not from the summarized description)
  4. Generate standardised title
  5. Evaluate ROUGE-L against ground truth (when available)
  6. Save:
       - Nhan_LexRank_predictions.json
       - Nhan_LexRank_performance.json

Usage:
    pip install underthesea scikit-learn rouge-score numpy requests tqdm
    python baseline_lexrank.py
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

# ── Optional: underthesea for Vietnamese word-tokenization ────────────────────
try:
    from underthesea import word_tokenize, sent_tokenize as vi_sent_tokenize
    HAS_UNDERTHESEA = True
    print("✅ underthesea loaded — using Vietnamese word tokenizer")
except ImportError:
    HAS_UNDERTHESEA = False
    print("⚠️  underthesea not found — falling back to simple sentence splitter")

# ── Optional: rouge-score for evaluation ──────────────────────────────────────
try:
    from rouge_score import rouge_scorer as rs_module
    HAS_ROUGE = True
except ImportError:
    HAS_ROUGE = False
    print("⚠️  rouge-score not found — skipping ROUGE-L evaluation")

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ══════════════════════════════════════════════════════════════════════════════
# 0. CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

SHEET_ID   = "1qoyFArLxQJsSYkMf3_fPKFseOfoFcZlJ4jnf3eZLC3w"
GID        = "0"
SHEET_URL  = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

OUTPUT_DIR = Path(__file__).parent        # same folder as this script
N_SUMMARY_SENTENCES = 3                   # how many sentences to extract per listing
LEXRANK_THRESHOLD = 0.1                    # Cosine similarity threshold for LexRank graph edges


# ══════════════════════════════════════════════════════════════════════════════
# 1. FETCH DATA FROM GOOGLE SHEETS
# ══════════════════════════════════════════════════════════════════════════════

def fetch_sheet(url: str) -> list:
    """
    Download the public Google Sheet as CSV and return list of row dicts.
    Expected columns (Vietnamese):
        Mô tả thô | ID | Tiêu đề chuẩn | Mô tả chuẩn
    """
    print(f"\n📥 Fetching data from Google Sheets …")
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()

    # Google returns UTF-8 with BOM sometimes
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
# 2. VIETNAMESE LEXRANK SUMMARIZER
# ══════════════════════════════════════════════════════════════════════════════

VI_STOPWORDS = {
    "và","hoặc","hay","nhưng","mà","vì","nên","thì","là","có","được","cho",
    "với","của","trong","trên","tại","ở","đến","từ","bởi","theo","để","về",
    "ra","vào","lên","xuống","đã","đang","sẽ","rất","cũng","đều","chỉ",
    "này","đó","kia","nào","gì","bán","mua","cần","liên","hệ","ẩn","sđt",
    "anh","chị","em","ace","khách","dẫn","báo","trước","phút","chốt","nhà",
    "chúc","bùng","nổ","thu","bông","gửi","hình","lấy","sổ","quy","trình",
    "cty","chuẩn","hỗ","trợ","tốt","nhất","mong","kết","duyên","cùng",
}


def _extract_sentences(text: str) -> list[str]:
    # First split by newlines as they are natural boundaries in real-estate ads
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    sents = []
    for line in lines:
        if HAS_UNDERTHESEA:
            sents.extend(vi_sent_tokenize(line))
        else:
            # split by punctuation
            parts = re.split(r'(?<=[.!?])\s+', line)
            sents.extend(parts)
    return [s.strip() for s in sents if len(s.strip()) > 12]


def _vi_tokenize(text: str) -> str:
    """Return space-joined tokens for TF-IDF; uses underthesea if available."""
    if HAS_UNDERTHESEA:
        tokens = word_tokenize(text, format="text").lower().split()
    else:
        tokens = re.sub(r'[^\w\s]', ' ', text.lower()).split()
    return " ".join(t for t in tokens if t not in VI_STOPWORDS and len(t) > 1)


def _pagerank(adj: np.ndarray, d: float = 0.85, max_iter: int = 100) -> np.ndarray:
    """Power-iteration PageRank on an adjacency matrix."""
    n = adj.shape[0]
    row_sum = adj.sum(axis=1, keepdims=True)
    
    # Handle sink/isolated nodes by assigning uniform transitions
    row_sum[row_sum == 0] = 1
    trans = adj / row_sum
    
    # If a row was all zeros, distribute uniform probability across all nodes
    for i in range(n):
        if adj[i].sum() == 0:
            trans[i] = np.ones(n) / n
            
    scores = np.ones(n) / n
    for _ in range(max_iter):
        new_s = (1 - d) / n + d * trans.T @ scores
        if np.linalg.norm(new_s - scores) < 1e-6:
            break
        scores = new_s
    return scores


# Blacklist patterns — sentences containing these are excluded from ranking
_BLACKLIST_RE = re.compile(
    r'(liên hệ|sđt|alo|zalo|facebook|inbox|báo trước|dẫn khách'
    r'|ký phiếu|quy trình|đầu chủ|thiên khôi|hoa hồng|chúc ace'
    r'|chốt bùng|thu bông|hỗ trợ tốt nhất|khảo sát)',
    re.IGNORECASE
)

# Sentences containing these terms get a PageRank score boost
_PRIORITY_TERMS = (
    "diện tích", "kết cấu", "hẻm", "mặt tiền", "sổ hồng",
    "pháp lý", "hoàn công", "giá", "tầng", "phòng ngủ",
    "vị trí", "phường", "quận",
)


def lexrank_summarize(text: str, n_sentences: int = 3, threshold: float = LEXRANK_THRESHOLD) -> str:
    """
    Vietnamese LexRank extractive summarization.
    Computes cosine similarity of TF-IDF vectors, applies a threshold,
    and runs PageRank. Returns top-N sentences in original order.
    """
    sentences = _extract_sentences(text)

    # Filter out boilerplate / agent-instructions
    sentences = [s for s in sentences if not _BLACKLIST_RE.search(s)]

    if not sentences:
        return text.strip()[:400]
    if len(sentences) <= n_sentences:
        return " ".join(sentences)

    tokenized = [_vi_tokenize(s) for s in sentences]

    try:
        vec = TfidfVectorizer(min_df=1)
        tfidf = vec.fit_transform(tokenized)
    except ValueError:
        return " ".join(sentences[:n_sentences])

    sim = cosine_similarity(tfidf, tfidf).astype(float)
    np.fill_diagonal(sim, 0)

    # Thresholding: Keep only edges with similarity above the threshold
    # Binary LexRank: Adjacency matrix has 1 if similarity > threshold, else 0
    adj = (sim > threshold).astype(float)

    scores = _pagerank(adj)

    # Priority boost: sentences mentioning key real-estate terms
    for i, sent in enumerate(sentences):
        sl = sent.lower()
        bonus = sum(0.05 for term in _PRIORITY_TERMS if term in sl)
        scores[i] += bonus

    top_idx = sorted(np.argsort(scores)[-n_sentences:].tolist())
    return " ".join(sentences[i] for i in top_idx)


# ══════════════════════════════════════════════════════════════════════════════
# 3. REGEX SPEC EXTRACTION
# ══════════════════════════════════════════════════════════════════════════════

def extract_specs_from_header(line: str) -> dict:
    specs = {}
    lower_line = line.lower().strip()
    street_name = None
    rest = line

    # Match CMT8 / 3 Tháng 2
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
        # Match capitalized words at the start
        m = re.match(r'^([A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝĂĐƠƯẠẶẤẦẨẪẬẮẰẲẴẶẸẼẾỀỂỄỆỈỊỌỎỐỒỔỖỘỚỜỞỠỢỤỦỨỪỬỮỰỲỴỶỸ][a-zA-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝĂĐƠƯẠẶẤẦẨẪẬẮẰẲẴẶẸẼẾỀỂỄỆỈỊỌỎỐỒỔỖỘỚỜỞỠỢỤỦỨỪỬỮỰỲỴỶỸa-zàáâãèéêìíòóôõùúýăđơưạặấầẩẫậắằẳẵặẹẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ\s\-\,\.]+?)(?=\s+\d)', line)
        if m:
            street_name = m.group(1).strip().rstrip(',')
            rest = line[m.end():]

    if street_name:
        specs["duong"] = street_name

    # Extract all numbers from the rest of the line
    num_matches = re.findall(r'\d+(?:[.,/]\d+)*', rest)
    if len(num_matches) >= 5:
        if "tỷ" in lower_line or "ty" in lower_line or "tỷ" in rest.lower() or "ty" in rest.lower():
            # Parse area
            area_str = num_matches[0]
            if "/" in area_str:
                area_str = area_str.split("/")[0]
            try:
                specs["dien_tich_m2"] = float(area_str.replace(',', '.'))
            except ValueError:
                pass

            # Parse floors
            try:
                specs["so_tang"] = int(num_matches[1])
            except ValueError:
                pass

            # Parse width
            width_str = num_matches[2]
            if "/" in width_str:
                width_str = width_str.split("/")[0]
            try:
                specs["mat_tien_m"] = float(width_str.replace(',', '.'))
            except ValueError:
                pass

            # Parse length
            try:
                specs["chieu_sau_m"] = float(num_matches[3].replace(',', '.'))
            except ValueError:
                pass

            # Parse price
            try:
                specs["gia_ty"] = float(num_matches[4].replace(',', '.'))
            except ValueError:
                pass

    return specs


def extract_specs(text: str) -> dict:
    """
    Extract specifications directly from the RAW input text using regular expressions (Regex).
    Note: Regex is run on the RAW input text, not the summarized description, to ensure
    no critical property dimensions/specs are missed due to sentence extraction/summarization.
    """
    t = text.lower()
    first_line = text.strip().splitlines()[0] if text.strip() else ""

    # 1. Fallback / general regex extraction
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

    # 2. Merge / overwrite with header-extracted specs
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


# ══════════════════════════════════════════════════════════════════════════════
# 4. TITLE GENERATION
# ══════════════════════════════════════════════════════════════════════════════

def generate_title(specs: dict) -> str:
    parts = []

    # Location
    loc = " ".join(filter(None, [specs.get("duong"), specs.get("quan")]))
    if loc:
        parts.append(loc)

    # Area
    dt = specs.get("dien_tich_m2")
    ngang = specs.get("mat_tien_m")
    custom_sau = specs.get("chieu_sau_m")
    if dt:
        dim = f"{dt}m2"
        if ngang and custom_sau:
            dim += f" ({ngang}x{custom_sau})"
        elif ngang:
            dim += f" ({ngang}m ngang)"
        parts.append(dim)

    # Alley type
    hem = specs.get("phan_loai_hem")
    if hem:
        parts.append(hem)

    # Floors
    tang = specs.get("so_tang")
    if tang:
        parts.append(f"{tang} tầng")

    # Price
    gia = specs.get("gia_ty")
    if gia:
        parts.append(f"{gia} Tỷ")

    return " - ".join(parts) if parts else "Bất động sản cần bán"


# ══════════════════════════════════════════════════════════════════════════════
# 5. MAIN PIPELINE
# ══════════════════════════════════════════════════════════════════════════════

def run_pipeline():
    # ── Step 1: Fetch ──────────────────────────────────────────────────────────
    rows = fetch_sheet(SHEET_URL)

    # ── Step 2: Inference ──────────────────────────────────────────────────────
    predictions = []
    latency_log = []

    print(f"\n🚀 Running LexRank on {len(rows)} listings …")
    for row in tqdm(rows, desc="LexRank"):
        raw = row["raw_input"]
        sid = row["id"]

        t0 = time.perf_counter()

        description = lexrank_summarize(raw, N_SUMMARY_SENTENCES, LEXRANK_THRESHOLD)
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

    # ── Step 3: Comprehensive Evaluation (ROUGE-L, BERTScore, Local LLM Judge) ─
    import sys
    sys.path.append(str(Path(__file__).parent.parent.parent))
    from evaluation import RealEstateEvaluator

    evaluator = RealEstateEvaluator()
    eval_results = evaluator.evaluate_dataset(predictions, model_local="google/gemma-4-e4b")

    # ── Step 4: Save predictions ──────────────────────────────────────────────
    dod_predictions = []
    for p in predictions:
        dod_predictions.append({
            "id":                    p["id"],
            "raw_input_cleaned":     p["raw_input_cleaned"],
            "predicted_title":       p["predicted_title"],
            "predicted_description": p["predicted_description"],
            "extracted_specs":       p["extracted_specs"],
        })

    pred_path = OUTPUT_DIR / "Nhan_LexRank_predictions.json"
    with open(pred_path, "w", encoding="utf-8") as f:
        json.dump(dod_predictions, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Saved: {pred_path}  ({len(dod_predictions)} records)")

    # ── Step 5: Save performance ──────────────────────────────────────────────
    performance = {
        "model_name":                 "LexRank (Vietnamese TF-IDF + PageRank + Cosine Similarity Thresholding)",
        "algorithm":                  "Thresholded Graph-based Extractive Summarization",
        "underthesea_available":      HAS_UNDERTHESEA,
        "n_listings_processed":       len(predictions),
        "average_latency_seconds":    round(float(np.mean(latency_log)), 5),
        "total_time_seconds":         round(float(sum(latency_log)), 3),
        "estimated_cost_vnd_per_1k":  0,
        "latency_per_sample":         latency_log,
        "evaluation_results":         eval_results,
    }
    perf_path = OUTPUT_DIR / "Nhan_LexRank_performance.json"
    with open(perf_path, "w", encoding="utf-8") as f:
        json.dump(performance, f, ensure_ascii=False, indent=2)
    print(f"💾 Saved: {perf_path}")

    # ── Step 6: Preview first 3 results ──────────────────────────────────────
    print("\n" + "═" * 68)
    print("📋 SAMPLE PREDICTIONS (first 3)")
    print("═" * 68)
    for p in predictions[:3]:
        print(f"\n🆔  {p['id']}")
        print(f"📌  TITLE : {p['predicted_title']}")
        print(f"📝  DESC  : {p['predicted_description'][:200]}…")
        specs = p["extracted_specs"]
        print(f"📊  SPECS : {specs}")
        if p.get("gt_title"):
            print(f"✅  GT    : {p['gt_title']}")
        print("─" * 68)

    print("\n✅ Pipeline complete!\n")
    return predictions, performance


# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    run_pipeline()
