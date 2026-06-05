import json
import os
import sys

# Reconfigure console encoding
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

def main():
    nb_path = "HuuHieu_PhoBERT_FineTuning.ipynb"
    if not os.path.exists(nb_path):
        print(f"File {nb_path} not found.")
        return
        
    with open(nb_path, "r", encoding="utf-8") as f:
        nb = json.load(f)
        
    # Cell 5 is the data cell
    data_cell = nb['cells'][5]
    print("Original first 2 lines:", "".join(data_cell['source'][:2]))
    
    # Prefix to inject
    prefix = [
        "# ── Dữ liệu tải từ file json ─────────────────────────────────\n",
        "import os\n",
        "import json\n",
        "\n",
        "if os.path.exists('train.json') and os.path.exists('val.json') and os.path.exists('test.json'):\n",
        "    print('📂 Phát hiện train.json, val.json, test.json. Đang nạp dữ liệu từ file...')\n",
        "    with open('train.json', 'r', encoding='utf-8') as f:\n",
        "        TRAIN_RAW = json.load(f)\n",
        "    with open('val.json', 'r', encoding='utf-8') as f:\n",
        "        VAL_RAW = json.load(f)\n",
        "    with open('test.json', 'r', encoding='utf-8') as f:\n",
        "        TEST_RAW = json.load(f)\n",
        "    \n",
        "    # Map keys from unified format to expected format in this notebook\n",
        "    for r in TRAIN_RAW:\n",
        "        if 'raw_input_cleaned' in r: r['raw'] = r['raw_input_cleaned']\n",
        "        if 'clean_description' in r: r['desc'] = r['clean_description']\n",
        "    for r in VAL_RAW:\n",
        "        if 'raw_input_cleaned' in r: r['raw'] = r['raw_input_cleaned']\n",
        "        if 'clean_description' in r: r['desc'] = r['clean_description']\n",
        "    for r in TEST_RAW:\n",
        "        if 'raw_input_cleaned' in r: r['raw'] = r['raw_input_cleaned']\n",
        "        if 'clean_description' in r: r['desc'] = r['clean_description']\n",
        "        else: r['desc'] = ''\n",
        "else:\n",
        "    print('⚠️ Không tìm thấy file dữ liệu json. Đang sử dụng dữ liệu hardcoded mặc định...')\n",
        "    # Fallback to hardcoded variables defined below\n",
        "\n"
    ]
    
    # Add prefix to the original source list
    data_cell['source'] = prefix + data_cell['source']
    
    with open(nb_path, "w", encoding="utf-8") as f:
        json.dump(nb, f, ensure_ascii=False, indent=2)
        
    print("Notebook successfully patched!")

if __name__ == "__main__":
    main()
