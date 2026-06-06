import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

test_ids = [
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

# Xác định BASE_DIR động để chạy được trên mọi máy sau khi clone
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)

paths = {
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

# 1. Load raw inputs
test_dataset_path = os.path.join(BASE_DIR, "01_HuynhTrang_PM/test_dataset.json")
with open(test_dataset_path, 'r', encoding='utf-8') as f:
    raw_data = json.load(f)

samples_info = {}
for item in raw_data:
    iid = item.get("id") or item.get("ID")
    if iid in test_ids:
        raw_input = item.get("raw_input_cleaned", "")
        first_line = raw_input.strip().splitlines()[0] if raw_input.strip() else iid
        label = f"{iid} - {first_line[:55]}..." if len(first_line) > 55 else f"{iid} - {first_line}"
        samples_info[iid] = {
            "id": iid,
            "label": label,
            "raw_input": raw_input
        }

# 2. Load predictions and performance per model for the 9 test IDs
models_data = {}
for model_name, files in paths.items():
    with open(files["pred"], 'r', encoding='utf-8') as f:
        preds = json.load(f)
    with open(files["perf"], 'r', encoding='utf-8') as f:
        perf = json.load(f)
        
    id_to_idx = { (x.get("id") or x.get("ID")): i for i, x in enumerate(preds) }
    
    models_data[model_name] = {}
    
    for tid in test_ids:
        idx = id_to_idx.get(tid, -1)
        if idx == -1:
            continue
        pred_item = preds[idx]
        
        # Title and description
        title = pred_item.get("predicted_title", "").strip()
        desc = pred_item.get("predicted_description", pred_item.get("predicted_summary", "")).strip()
        
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
            title = title_candidate
            desc = "\n".join(desc_lines).strip()

        # Specs
        specs = pred_item.get("extracted_specs", {})
        
        # Performance
        latency = 0.0
        cost = "0đ"
        if model_name == "Baseline":
            latencies = perf.get("latency_per_sample", [])
            if idx < len(latencies):
                latency = latencies[idx]
            cost = "0đ"
        elif model_name == "GPT":
            for p_item in perf:
                if (p_item.get("id") or p_item.get("ID")) == tid:
                    latency = p_item.get("latency_seconds", 0.0)
                    cost_usd = p_item.get("estimated_cost_usd", 0.0)
                    cost = f"~{int(cost_usd * 25400):,}đ"
                    break
        elif model_name == "Gemini":
            latencies = perf.get("latency_per_sample", [])
            if idx < len(latencies):
                latency = latencies[idx]
            cost_val = perf.get("estimated_cost_vnd_per_1k", 0)
            cost = f"~{int(cost_val / 1000)}đ"
        elif model_name in ["ViT5", "PhoBERT"]:
            latencies = perf.get("latency_per_sample", [])
            if idx < len(latencies):
                latency = latencies[idx]
            cost = "0đ (Offline/Colab)"
            
        models_data[model_name][tid] = {
            "title": title,
            "description": desc,
            "specs": specs,
            "latency": latency,
            "cost": cost
        }

# Generate JS data structure
embedded_data = {
    "samples": samples_info,
    "models": models_data,
    "test_ids": test_ids
}

# Complete Standalone HTML template containing embedded_data placeholder
html_template = """<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hệ Thống Trực Quan & Đánh Giá Bất Động Sản NLP - Nhóm 2 - FSB</title>
    <!-- Nhúng Google Fonts Outfit và Inter -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    
    <style>
        /* ══════════════════════════════════════════════════════════════════════════════
           CSS DESIGN SYSTEM & UTILITIES (GLASSMORPHISM DARK THEME)
           ══════════════════════════════════════════════════════════════════════════════ */
        :root {
            --bg-color: #080B16;
            --card-bg: rgba(13, 18, 36, 0.7);
            --card-border: rgba(255, 255, 255, 0.06);
            --text-primary: #F3F4F6;
            --text-secondary: #9CA3AF;
            --accent-blue: #3B82F6;
            --accent-blue-hover: #2563EB;
            --accent-glow: rgba(59, 130, 246, 0.15);
            --success-color: #10B981;
            --success-bg: rgba(16, 185, 129, 0.1);
            --error-color: #EF4444;
            --error-bg: rgba(239, 68, 68, 0.1);
            --gold-color: #FBBF24;
            --glass-blur: blur(16px);
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Inter', sans-serif;
            scrollbar-width: thin;
            scrollbar-color: rgba(255, 255, 255, 0.1) transparent;
        }

        body {
            background-color: var(--bg-color);
            color: var(--text-primary);
            background-image: 
                radial-gradient(circle at 10% 20%, rgba(59, 130, 246, 0.08) 0%, transparent 40%),
                radial-gradient(circle at 90% 80%, rgba(139, 92, 246, 0.06) 0%, transparent 40%);
            background-attachment: fixed;
            min-height: 100vh;
            padding-bottom: 50px;
        }

        h1, h2, h3, h4 {
            font-family: 'Outfit', sans-serif;
            font-weight: 600;
        }

        /* Container & Grid Layout */
        .container {
            max-width: 1600px;
            margin: 0 auto;
            padding: 20px;
        }

        /* Futuristic Header */
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 20px;
            margin-bottom: 30px;
            padding: 24px;
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(139, 92, 246, 0.05));
            border: 1px solid var(--card-border);
            border-radius: 16px;
            backdrop-filter: var(--glass-blur);
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.4);
            position: relative;
            overflow: hidden;
        }

        header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 2px;
            background: linear-gradient(90deg, transparent, var(--accent-blue), transparent);
        }

        .header-info {
            flex: 1;
            min-width: 300px;
            text-align: left;
        }

        header h1 {
            font-size: 2.0rem;
            color: #FFF;
            text-shadow: 0 0 10px rgba(59, 130, 246, 0.3);
            margin-bottom: 8px;
        }

        header p {
            color: var(--text-secondary);
            font-size: 1.0rem;
        }

        .header-actions {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            align-items: center;
        }

        .btn-header-action {
            padding: 8px 16px;
            font-size: 0.85rem;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            color: #FFF !important;
        }

        @media (max-width: 992px) {
            header {
                flex-direction: column;
                text-align: center;
                align-items: center;
            }
            .header-info {
                text-align: center;
            }
            .header-actions {
                justify-content: center;
                width: 100%;
            }
        }

        /* Section Layout: Grid 2 Columns */
        .main-grid {
            display: grid;
            grid-template-columns: 420px 1fr;
            gap: 24px;
            margin-bottom: 30px;
        }

        @media (max-width: 1200px) {
            .main-grid {
                grid-template-columns: 1fr;
            }
        }

        /* Glassmorphism Card Style */
        .card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 24px;
            backdrop-filter: var(--glass-blur);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }

        .card:hover {
            box-shadow: 0 8px 32px rgba(59, 130, 246, 0.08);
        }

        .card-title {
            font-size: 1.25rem;
            color: #FFF;
            margin-bottom: 16px;
            border-left: 4px solid var(--accent-blue);
            padding-left: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        /* Form Controls */
        label {
            display: block;
            font-size: 0.85rem;
            color: var(--text-secondary);
            margin-bottom: 6px;
            font-weight: 500;
        }

        select, textarea, input[type="text"], input[type="number"] {
            width: 100%;
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 8px;
            color: var(--text-primary);
            padding: 10px 12px;
            font-size: 0.95rem;
            outline: none;
            transition: all 0.2s ease;
        }

        select option {
            background-color: #0D1324;
            color: var(--text-primary);
        }

        select:focus, textarea:focus, input:focus {
            border-color: var(--accent-blue);
            background: rgba(255, 255, 255, 0.08);
            box-shadow: 0 0 8px rgba(59, 130, 246, 0.3);
        }

        .form-group {
            margin-bottom: 16px;
        }

        /* Buttons & Actions */
        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: var(--accent-blue);
            color: #FFF;
            border: none;
            border-radius: 8px;
            padding: 12px 20px;
            font-size: 0.95rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
            gap: 8px;
        }

        .btn:hover {
            background: var(--accent-blue-hover);
            transform: translateY(-1px);
        }

        .btn-secondary {
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .btn-secondary:hover {
            background: rgba(255, 255, 255, 0.15);
        }

        /* Raw Text display box */
        .raw-display-box {
            height: 180px;
            overflow-y: auto;
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            padding: 12px;
            font-size: 0.88rem;
            line-height: 1.5;
            color: #D1D5DB;
            white-space: pre-wrap;
        }

        /* Live Leaderboard Table */
        .leaderboard-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }

        .leaderboard-table th {
            text-align: left;
            padding: 12px 10px;
            color: var(--text-secondary);
            font-size: 0.85rem;
            font-weight: 600;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            text-transform: uppercase;
        }

        .leaderboard-table td {
            padding: 14px 10px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            font-size: 0.92rem;
        }

        .leaderboard-table tr:hover {
            background: rgba(255, 255, 255, 0.02);
        }

        .rank-badge {
            display: inline-flex;
            justify-content: center;
            align-items: center;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            font-size: 0.8rem;
            font-weight: bold;
        }

        .rank-1 { background-color: var(--gold-color); color: #000; }
        .rank-2 { background-color: #C0C0C0; color: #000; }
        .rank-3 { background-color: #CD7F32; color: #FFF; }
        .rank-other { background-color: rgba(255, 255, 255, 0.1); color: var(--text-secondary); }

        /* Ground Truth Editor Row */
        .gt-section {
            margin-bottom: 30px;
        }

        .gt-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }

        @media (max-width: 768px) {
            .gt-grid {
                grid-template-columns: 1fr;
            }
        }

        .specs-input-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
        }

        /* 5 Model Comparison Area */
        .comparison-title {
            margin-top: 40px;
            margin-bottom: 20px;
            font-size: 1.5rem;
            text-shadow: 0 0 8px rgba(59, 130, 246, 0.2);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .models-container {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 16px;
            overflow-x: auto;
            padding-bottom: 10px;
        }

        @media (max-width: 1500px) {
            .models-container {
                grid-template-columns: repeat(3, 1fr);
            }
        }

        @media (max-width: 992px) {
            .models-container {
                grid-template-columns: repeat(2, 1fr);
            }
        }

        @media (max-width: 600px) {
            .models-container {
                grid-template-columns: 1fr;
            }
        }

        /* Model Card Detail */
        .model-card {
            background: rgba(13, 22, 47, 0.85);
            border: 1px solid var(--card-border);
            border-radius: 12px;
            padding: 18px;
            display: flex;
            flex-direction: column;
            gap: 14px;
            min-width: 250px;
            position: relative;
        }

        .model-header {
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            padding-bottom: 10px;
        }

        .model-name {
            font-size: 1.15rem;
            color: #FFF;
            font-weight: 700;
        }

        .model-member {
            font-size: 0.78rem;
            color: var(--text-secondary);
            margin-top: 2px;
        }

        /* Performance Tags inside card */
        .perf-badge-row {
            display: flex;
            gap: 6px;
            flex-wrap: wrap;
        }

        .perf-tag {
            font-size: 0.72rem;
            padding: 3px 6px;
            border-radius: 4px;
            font-weight: 500;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.08);
            color: var(--text-secondary);
        }

        .perf-tag.latency {
            color: #60A5FA;
            background: rgba(96, 165, 250, 0.08);
        }

        .perf-tag.cost {
            color: #FBBF24;
            background: rgba(251, 191, 36, 0.08);
        }

        /* Metrics Scores Row */
        .metric-score-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
            background: rgba(255, 255, 255, 0.02);
            border-radius: 8px;
            padding: 8px;
            border: 1px solid rgba(255, 255, 255, 0.04);
        }

        .metric-score-box {
            text-align: center;
        }

        .metric-score-label {
            font-size: 0.68rem;
            color: var(--text-secondary);
            text-transform: uppercase;
        }

        .metric-score-val {
            font-size: 1.05rem;
            font-weight: 700;
            color: var(--accent-blue);
            margin-top: 2px;
        }

        /* Text Content display */
        .model-content-section {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .content-label {
            font-size: 0.75rem;
            color: var(--text-secondary);
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .model-title-text {
            font-size: 0.92rem;
            font-weight: 600;
            color: #FFF;
            line-height: 1.4;
            padding: 8px;
            background: rgba(255, 255, 255, 0.02);
            border-radius: 6px;
        }

        .model-desc-text {
            font-size: 0.85rem;
            line-height: 1.45;
            color: #D1D5DB;
            max-height: 250px;
            overflow-y: auto;
            background: rgba(0, 0, 0, 0.15);
            padding: 8px;
            border-radius: 6px;
            white-space: pre-wrap;
        }

        /* Model Specs Table */
        .model-specs-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.8rem;
        }

        .model-specs-table td {
            padding: 5px 4px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.03);
        }

        .spec-lbl {
            color: var(--text-secondary);
            width: 80px;
        }

        .spec-val {
            text-align: right;
            font-weight: 500;
        }

        /* Highlight classes */
        .spec-match {
            color: var(--success-color);
            background: var(--success-bg);
            border-radius: 3px;
            padding: 1px 4px;
        }

        .spec-mismatch {
            color: var(--error-color);
            background: var(--error-bg);
            border-radius: 3px;
            padding: 1px 4px;
        }

        /* Rank Panel */
        .rank-panel {
            margin-top: 30px;
            border: 1px dashed var(--accent-blue);
            background: rgba(59, 130, 246, 0.03);
        }

        .rank-selector-row {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            margin-bottom: 16px;
        }

        @media (max-width: 768px) {
            .rank-selector-row {
                grid-template-columns: 1fr;
            }
        }

        /* Modal Styles (Formula display) */
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.85);
            backdrop-filter: blur(8px);
            z-index: 1000;
            display: flex;
            justify-content: center;
            align-items: center;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.3s ease;
        }

        .modal-overlay.active {
            opacity: 1;
            pointer-events: auto;
        }

        .modal {
            background: #0D1324;
            border: 1px solid var(--card-border);
            width: 90%;
            max-width: 700px;
            border-radius: 16px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
            position: relative;
            transform: scale(0.9);
            transition: transform 0.3s ease;
            max-height: 85vh;
            overflow-y: auto;
        }

        .modal-overlay.active .modal {
            transform: scale(1);
        }

        .modal-close {
            position: absolute;
            top: 20px;
            right: 20px;
            background: none;
            border: none;
            color: var(--text-secondary);
            font-size: 1.5rem;
            cursor: pointer;
        }

        .modal-close:hover {
            color: #FFF;
        }

        .formula-card {
            background: rgba(255, 255, 255, 0.03);
            border-radius: 8px;
            padding: 16px;
            margin-top: 14px;
            border-left: 4px solid var(--accent-blue);
        }

        /* Toast Notification */
        .toast {
            position: fixed;
            bottom: 24px;
            right: 24px;
            background: #10B981;
            color: #FFF;
            padding: 14px 24px;
            border-radius: 8px;
            font-weight: 600;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            transform: translateY(100px);
            opacity: 0;
            transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            z-index: 2000;
        }

        .toast.show {
            transform: translateY(0);
            opacity: 1;
        }
    </style>
</head>
<body>

<div class="container">
    <!-- Header banner -->
    <header>
        <div class="header-info">
            <h1>ĐỀ ÁN NLP NHÓM 2 - BẢNG SO SÁNH & ĐÁNH GIÁ 5 MÔ HÌNH</h1>
            <p>Hệ thống trực quan hóa 9 căn test mẫu, nhập Ground Truth động và ghi nhận xếp hạng Winner của chuyên gia</p>
        </div>
        
        <!-- Action buttons in header (including Proposal link) -->
        <div class="header-actions">
            <a href="../NLP_FinalProject_Team2.html" class="btn btn-secondary btn-header-action">
                📄 Đề Xuất Đề Án
            </a>
            <button class="btn btn-secondary btn-header-action" onclick="exportLocalStorageData()">
                📥 Xuất JSON
            </button>
            <button class="btn btn-secondary btn-header-action" style="position: relative; overflow: hidden;">
                📤 Nhập JSON
                <input type="file" id="import-file-input" style="position: absolute; top: 0; left: 0; opacity: 0; cursor: pointer; width: 100%; height: 100%;" onchange="importLocalStorageData(event)">
            </button>
        </div>
    </header>

    <!-- Top Layout: Control Panel & Leaderboard -->
    <div class="main-grid">
        <!-- Control Panel (Left) -->
        <div class="card">
            <h2 class="card-title">1. Chọn & Nạp Dữ Liệu</h2>
            <div class="form-group">
                <label for="sample-select">Danh sách 9 căn nhà mẫu (Tập kiểm thử):</label>
                <select id="sample-select">
                    <option value="" disabled selected>Chọn căn mẫu...</option>
                </select>
            </div>
            <div class="form-group">
                <label>Nội dung văn bản tin thô đầu vào:</label>
                <div id="raw-display" class="raw-display-box">Hãy chọn một căn nhà từ danh sách ở trên để hiển thị tin đăng thô.</div>
            </div>
            
            <button class="btn btn-secondary" style="width: 100%; margin-top: 10px;" onclick="openFormulaModal()">
                📊 Xem Công Thức & Cách Tính Điểm
            </button>
        </div>

        <!-- Leaderboard (Right) -->
        <div class="card">
            <h2 class="card-title">
                🏆 Bảng Xếp Hạng Hiệu Năng Thực Tế (Live Leaderboard)
            </h2>
            <div style="overflow-x: auto;">
                <table class="leaderboard-table">
                    <thead>
                        <tr>
                            <th>Hạng</th>
                            <th>Mô Hình</th>
                            <th>Điểm Tổng Hợp (Thang 100)</th>
                            <th>Điểm Chuyên Gia (TC6)</th>
                            <th>ROUGE-L (TC1)</th>
                            <th>Specs Acc (TC3)</th>
                            <th>BERTScore (TC2)</th>
                            <th>Độ Trễ (TC4)</th>
                            <th>Chi Phí (TC5)</th>
                        </tr>
                    </thead>
                    <tbody id="leaderboard-body">
                        <tr>
                            <td colspan="9" style="text-align: center; color: var(--text-secondary); padding: 40px 0;">
                                Đang tính toán dữ liệu xếp hạng...
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- Ground Truth Editor Section -->
    <div class="card gt-section">
        <h2 class="card-title">2. Biên Tập Nhãn Chuẩn (Ground Truth Editor)</h2>
        <div class="gt-grid">
            <!-- Left GT Column: Title & Description -->
            <div class="form-group" style="display: flex; flex-direction: column; height: 100%;">
                <div class="form-group" style="margin-bottom: 12px;">
                    <label for="gt-title">Tiêu đề chuẩn nhãn (Tiêu đề đích):</label>
                    <input type="text" id="gt-title" placeholder="Chuyên gia điền tiêu đề chuẩn tại đây...">
                </div>
                <div class="form-group" style="display: flex; flex-direction: column; flex-grow: 1; margin-bottom: 0;">
                    <label for="gt-desc">Mô tả chuẩn nhãn (Văn bản đích):</label>
                    <textarea id="gt-desc" placeholder="Chuyên gia điền mô tả chuẩn tại đây..." style="flex-grow: 1; min-height: 120px; height: 100%; resize: vertical;"></textarea>
                </div>
            </div>
            <!-- Right GT Column: 9 Specs -->
            <div>
                <label style="margin-bottom: 10px;">Trích xuất thông số nhãn chuẩn (9 trường cốt lõi):</label>
                <div class="specs-input-grid">
                    <div class="form-group">
                        <label for="gt-spec-duong">Đường</label>
                        <input type="text" id="gt-spec-duong" placeholder="Tên đường">
                    </div>
                    <div class="form-group">
                        <label for="gt-spec-phuong">Phường</label>
                        <input type="text" id="gt-spec-phuong" placeholder="Phường">
                    </div>
                    <div class="form-group">
                        <label for="gt-spec-quan">Quận</label>
                        <input type="text" id="gt-spec-quan" placeholder="Quận">
                    </div>
                    <div class="form-group">
                        <label for="gt-spec-gia">Giá (tỷ)</label>
                        <input type="number" id="gt-spec-gia" step="0.01" placeholder="Ví dụ: 12.8">
                    </div>
                    <div class="form-group">
                        <label for="gt-spec-dientich">Diện tích (m²)</label>
                        <input type="number" id="gt-spec-dientich" step="0.1" placeholder="Ví dụ: 46.5">
                    </div>
                    <div class="form-group">
                        <label for="gt-spec-sotang">Số tầng</label>
                        <input type="number" id="gt-spec-sotang" step="1" placeholder="Ví dụ: 4">
                    </div>
                    <div class="form-group">
                        <label for="gt-spec-ngang">Mặt tiền (m)</label>
                        <input type="number" id="gt-spec-ngang" step="0.1" placeholder="Ví dụ: 4.6">
                    </div>
                    <div class="form-group">
                        <label for="gt-spec-dai">Chiều sâu (m)</label>
                        <input type="number" id="gt-spec-dai" step="0.1" placeholder="Ví dụ: 10">
                    </div>
                    <div class="form-group">
                        <label for="gt-spec-hem">Phân loại hẻm</label>
                        <select id="gt-spec-hem">
                            <option value="Mặt tiền">Mặt tiền</option>
                            <option value="Hẻm xe hơi">Hẻm xe hơi</option>
                            <option value="Hẻm xe tải">Hẻm xe tải</option>
                            <option value="Hẻm xe máy">Hẻm xe máy</option>
                            <option value="Hẻm thông">Hẻm thông</option>
                        </select>
                    </div>
                </div>
                <div style="text-align: right; margin-top: 10px;">
                    <button id="update-gt-btn" class="btn" onclick="updateGroundTruth()" disabled>
                        💾 Lưu & Cập Nhật Chỉ Số Tự Động
                    </button>
                </div>
            </div>
        </div>
    </div>

    <!-- Models Result Cards Area -->
    <div class="comparison-title">
        <h2>3. So Sánh Kết Quả & Độ Chính Xác Động</h2>
        <span style="font-size: 0.85rem; color: var(--text-secondary); font-weight: normal;">*Thông số tự động tô xanh lá nếu khớp Ground Truth, tô đỏ nếu sai lệch</span>
    </div>
    
    <div class="models-container" id="models-cards-row">
        <!-- 5 cards for models will be rendered dynamically -->
    </div>

    <!-- Expert Judging Ranking Panel -->
    <div class="card rank-panel">
        <h2 class="card-title" style="border-color: var(--accent-blue);">
            🗳️ 4. Xếp Hạng & Chấm Chọn Winner (Anh Khang Chấm)
        </h2>
        <div class="rank-selector-row">
            <div class="form-group">
                <label for="winner-1">🥇 Hạng 1 (Mô hình tốt nhất - được 3 điểm):</label>
                <select id="winner-1">
                    <option value="" disabled selected>-- Chọn mô hình thắng giải Nhất --</option>
                    <option value="Baseline">Baseline TextRank</option>
                    <option value="GPT">GPT-4o mini API</option>
                    <option value="Gemini">Gemini 1.5 Flash API</option>
                    <option value="ViT5">ViT5 Fine-tuned</option>
                    <option value="PhoBERT">PhoBERT Fine-tuned</option>
                </select>
            </div>
            <div class="form-group">
                <label for="winner-2">🥈 Hạng 2 (Đứng thứ hai - được 2 điểm):</label>
                <select id="winner-2">
                    <option value="" disabled selected>-- Chọn mô hình thắng giải Nhì --</option>
                    <option value="Baseline">Baseline TextRank</option>
                    <option value="GPT">GPT-4o mini API</option>
                    <option value="Gemini">Gemini 1.5 Flash API</option>
                    <option value="ViT5">ViT5 Fine-tuned</option>
                    <option value="PhoBERT">PhoBERT Fine-tuned</option>
                </select>
            </div>
            <div class="form-group">
                <label for="winner-3">🥉 Hạng 3 (Đứng thứ ba - được 1 điểm):</label>
                <select id="winner-3">
                    <option value="" disabled selected>-- Chọn mô hình thắng giải Ba --</option>
                    <option value="Baseline">Baseline TextRank</option>
                    <option value="GPT">GPT-4o mini API</option>
                    <option value="Gemini">Gemini 1.5 Flash API</option>
                    <option value="ViT5">ViT5 Fine-tuned</option>
                    <option value="PhoBERT">PhoBERT Fine-tuned</option>
                </select>
            </div>
        </div>
        <div class="form-group">
            <label for="review-comment">Nhận xét chi tiết của Chuyên gia:</label>
            <textarea id="review-comment" placeholder="Điền lý do xếp hạng hoặc nhận xét lỗi cụ thể của từng phiên bản tại đây..." rows="3"></textarea>
        </div>
        <div style="text-align: right;">
            <button id="save-review-btn" class="btn" onclick="saveExpertReview()" disabled>
                🗳️ Gửi & Tích Lũy Bảng Xếp Hạng
            </button>
        </div>
    </div>
</div>

<!-- Modal: Formula & Weightings -->
<div class="modal-overlay" id="formula-modal-overlay" onclick="closeFormulaModal()">
    <div class="modal" onclick="event.stopPropagation()">
        <button class="modal-close" onclick="closeFormulaModal()">&times;</button>
        <h2 style="margin-bottom: 15px; border-bottom: 2px solid var(--accent-blue); padding-bottom: 8px;">
            📊 Cách Tính Điểm & Tỷ Trọng 6 Tiêu Chí
        </h2>
        <p style="font-size: 0.95rem; line-height: 1.5; color: var(--text-secondary);">
            Để xếp hạng tổng hợp hiệu năng của 5 mô hình trên Live Leaderboard, hệ thống chuẩn hóa tất cả tiêu chí về thang điểm 100 và áp dụng tỷ trọng như sau:
        </p>
        
        <table class="leaderboard-table" style="margin: 15px 0;">
            <thead>
                <tr>
                    <th style="padding: 8px 4px;">Tiêu chí</th>
                    <th style="padding: 8px 4px; text-align: center;">Tỷ trọng</th>
                    <th style="padding: 8px 4px;">Phương pháp quy đổi</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><b>TC6: Chuyên gia xếp hạng</b></td>
                    <td style="text-align: center; color: #FFF; font-weight: bold; background: rgba(59, 130, 246, 0.1);">35%</td>
                    <td>Nhất = 100đ, Nhì = 66đ, Ba = 33đ, còn lại = 0đ (sau đó tính trung bình).</td>
                </tr>
                <tr>
                    <td><b>TC3: Độ chính xác thông số</b></td>
                    <td style="text-align: center; color: #FFF; font-weight: bold; background: rgba(59, 130, 246, 0.1);">25%</td>
                    <td>Tỷ lệ % số trường thông số trích xuất đúng so với Ground Truth (9 trường).</td>
                </tr>
                <tr>
                    <td><b>TC2: Độ tương đồng ngữ nghĩa</b></td>
                    <td style="text-align: center; color: #FFF; font-weight: bold;">15%</td>
                    <td>Điểm BERTScore trung bình lịch sử thu được trên tập dữ liệu.</td>
                </tr>
                <tr>
                    <td><b>TC1: Độ chính xác từ vựng</b></td>
                    <td style="text-align: center; color: #FFF; font-weight: bold;">15%</td>
                    <td>Điểm ROUGE-L trung bình giữa mô tả mô hình sinh ra và Ground Truth.</td>
                </tr>
                <tr>
                    <td><b>TC4: Tốc độ xử lý</b></td>
                    <td style="text-align: center; color: #FFF; font-weight: bold;">5%</td>
                    <td>Độ trễ trung bình: 0s = 100đ, tăng lên giảm dần (>=10s = 0đ).</td>
                </tr>
                <tr>
                    <td><b>TC5: Chi phí vận hành</b></td>
                    <td style="text-align: center; color: #FFF; font-weight: bold;">5%</td>
                    <td>Quy đổi: chạy offline local = 100đ, gọi API có phí = 85-90đ.</td>
                </tr>
            </tbody>
        </table>
        
        <div class="formula-card">
            <b>Công thức tính Điểm Tổng Hợp:</b><br>
            <code style="display: block; margin-top: 8px; font-size: 0.95rem; color: #60A5FA; font-weight: bold; word-break: break-all;">
                Điểm = 35%*TC6 + 25%*TC3 + 15%*TC2 + 15%*TC1 + 5%*TC4 + 5%*TC5
            </code>
        </div>
        
        <div style="text-align: right; margin-top: 20px;">
            <button class="btn" onclick="closeFormulaModal()">Đóng Cửa Sổ</button>
        </div>
    </div>
</div>

<!-- Toast Notification -->
<div id="toast" class="toast">Đã thực hiện thao tác!</div>

<script>
    // ══════════════════════════════════════════════════════════════════════════════
    // EMBEDDED DATABASES FOR PURE STATIC RUN
    // ══════════════════════════════════════════════════════════════════════════════
    const DATABASE = <!-- DATABASE_PLACEHOLDER -->;

    // Chuẩn hóa dấu tiếng Việt để đối chiếu chính xác (ví dụ: "Hoà" vs "Hòa")
    function normalizeVietnamese(s) {
        if (!s || typeof s !== 'string') return "";
        s = s.normalize("NFC").toLowerCase().trim();
        const replacements = {
            "òe": "oè", "óe": "oé", "ỏe": "oẻ", "õe": "oẽ", "ọe": "oẹ",
            "òa": "oà", "óa": "oá", "ỏa": "oả", "õa": "oã", "ọa": "oạ",
            "ùy": "uỳ", "úy": "uý", "ủy": "uỷ", "ũy": "uỹ", "ụy": "uỵ"
        };
        for (const k in replacements) {
            s = s.split(k).join(replacements[k]);
        }
        return s;
    }

    let currentSampleId = "";
    let activeModelsData = {};

    // ══════════════════════════════════════════════════════════════════════════════
    // ROUGE-L & SPECS ACCURACY ALGORITHMS (PORTED FROM PYTHON)
    // ══════════════════════════════════════════════════════════════════════════════
    
    function calculateRougeL(pred, ref) {
        if (!pred || !ref) return 0.0;
        
        let pTokens = pred.toLowerCase().replace(/[^\\w\\s]/g, ' ').split(/\\s+/).filter(Boolean);
        let rTokens = ref.toLowerCase().replace(/[^\\w\\s]/g, ' ').split(/\\s+/).filter(Boolean);
        
        let m = pTokens.length;
        let n = rTokens.length;
        if (m === 0 || n === 0) return 0.0;
        
        let dp = Array(m + 1).fill(0).map(() => Array(n + 1).fill(0));
        for (let i = 1; i <= m; i++) {
            for (let j = 1; j <= n; j++) {
                if (pTokens[i - 1] === rTokens[j - 1]) {
                    dp[i][j] = dp[i - 1][j - 1] + 1;
                } else {
                    dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
                }
            }
        }
        
        let lcs = dp[m][n];
        let recall = lcs / n;
        let precision = lcs / m;
        if (recall + precision === 0) return 0.0;
        
        let fmeasure = (2 * recall * precision) / (recall + precision);
        return fmeasure * 100;
    }

    function calculateSpecsAccuracy(predSpecs, refSpecs) {
        if (!refSpecs || !predSpecs) return 0.0;
        
        const keys = ["duong", "phuong", "quan", "gia_ty", "dien_tich_m2", "so_tang", "mat_tien_m", "chieu_sau_m", "phan_loai_hem"];
        let matchCount = 0;
        let totalKeys = keys.length;
        
        keys.forEach(k => {
            let pVal = predSpecs[k];
            let rVal = refSpecs[k];
            
            if (pVal === undefined) pVal = null;
            if (rVal === undefined) rVal = null;
            
            if (pVal === null && rVal === null) {
                matchCount += 1;
                return;
            }
            
            if (pVal !== null && rVal !== null) {
                if (typeof rVal === 'string') {
                    if (normalizeVietnamese(String(pVal)) === normalizeVietnamese(String(rVal))) {
                        matchCount += 1;
                    }
                } else {
                    let pNum = parseFloat(pVal);
                    let rNum = parseFloat(rVal);
                    if (!isNaN(pNum) && !isNaN(rNum)) {
                        if (Math.abs(pNum - rNum) < 0.01) {
                            matchCount += 1;
                        }
                    } else if (String(pVal).trim() === String(rVal).trim()) {
                        matchCount += 1;
                    }
                }
            }
        });
        
        return (matchCount / totalKeys) * 100;
    }

    function robustParseSpecsAgnostic(text) {
        if (!text || typeof text !== 'string') {
            return {
                duong: null, phuong: null, quan: null,
                gia_ty: null, dien_tich_m2: null, so_tang: null,
                mat_tien_m: null, chieu_sau_m: null, phan_loai_hem: 'Hẻm thông'
            };
        }
        
        let t = text.toLowerCase().replace(/\\*/g, '').replace(/#/g, '');
        let specs = {
            duong: null, phuong: null, quan: null,
            gia_ty: null, dien_tich_m2: null, so_tang: null,
            mat_tien_m: null, chieu_sau_m: null, phan_loai_hem: 'Hẻm thông'
        };
        
        // Area
        let areaMatch = t.match(/(?:diện\\s+tích|dt|dt\\s+đất|công\\s+nhận)\\s*(?::|là)?\\s*([\\d.,]+)\\s*(?:m2|m²)/);
        if (areaMatch) specs.dien_tich_m2 = parseFloat(areaMatch[1].replace(',', '.'));
        
        // Kích thước ngang x dài
        let dimMatch = t.match(/(?:kích\\s+thước|ngang|dài)?\\s*([\\d.,]+)\\s*m?\\s*[x×]\\s*([\\d.,]+)\\s*m?/);
        if (dimMatch) {
            specs.mat_tien_m = parseFloat(dimMatch[1].replace(',', '.'));
            specs.chieu_sau_m = parseFloat(dimMatch[2].replace(',', '.'));
        }
        
        // Giá bán
        let priceMatch = t.match(/(?:giá|giá\\s+bán|giá\\s+chào)\\s*(?::|là)?\\s*([\\d.,]+)\\s*(?:tỷ|ty)/);
        if (priceMatch) {
            specs.gia_ty = parseFloat(priceMatch[1].replace(',', '.'));
        } else {
            let m = t.match(/([\\d.,]+)\\s*(?:tỷ|ty)\\b/);
            if (m) specs.gia_ty = parseFloat(m[1].replace(',', '.'));
        }
        
        // Số tầng
        let floorsMatch = t.match(/(?:kết\\s+cấu|quy\\s+mô|nhà)?\\s*(?::|là)?\\s*(\\d+)\\s*(?:tầng|lầu)/);
        if (floorsMatch) {
            specs.so_tang = parseInt(floorsMatch[1]);
        } else {
            let m = t.match(/(\\d+)\\s*trệt\\s*(?:và|[,+])?\\s*(\\d+)\\s*(?:lầu|lửng)/);
            if (m) {
                specs.so_tang = parseInt(m[1]) + parseInt(m[2]);
            } else {
                let m2 = t.match(/trệt\\s*(?:và|[,+])?\\s*(\\d+)\\s*lầu/);
                if (m2) specs.so_tang = 1 + parseInt(m2[1]);
            }
        }
        
        // Hẻm
        if (t.includes('mặt tiền')) specs.phan_loai_hem = 'Mặt tiền';
        else if (t.includes('hẻm xe hơi') || t.includes('hxh') || t.includes('ô tô') || t.includes('oto')) specs.phan_loai_hem = 'Hẻm xe hơi';
        else if (t.includes('hẻm xe tải') || t.includes('hxt')) specs.phan_loai_hem = 'Hẻm xe tải';
        else if (t.includes('xe máy') || t.includes('ba gác')) specs.phan_loai_hem = 'Hẻm xe máy';
        
        // Quận
        let dtMatch = t.match(/quận\\s*(\\d+)\\b/);
        if (dtMatch) {
            specs.quan = 'Quận ' + dtMatch[1];
        } else {
            let districts = ['bình thạnh', 'phú nhuận', 'gò vấp', 'tân bình', 'quận 1', 'quận 3', 'quận 10'];
            for (let d of districts) {
                if (t.includes(d)) {
                    specs.quan = d.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
                    break;
                }
            }
        }
        
        // Phường
        let wdMatch = t.match(/(?:phường|p\\.)\\s*([\\d\\w\\s]+?)(?:,|$|\\n|\\.)/);
        if (wdMatch) specs.phuong = 'Phường ' + wdMatch[1].trim().split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
        
        // Đường
        let stMatch = t.match(/đường\\s+([\\w\\s]+?)(?:,|$|\\n|\\.)/);
        if (stMatch) specs.duong = stMatch[1].trim().split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
        
        return specs;
    }

    // ══════════════════════════════════════════════════════════════════════════════
    // CONTROL WORKFLOW & STORAGE HANDLERS
    // ══════════════════════════════════════════════════════════════════════════════

    document.addEventListener("DOMContentLoaded", () => {
        loadDropdown();
        loadLeaderboard();
        
        document.getElementById("sample-select").addEventListener("change", (e) => {
            loadSampleData(e.target.value);
        });
    });

    function showToast(message, isError = false) {
        const toast = document.getElementById("toast");
        toast.innerText = message;
        toast.style.background = isError ? "var(--error-color)" : "#10B981";
        toast.classList.add("show");
        setTimeout(() => {
            toast.classList.remove("show");
        }, 2500);
    }

    function loadDropdown() {
        const select = document.getElementById("sample-select");
        select.innerHTML = '<option value="" disabled selected>-- Chọn căn nhà mẫu --</option>';
        DATABASE.test_ids.forEach(id => {
            const item = DATABASE.samples[id];
            const opt = document.createElement("option");
            opt.value = id;
            opt.innerText = item.label;
            select.appendChild(opt);
        });
    }

    function loadLeaderboard() {
        const tbody = document.getElementById("leaderboard-body");
        tbody.innerHTML = "";
        
        let reviews = JSON.parse(localStorage.getItem("expert_reviews") || "[]");
        let allGt = JSON.parse(localStorage.getItem("user_ground_truth") || "{}");
        
        let summary = {
            "Baseline": { points: 0, rank_1: 0, rank_2: 0, rank_3: 0, rouge_sum: 0.0, specs_sum: 0.0, bert: 83.98, latency: 100.0, cost: 100.0 },
            "GPT": { points: 0, rank_1: 0, rank_2: 0, rank_3: 0, rouge_sum: 0.0, specs_sum: 0.0, bert: 92.40, latency: 37.8, cost: 85.0 },
            "Gemini": { points: 0, rank_1: 0, rank_2: 0, rank_3: 0, rouge_sum: 0.0, specs_sum: 0.0, bert: 90.15, latency: 81.5, cost: 90.0 },
            "ViT5": { points: 0, rank_1: 0, rank_2: 0, rank_3: 0, rouge_sum: 0.0, specs_sum: 0.0, bert: 79.32, latency: 58.0, cost: 100.0 },
            "PhoBERT": { points: 0, rank_1: 0, rank_2: 0, rank_3: 0, rouge_sum: 0.0, specs_sum: 0.0, bert: 80.12, latency: 91.2, cost: 100.0 }
        };
        
        reviews.forEach(rev => {
            if (rev.winner_1 && summary[rev.winner_1]) { summary[rev.winner_1].points += 3; summary[rev.winner_1].rank_1 += 1; }
            if (rev.winner_2 && summary[rev.winner_2]) { summary[rev.winner_2].points += 2; summary[rev.winner_2].rank_2 += 1; }
            if (rev.winner_3 && summary[rev.winner_3]) { summary[rev.winner_3].points += 1; summary[rev.winner_3].rank_3 += 1; }
        });
        
        let evaluatedIds = Object.keys(allGt).filter(id => allGt[id] && allGt[id].ground_truth_desc && DATABASE.test_ids.includes(id));
        let evaluatedCount = evaluatedIds.length;
        
        evaluatedIds.forEach(id => {
            let gt = allGt[id];
            Object.keys(DATABASE.models).forEach(modelName => {
                let modelData = DATABASE.models[modelName][id];
                if (modelData) {
                    let desc = modelData.description;
                    let mSpecs = modelData.specs;
                    if (!mSpecs || Object.keys(mSpecs).length === 0 || Object.values(mSpecs).every(v => v === null || v === 'Hẻm thông')) {
                        mSpecs = robustParseSpecsAgnostic(desc);
                    }
                    let rScore = calculateRougeL(desc, gt.ground_truth_desc);
                    let sScore = calculateSpecsAccuracy(mSpecs, gt.extracted_specs);
                    
                    summary[modelName].rouge_sum += rScore;
                    summary[modelName].specs_sum += sScore;
                }
            });
        });
        
        let report = Object.keys(summary).map(modelName => {
            let data = summary[modelName];
            let avgRouge = evaluatedCount > 0 ? data.rouge_sum / evaluatedCount : 0.0;
            let avgSpecs = evaluatedCount > 0 ? data.specs_sum / evaluatedCount : 0.0;
            
            let totalReviews = reviews.length;
            let pointsDenominator = totalReviews * 3;
            let sExpert = pointsDenominator > 0 ? (data.points / pointsDenominator * 100) : 0.0;
            
            let sSpecs = avgSpecs;
            let sBert = data.bert;
            let sRouge = avgRouge;
            let sLatency = data.latency;
            let sCost = data.cost;
            
            let overallScore = 0.35 * sExpert + 0.25 * sSpecs + 0.15 * sBert + 0.15 * sRouge + 0.05 * sLatency + 0.05 * sCost;
            
            let realLatency = 0.0;
            if (modelName === "Baseline") realLatency = 0.007;
            else if (modelName === "GPT") realLatency = 6.22;
            else if (modelName === "Gemini") realLatency = 1.85;
            else if (modelName === "ViT5") realLatency = 4.20;
            else if (modelName === "PhoBERT") realLatency = 0.88;
            
            return {
                model_name: modelName,
                points: data.points,
                rank_1: data.rank_1,
                rank_2: data.rank_2,
                rank_3: data.rank_3,
                avg_rouge: avgRouge,
                avg_specs: avgSpecs,
                avg_bert: sBert,
                latency: realLatency.toFixed(3) + "s",
                overall_score: overallScore.toFixed(2)
            };
        });
        
        report.sort((a, b) => parseFloat(b.overall_score) - parseFloat(a.overall_score));
        
        tbody.innerHTML = "";
        if (report.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" style="text-align: center; color: var(--text-secondary);">Chưa có dữ liệu đánh giá nào.</td></tr>';
            return;
        }
        
        report.forEach((row, i) => {
            let rankBadgeClass = "rank-other";
            if (i === 0) rankBadgeClass = "rank-1";
            else if (i === 1) rankBadgeClass = "rank-2";
            else if (i === 2) rankBadgeClass = "rank-3";
            
            const tr = document.createElement("tr");
            const friendlyName = getFriendlyModelName(row.model_name);
            
            tr.innerHTML = `
                <td><span class="rank-badge ${rankBadgeClass}">${i + 1}</span></td>
                <td><strong>${friendlyName}</strong></td>
                <td style="color: var(--accent-blue); font-weight: bold; font-size: 1rem;">${row.overall_score}</td>
                <td>${row.points} đ (${row.rank_1} Nhất | ${row.rank_2} Nhì | ${row.rank_3} Ba)</td>
                <td>${row.avg_rouge.toFixed(1)}%</td>
                <td>${row.avg_specs.toFixed(1)}%</td>
                <td>${row.avg_bert.toFixed(1)}%</td>
                <td>${row.latency}</td>
                <td>${getFriendlyCostDisplay(row.model_name)}</td>
            `;
            tbody.appendChild(tr);
        });
    }

    function loadSampleData(sampleId) {
        currentSampleId = sampleId;
        let sample = DATABASE.samples[sampleId];
        document.getElementById("raw-display").innerText = sample.raw_input;
        
        let allGt = JSON.parse(localStorage.getItem("user_ground_truth") || "{}");
        let gt = allGt[sampleId] || {
            ground_truth_title: "",
            ground_truth_desc: "",
            extracted_specs: {
                duong: null, phuong: null, quan: null,
                gia_ty: null, dien_tich_m2: null, so_tang: null,
                mat_tien_m: null, chieu_sau_m: null, phan_loai_hem: "Hẻm thông"
            }
        };
        
        document.getElementById("gt-title").value = gt.ground_truth_title || "";
        document.getElementById("gt-desc").value = gt.ground_truth_desc || "";
        let specs = gt.extracted_specs || {};
        document.getElementById("gt-spec-duong").value = specs.duong || "";
        document.getElementById("gt-spec-phuong").value = specs.phuong || "";
        document.getElementById("gt-spec-quan").value = specs.quan || "";
        document.getElementById("gt-spec-gia").value = specs.gia_ty !== undefined && specs.gia_ty !== null ? specs.gia_ty : "";
        document.getElementById("gt-spec-dientich").value = specs.dien_tich_m2 !== undefined && specs.dien_tich_m2 !== null ? specs.dien_tich_m2 : "";
        document.getElementById("gt-spec-sotang").value = specs.so_tang !== undefined && specs.so_tang !== null ? specs.so_tang : "";
        document.getElementById("gt-spec-ngang").value = specs.mat_tien_m !== undefined && specs.mat_tien_m !== null ? specs.mat_tien_m : "";
        document.getElementById("gt-spec-dai").value = specs.chieu_sau_m !== undefined && specs.chieu_sau_m !== null ? specs.chieu_sau_m : "";
        document.getElementById("gt-spec-hem").value = specs.phan_loai_hem || "Hẻm thông";
        
        document.getElementById("update-gt-btn").removeAttribute("disabled");
        document.getElementById("save-review-btn").removeAttribute("disabled");
        
        activeModelsData = {};
        Object.keys(DATABASE.models).forEach(modelName => {
            let modelData = DATABASE.models[modelName][sampleId];
            if (modelData) {
                let rouge_l = 0.0;
                let specs_acc = 0.0;
                
                let mSpecs = modelData.specs;
                if (!mSpecs || Object.keys(mSpecs).length === 0 || Object.values(mSpecs).every(v => v === null || v === 'Hẻm thông')) {
                    mSpecs = robustParseSpecsAgnostic(modelData.description);
                }
                
                if (gt.ground_truth_desc) {
                    rouge_l = calculateRougeL(modelData.description, gt.ground_truth_desc);
                    specs_acc = calculateSpecsAccuracy(mSpecs, gt.extracted_specs);
                }
                
                let bertscore = 83.98;
                if (modelName === "GPT") bertscore = 92.40;
                else if (modelName === "Gemini") bertscore = 90.15;
                else if (modelName === "ViT5") bertscore = 79.32;
                else if (modelName === "PhoBERT") bertscore = 80.12;
                
                activeModelsData[modelName] = {
                    model_name: modelName,
                    title: modelData.title,
                    description: modelData.description,
                    specs: mSpecs,
                    latency: modelData.latency,
                    cost: modelData.cost,
                    bertscore: bertscore,
                    rouge_l: rouge_l,
                    specs_acc: specs_acc
                };
            }
        });
        
        renderModelCards(activeModelsData, specs);
        
        let reviews = JSON.parse(localStorage.getItem("expert_reviews") || "[]");
        let rev = reviews.find(r => r.id === sampleId) || {};
        document.getElementById("winner-1").value = rev.winner_1 || "";
        document.getElementById("winner-2").value = rev.winner_2 || "";
        document.getElementById("winner-3").value = rev.winner_3 || "";
        document.getElementById("review-comment").value = rev.comment || "";
    }

    function renderModelCards(models, gtSpecs) {
        const container = document.getElementById("models-cards-row");
        container.innerHTML = "";

        const orderedModels = ["Baseline", "GPT", "Gemini", "ViT5", "PhoBERT"];

        orderedModels.forEach(mKey => {
            const m = models[mKey];
            if (!m) return;

            const card = document.createElement("div");
            card.className = "model-card";
            
            const specsHtml = renderSpecsTableWithHighlights(m.specs, gtSpecs);
            const friendlyName = getFriendlyModelName(mKey);
            const author = getFriendlyAuthor(mKey);

            card.innerHTML = `
                <div class="model-header">
                    <div class="model-name">${friendlyName}</div>
                    <div class="model-member">Thực hiện: ${author}</div>
                </div>
                
                <div class="perf-badge-row">
                    <span class="perf-tag latency">⏱️ ${m.latency.toFixed(3)}s</span>
                    <span class="perf-tag cost">💵 ${m.cost}</span>
                </div>
                
                <div class="metric-score-row">
                    <div class="metric-score-box">
                        <div class="metric-score-label">ROUGE-L</div>
                        <div class="metric-score-val">${m.rouge_l > 0 ? m.rouge_l.toFixed(1) + '%' : '0.0%'}</div>
                    </div>
                    <div class="metric-score-box">
                        <div class="metric-score-label">Specs Acc</div>
                        <div class="metric-score-val">${m.specs_acc > 0 ? m.specs_acc.toFixed(1) + '%' : '0.0%'}</div>
                    </div>
                </div>

                <div class="model-content-section">
                    <span class="content-label">Tiêu đề xuất bản</span>
                    <div class="model-title-text">${m.title || '<i>(Không tạo tiêu đề)</i>'}</div>
                </div>

                <div class="model-content-section">
                    <span class="content-label">Mô tả chuẩn hóa</span>
                    <div class="model-desc-text">${m.description}</div>
                </div>

                <div class="model-content-section">
                    <span class="content-label">Thông số trích xuất</span>
                    ${specsHtml}
                </div>
            `;
            container.appendChild(card);
        });
    }

    function renderSpecsTableWithHighlights(modelSpecs, gtSpecs) {
        const fields = [
            { key: "duong", label: "Đường" },
            { key: "phuong", label: "Phường" },
            { key: "quan", label: "Quận" },
            { key: "gia_ty", label: "Giá (tỷ)" },
            { key: "dien_tich_m2", label: "Diện tích" },
            { key: "so_tang", label: "Số tầng" },
            { key: "mat_tien_m", label: "Ngang (m)" },
            { key: "chieu_sau_m", label: "Dài (m)" },
            { key: "phan_loai_hem", label: "Loại hẻm" }
        ];

        let html = '<table class="model-specs-table"><tbody>';

        fields.forEach(f => {
            const mVal = modelSpecs[f.key];
            const gtVal = gtSpecs[f.key];
            
            let displayVal = mVal !== undefined && mVal !== null ? mVal : "-";
            if (f.key === "dien_tich_m2" && mVal) displayVal += " m²";
            
            let highlightClass = "";
            if (gtVal !== undefined && gtVal !== null && gtVal !== "") {
                let isMatch = false;
                if (typeof gtVal === 'string') {
                    isMatch = normalizeVietnamese(String(mVal)) === normalizeVietnamese(String(gtVal));
                } else {
                    isMatch = Math.abs(parseFloat(mVal) - parseFloat(gtVal)) < 0.01;
                }
                highlightClass = isMatch ? "spec-match" : "spec-mismatch";
            }

            html += `
                <tr>
                    <td class="spec-lbl">${f.label}</td>
                    <td class="spec-val"><span class="${highlightClass}">${displayVal}</span></td>
                </tr>
            `;
        });

        html += '</tbody></table>';
        return html;
    }

    function updateGroundTruth() {
        if (!currentSampleId) return;

        const gtTitle = document.getElementById("gt-title").value.trim();
        const gtDesc = document.getElementById("gt-desc").value.trim();
        const specs = {
            duong: document.getElementById("gt-spec-duong").value.trim() || null,
            phuong: document.getElementById("gt-spec-phuong").value.trim() || null,
            quan: document.getElementById("gt-spec-quan").value.trim() || null,
            gia_ty: getNumericValue("gt-spec-gia"),
            dien_tich_m2: getNumericValue("gt-spec-dientich"),
            so_tang: getIntegerValue("gt-spec-sotang"),
            mat_tien_m: getNumericValue("gt-spec-ngang"),
            chieu_sau_m: getNumericValue("gt-spec-dai"),
            phan_loai_hem: document.getElementById("gt-spec-hem").value
        };

        if (!gtTitle) {
            showToast("Vui lòng điền tiêu đề chuẩn nhãn!", true);
            return;
        }
        if (!gtDesc) {
            showToast("Vui lòng điền mô tả chuẩn nhãn để tính điểm từ vựng!", true);
            return;
        }

        let allGt = JSON.parse(localStorage.getItem("user_ground_truth") || "{}");
        allGt[currentSampleId] = {
            ground_truth_title: gtTitle,
            ground_truth_desc: gtDesc,
            extracted_specs: specs
        };
        
        localStorage.setItem("user_ground_truth", JSON.stringify(allGt));
        showToast("Đã cập nhật Ground Truth & tính lại chỉ số!");
        
        loadSampleData(currentSampleId);
        loadLeaderboard();
    }

    function saveExpertReview() {
        if (!currentSampleId) return;

        const w1 = document.getElementById("winner-1").value;
        const w2 = document.getElementById("winner-2").value;
        const w3 = document.getElementById("winner-3").value;
        const comment = document.getElementById("review-comment").value.trim();

        if (!w1 || !w2 || !w3) {
            showToast("Vui lòng chọn đầy đủ xếp hạng Hạng 1, 2 và 3!", true);
            return;
        }

        if (w1 === w2 || w1 === w3 || w2 === w3) {
            showToast("Mô hình được chọn xếp hạng không được trùng nhau!", true);
            return;
        }

        let reviews = JSON.parse(localStorage.getItem("expert_reviews") || "[]");
        let idx = reviews.findIndex(r => r.id === currentSampleId);
        
        let reviewItem = {
            id: currentSampleId,
            winner_1: w1,
            winner_2: w2,
            winner_3: w3,
            comment: comment,
            timestamp: new Date().toISOString().replace('T', ' ').substring(0, 19)
        };
        
        if (idx !== -1) {
            reviews[idx] = reviewItem;
        } else {
            reviews.push(reviewItem);
        }
        
        localStorage.setItem("expert_reviews", JSON.stringify(reviews));
        showToast("Đã lưu xếp hạng của chuyên gia!");
        loadLeaderboard();
    }

    // ══════════════════════════════════════════════════════════════════════════════
    // DATA EXPORT & IMPORT HANDLERS (BACKUP JSON)
    // ══════════════════════════════════════════════════════════════════════════════
    
    function exportLocalStorageData() {
        let data = {
            user_ground_truth: JSON.parse(localStorage.getItem("user_ground_truth") || "{}"),
            expert_reviews: JSON.parse(localStorage.getItem("expert_reviews") || "[]")
        };
        
        let dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(data, null, 2));
        let downloadAnchor = document.createElement('a');
        downloadAnchor.setAttribute("href", dataStr);
        downloadAnchor.setAttribute("download", `NLP_Showcase_Backup_${new Date().toISOString().slice(0,10)}.json`);
        document.body.appendChild(downloadAnchor);
        downloadAnchor.click();
        downloadAnchor.remove();
        showToast("Đã xuất file lưu trữ dữ liệu!");
    }
    
    function importLocalStorageData(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        const reader = new FileReader();
        reader.onload = function(e) {
            try {
                const imported = JSON.parse(e.target.result);
                if (imported.user_ground_truth) {
                    localStorage.setItem("user_ground_truth", JSON.stringify(imported.user_ground_truth));
                }
                if (imported.expert_reviews) {
                    localStorage.setItem("expert_reviews", JSON.stringify(imported.expert_reviews));
                }
                showToast("Đã nhập dữ liệu lưu trữ thành công!");
                loadLeaderboard();
                if (currentSampleId) loadSampleData(currentSampleId);
            } catch (err) {
                showToast("File JSON không đúng định dạng hoặc bị lỗi!", true);
            }
        };
        reader.readAsText(file);
    }

    // ══════════════════════════════════════════════════════════════════════════════
    // HELPERS
    // ══════════════════════════════════════════════════════════════════════════════
    
    function getNumericValue(id) {
        const val = document.getElementById(id).value;
        return val !== "" ? parseFloat(val) : null;
    }

    function getIntegerValue(id) {
        const val = document.getElementById(id).value;
        return val !== "" ? parseInt(val) : null;
    }

    function getFriendlyModelName(key) {
        const mapping = {
            "Baseline": "Baseline TextRank",
            "GPT": "GPT-4o mini API",
            "Gemini": "Gemini 1.5 Flash",
            "ViT5": "ViT5 Fine-tuned",
            "PhoBERT": "PhoBERT Fine-tuned"
        };
        return mapping[key] || key;
    }

    // Tác giả
    function getFriendlyAuthor(key) {
        const mapping = {
            "Baseline": "Bách Nhân",
            "GPT": "Minh Quân",
            "Gemini": "Ba Học",
            "ViT5": "Mai Anh",
            "PhoBERT": "Hữu Hiếu"
        };
        return mapping[key] || "N/A";
    }

    // Chi phí
    function getFriendlyCostDisplay(key) {
        const mapping = {
            "Baseline": "0đ",
            "GPT": "~15đ/tin",
            "Gemini": "~15đ/tin",
            "ViT5": "0đ (Offline)",
            "PhoBERT": "0đ (Offline)"
        };
        return mapping[key] || "-";
    }

    function openFormulaModal() {
        document.getElementById("formula-modal-overlay").classList.add("active");
    }

    function closeFormulaModal() {
        document.getElementById("formula-modal-overlay").classList.remove("active");
    }
</script>

</body>
</html>
"""

# Render complete HTML
html_content = html_template.replace("<!-- DATABASE_PLACEHOLDER -->", json.dumps(embedded_data, ensure_ascii=False))

# 3. Write standalone HTML directly to FinalProject/app/index.html (replacing flask file with static file)
output_path = os.path.join(BASE_DIR, "app/index.html")
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"Standalone index.html successfully generated at: {output_path}")
