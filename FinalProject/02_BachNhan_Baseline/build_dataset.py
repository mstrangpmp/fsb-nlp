# -*- coding: utf-8 -*-
"""
Dự án FSB-NLP501: Script tạo tập dữ liệu mới từ Google Sheet
Chỉ lọc các dòng có đầy đủ "Mô tả thô" và "Mô tả chuẩn".
"""

import csv
import json
import io
import requests
from pathlib import Path

SHEET_ID   = "1qoyFArLxQJsSYkMf3_fPKFseOfoFcZlJ4jnf3eZLC3w"
GID        = "0"
SHEET_URL  = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

def build_dataset():
    print("📥 Đang tải dữ liệu từ Google Sheets...")
    try:
        resp = requests.get(SHEET_URL, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        print(f"❌ Không thể kết nối tới Google Sheets: {str(e)}")
        return

    # Google Sheets export dạng CSV hỗ trợ UTF-8 với BOM
    content = resp.content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(content))
    
    dataset = []
    for row in reader:
        raw = row.get("Mô tả thô", "").strip()
        gt = row.get("Mô tả chuẩn", "").strip()
        sid = row.get("ID", "").strip()
        title_gt = row.get("Tiêu đề chuẩn", "").strip()
        
        # Chỉ giữ lại dòng có đầy đủ cả Mô tả thô và Mô tả chuẩn
        if raw and gt:
            dataset.append({
                "id": sid,
                "raw_input": raw,
                "ground_truth": gt,
                "ground_truth_title": title_gt if title_gt else None
            })
            
    output_path = Path(__file__).parent / "sheet_annotated_dataset.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
        
    print(f"✅ Đã tạo bộ dữ liệu mới gồm {len(dataset)} dòng có nhãn tại: {output_path}")

if __name__ == "__main__":
    build_dataset()
