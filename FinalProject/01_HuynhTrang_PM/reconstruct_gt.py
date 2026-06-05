import json
import os
import sys
import re

# Fix console encoding on Windows
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

def robust_parse_specs_agnostic(text):
    if not text or not isinstance(text, str):
        return {
            'duong': None, 'phuong': None, 'quan': None,
            'gia_ty': None, 'dien_tich_m2': None, 'so_tang': None,
            'mat_tien_m': None, 'chieu_sau_m': None, 'phan_loai_hem': 'Hẻm thông'
        }
        
    t = text.lower().replace('*', '').replace('#', '')
    specs = {
        'duong': None, 'phuong': None, 'quan': None,
        'gia_ty': None, 'dien_tich_m2': None, 'so_tang': None,
        'mat_tien_m': None, 'chieu_sau_m': None, 'phan_loai_hem': 'Hẻm thông'
    }
    
    # Area
    area_match = re.search(r'(?:diện\s+tích|dt)\s*(?:công\s+nhận)?\s*(?::|là)?\s*([\d.,]+)\s*(?:m2|m²)', t)
    if area_match:
        specs['dien_tich_m2'] = float(area_match.group(1).replace(',', '.'))
        
    # Dimensions
    dim_match = re.search(r'(?:kích\s+thước|dt|diện\s+tích|ngang)?\s*([\d.,]+)\s*m?\s*[x×]\s*([\d.,]+)\s*m?', t)
    if dim_match:
        specs['mat_tien_m'] = float(dim_match.group(1).replace(',', '.'))
        specs['chieu_sau_m'] = float(dim_match.group(2).replace(',', '.'))
        
    # Price
    price_match = re.search(r'(?:giá|giá\s+bán|giá\s+chào)\s*(?::|là)?\s*([\d.,]+)\s*(?:tỷ|ty)', t)
    if price_match:
        specs['gia_ty'] = float(price_match.group(1).replace(',', '.'))
    else:
        m = re.search(r'([\d.,]+)\s*(?:tỷ|ty)\b', t)
        if m:
            specs['gia_ty'] = float(m.group(1).replace(',', '.'))
            
    # Floors
    floors_match = re.search(r'(?:kết\s+cấu|quy\s+mô|nhà)?\s*(?::|là)?\s*(\d+)\s*(?:tầng|lầu)', t)
    if floors_match:
        specs['so_tang'] = int(floors_match.group(1))
    else:
        m = re.search(r'(\d+)\s*trệt\s*(?:và|[,+])?\s*(\d+)\s*(?:lầu|lửng)', t)
        if m:
            specs['so_tang'] = int(m.group(1)) + int(m.group(2))
        else:
            m = re.search(r'trệt\s*(?:và|[,+])?\s*(\d+)\s*lầu', t)
            if m:
                specs['so_tang'] = 1 + int(m.group(1))
                
    # Alley
    if 'mặt tiền' in t:
        specs['phan_loai_hem'] = 'Mặt tiền'
    elif 'hẻm xe hơi' in t or 'hxh' in t or 'ô tô' in t or 'oto' in t:
        specs['phan_loai_hem'] = 'Hẻm xe hơi'
    elif 'hẻm xe tải' in t or 'hxt' in t:
        specs['phan_loai_hem'] = 'Hẻm xe tải'
    elif 'xe máy' in t or 'ba gác' in t:
        specs['phan_loai_hem'] = 'Hẻm xe máy'
        
    # District
    dt_match = re.search(r'quận\s*(\d+)\b', t)
    if dt_match:
        specs['quan'] = 'Quận ' + dt_match.group(1)
    else:
        for d_name in ['bình thạnh', 'phú nhuận', 'gò vấp', 'tân bình', 'quận 1', 'quận 3', 'quận 10']:
            if d_name in t:
                specs['quan'] = d_name.title()
                break
                
    # Ward
    wd_match = re.search(r'(?:phường|p\.)\s*([\d\w\s]+?)(?:,|$|\n|\.)', t)
    if wd_match:
        specs['phuong'] = 'Phường ' + wd_match.group(1).strip().title()
        
    # Street
    st_match = re.search(r'đường\s+([\w\s]+?)(?:,|$|\n|\.)', t)
    if st_match:
        specs['duong'] = st_match.group(1).strip().title()
        
    return specs

def main():
    # Load sheet_annotated_dataset.json
    src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../02_BachNhan_Baseline/sheet_annotated_dataset.json"))
    if not os.path.exists(src_path):
        print(f"[Lỗi] Không tìm thấy file {src_path}")
        return
        
    with open(src_path, "r", encoding="utf-8") as f:
        annotated_data = json.load(f)
        
    gt_test = []
    for row in annotated_data:
        gt_desc = row.get("ground_truth", "")
        specs = robust_parse_specs_agnostic(gt_desc)
        
        gt_test.append({
            "id": row.get("id"),
            "ground_truth_desc": gt_desc,
            "extracted_specs": specs
        })
        
    dest_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "ground_truth_test.json"))
    with open(dest_path, "w", encoding="utf-8") as f:
        json.dump(gt_test, f, ensure_ascii=False, indent=2)
        
    print(f"Successfully reconstructed ground_truth_test.json with {len(gt_test)} records using robust parser.")

if __name__ == "__main__":
    main()
