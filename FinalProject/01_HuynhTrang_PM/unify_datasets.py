import urllib.request
import csv
import io
import json
import os
import sys

# Fix console encoding
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

SHEET_ID = "1qoyFArLxQJsSYkMf3_fPKFseOfoFcZlJ4jnf3eZLC3w"
GID = "0"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

def main():
    print("📥 Downloading data from Google Sheets...")
    try:
        resp = urllib.request.urlopen(SHEET_URL, timeout=30)
        csv_data = resp.read().decode("utf-8-sig")
    except Exception as e:
        print(f"❌ Failed to download Google Sheets: {e}")
        return

    reader = csv.DictReader(io.StringIO(csv_data))
    rows = list(reader)
    print(f"Total rows fetched: {len(rows)}")

    gt_records = []
    test_records = []

    for r in rows:
        sid = r.get("ID", "").strip()
        raw = r.get("Mô tả thô", "").strip()
        gt_title = r.get("Tiêu đề chuẩn", "").strip()
        gt_desc = r.get("Mô tả chuẩn", "").strip()

        if not sid or not raw:
            continue

        record = {
            "id": sid,
            "raw_input_cleaned": raw
        }

        if gt_desc:
            record["clean_title"] = gt_title
            record["clean_description"] = gt_desc
            gt_records.append(record)
        else:
            test_records.append(record)

    print(f"Ground Truth records found: {len(gt_records)}")
    print(f"Inference/Test records found: {len(test_records)}")

    # Split GT records into Train (9) and Val (2) sequentially as Hieu did (to maintain consistency)
    train_data = gt_records[:9]
    val_data = gt_records[9:]

    # Save to FinalProject/01_HuynhTrang_PM/
    dest_dir = os.path.dirname(__file__)
    
    with open(os.path.join(dest_dir, "train_dataset.json"), "w", encoding="utf-8") as f:
        json.dump(train_data, f, ensure_ascii=False, indent=2)
    print(f"Saved train_dataset.json: {len(train_data)} records")

    with open(os.path.join(dest_dir, "val_dataset.json"), "w", encoding="utf-8") as f:
        json.dump(val_data, f, ensure_ascii=False, indent=2)
    print(f"Saved val_dataset.json: {len(val_data)} records")

    # The test dataset should contain all 26 inference records
    with open(os.path.join(dest_dir, "test_dataset.json"), "w", encoding="utf-8") as f:
        json.dump(test_records, f, ensure_ascii=False, indent=2)
    print(f"Saved test_dataset.json: {len(test_records)} records")

if __name__ == "__main__":
    main()
