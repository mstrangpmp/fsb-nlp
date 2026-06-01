# -*- coding: utf-8 -*-
"""
Dự án FSB-NLP501 - Rút Gọn & Chuẩn Hóa Tin Đăng Bất Động Sản Bằng Transformers
Kịch bản hỗ trợ Trang (Người 1 - Data Curator) thực hiện:
1. Back-Translation (Dịch ngược / Làm thô): Biến 68 mô tả tốt (Ground Truth) thành tin thô nhạy cảm phục vụ tập Train.
2. Weak Supervision (Gán nhãn yếu): Dùng Few-shot Prompt tạo nhãn Silver cho tin thô viết dở, giúp Trang kiểm duyệt nhanh để làm tập Val/Test.
"""

import os
import pandas as pd
import json
import time
from typing import List, Dict

# Giả định dùng thư viện Google GenAI hoặc OpenAI để gọi LLM
# pip install google-generativeai openai
try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


# =====================================================================
# THIẾT LẬP LLM (API KEY) - Trang cấu hình API Key ở đây nếu chạy thật
# =====================================================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY")

if HAS_GENAI and GEMINI_API_KEY != "YOUR_GEMINI_API_KEY":
    genai.configure(api_key=GEMINI_API_KEY)


# =====================================================================
# 1. CHIẾN LƯỢC 1: BACK-TRANSLATION (DỊCH NGƯỢC)
# Dùng LLM biến mô tả Ground Truth (rất tốt) -> Tin thô (nhạy cảm, viết thô)
# =====================================================================

BACK_TRANSLATION_PROMPT = """
Bạn là một môi giới bất động sản đang vội vã, viết lách cẩu thả, không rành công nghệ.
Nhiệm vụ của bạn là đọc một mô tả bất động sản viết cực kỳ hay, trau chuốt (Ground Truth), 
và DỊCH NGƯỢC (Biến đổi) nó thành một tin đăng thô (Raw Listing Input) cẩu thả và nhạy cảm.

Các quy tắc biến đổi thành tin thô cẩu thả:
1. Chèn địa chỉ nhà cụ thể giả định ở phần đầu tin (Ví dụ: "163/24/80 Tô Hiến Thành").
2. Chèn SĐT đầu chủ giả lập ở cuối tin (Ví dụ: "0973.776.929 - Đầu chủ Nam").
3. Chèn các mã số nội bộ doanh nghiệp hoặc ký hiệu hoa hồng nội bộ (Ví dụ: "H3GB", "HH 1%", "ĐC Nam", "Nguồn Thiên Khôi").
4. Viết tắt bừa bãi: DT (Diện tích), KC (Kết cấu), TL (Thương lượng), WC, PN (Phòng ngủ), BTCT.
5. Ghép tất cả các câu lại thành một đoạn văn duy nhất, không xuống dòng, ngăn cách bằng dấu phẩy hoặc dấu chấm liên tiếp bừa bãi.
6. Giữ nguyên 100% các thông số kỹ thuật (specs) từ tin gốc: diện tích (m2), kích thước ngang x dài, số tầng, số phòng ngủ, giá tiền (tỷ).

Hãy chuyển đổi tin đăng sau đây thành tin thô cẩu thả:
MÔ TẢ GỐC (GROUND TRUTH):
"{ground_truth}"

ĐẦU RA TIN THÔ CẨU THẢ (RAW INPUT):
"""

def generate_raw_listing_via_gemini(ground_truth_text: str) -> str:
    """Gọi Gemini API để làm thô tin đăng tốt"""
    if not HAS_GENAI or GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
        # Fallback giả định nếu không có API key
        return f"123/45/6 Cầu Giấy DT 40m2 4 tầng 4x10 giá 8 tỷ TL. Liên hệ 0988.777.888 để xem nhà trực tiếp. HH 1%."
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(
            BACK_TRANSLATION_PROMPT.format(ground_truth=ground_truth_text)
        )
        return response.text.strip()
    except Exception as e:
        print(f"Lỗi gọi Gemini API: {e}")
        return f"LỖI_API: {e}"


# =====================================================================
# 2. CHIẾN LƯỢC 2: FEW-SHOT PROMPTING CHO TIN VIẾT DỞ
# Biến tin thô của các đầu chủ viết dở -> Nhãn Silver (để Trang duyệt nhanh)
# =====================================================================

FEW_SHOT_SYSTEM_PROMPT = """
Bạn là Trợ lý AI chuyên nghiệp thuộc website BDS Khang Ngô.
Nhiệm vụ của bạn là chuẩn hóa và làm sạch tin đăng bất động sản thô từ nguồn tin nội bộ.

Quy tắc chuẩn hóa nghiêm ngặt:
1. LOẠI BỎ tuyệt đối thông tin nhạy cảm: Số nhà thật (chỉ giữ lại tên đường), SĐT đầu chủ, Tên đầu chủ/môi giới, Hoa hồng, Mã số nguồn (e.g. H3GB).
2. THAY THẾ số nhà thật bằng vị trí tương đối gần trục đường chính (Ví dụ: "gần đường lớn Lý Thường Kiệt", "gần ngã tư Điện Biên Phủ").
3. BẢO TOÀN tuyệt đối 100% thông số kỹ thuật (Specs): Diện tích m2, kích thước ngang x dài, số tầng/lầu đúc, số phòng ngủ/WC, giá tiền (tỷ).
4. Định dạng đầu ra thành 2 phần rõ ràng:
   - TIÊU ĐỀ chuẩn hóa hấp dẫn đầy đủ specs cốt lõi.
   - MÔ TẢ mượt mà, trôi chảy, văn phong chuyên nghiệp, định dạng hấp dẫn người đọc.

Dưới đây là ví dụ mẫu Few-shot để học văn phong của BDS Khang Ngô:

VÍ DỤ 1:
- TIN THÔ: "163.24.80 Tô Hiến Thành 50.2 5 4 13 12.9 tỷ Hòa Hưng Quận 10 Nguyễn Hoàng Nam 0973776929 H3GB nhà 5 tầng kiên cố 6PN sổ nở hậu nhẹ giảm 300tr còn 12.9 tỷ TL"
- TIÊU ĐỀ CHUẨN: "Tô Hiến Thành (gần Trường Sơn) 50.2m2 5 lầu 4x13 - 12.9 tỷ Hẻm xe tải"
- MÔ TẢ CHUẨN: "Nhà 5 tầng kiên cố, 6 phòng ngủ, 4 WC tọa lạc tại vị trí cực đẹp khu trung tâm Quận 10, gần trục đường lớn Trường Sơn / Lý Thái Tổ di chuyển thuận lợi. Sổ vuông vức, nở hậu nhẹ phong thủy cực tốt. Hẻm ô tô rộng rãi xe tải vào tận cửa. Phù hợp cho gia đình định cư lâu dài kết hợp kinh doanh hoặc cho thuê dòng tiền cao. Thương lượng trực tiếp chủ."

Hãy làm sạch và chuẩn hóa tin thô sau:
- TIN THÔ: "{raw_input}"
- ĐẦU RA CHUẨN HÓA (TIÊU ĐỀ + MÔ TẢ):
"""

def generate_silver_label_via_openai(raw_text: str) -> Dict[str, str]:
    """Gọi OpenAI API để tạo nhãn Silver chuẩn hóa"""
    if not HAS_OPENAI or OPENAI_API_KEY == "YOUR_OPENAI_API_KEY":
        # Fallback giả lập cấu trúc
        return {
            "title": "Lê Văn Sỹ Tân Bình 42m2 4 lầu - 8.5 tỷ",
            "desc": "Nhà mới đúc BTCT kiên cố gồm 4PN, 3WC. Hẻm thông thoáng sạch sẽ gần Bàu Cát..."
        }
    
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional Vietnamese real estate assistant."},
                {"role": "user", "content": FEW_SHOT_SYSTEM_PROMPT.format(raw_input=raw_text)}
            ],
            temperature=0.3
        )
        output = response.choices[0].message.content.strip()
        
        # Parse tiêu đề và mô tả thô sơ từ output của GPT
        lines = output.split('\n')
        title = "Chưa nhận diện được tiêu đề"
        desc = output
        for line in lines:
            if "TIÊU ĐỀ" in line or "Tiêu đề" in line:
                title = line.replace("TIÊU ĐỀ CHUẨN:", "").replace("Tiêu đề chuẩn:", "").replace("- TIÊU ĐỀ:", "").strip()
            elif "MÔ TẢ" in line or "Mô tả" in line:
                desc = output.split(line)[1].strip() if len(output.split(line)) > 1 else output
                break
                
        return {"title": title, "desc": desc}
    except Exception as e:
        print(f"Lỗi gọi OpenAI API: {e}")
        return {"title": "LỖI_API", "desc": str(e)}


# =====================================================================
# 3. KỊCH BẢN CHẠY THỬ NGHIỆM ĐỂ XUẤT CSV CHO NHÓM
# =====================================================================

if __name__ == "__main__":
    print("=== DỰ ÁN FSB-NLP501: KỊCH BẢN DATA PREPROCESSING (TRANG) ===")
    
    # 1. Khởi tạo 5 mẫu mô tả Ground Truth mẫu có sẵn (Thực tế Trang sẽ đọc 68 mẫu từ Google Sheets)
    sample_ground_truths = [
        "Cần bán nhà đường Tô Hiến Thành, Quận 10. Diện tích 50.2m2, kích thước 4x13m. Nhà đúc kiên cố 5 tầng lầu gồm 6 phòng ngủ và 4 WC. Nằm trong khu dân trí cao yên tĩnh, gần công viên Lê Thị Riêng và cư xá Bắc Hải. Sổ hồng riêng nở hậu phong thủy tốt, giá bán 12.9 tỷ thương lượng trực tiếp.",
        "Nhà đẹp đón Tết đường Lê Văn Sỹ, Phường 1, Tân Bình. Diện tích 42m2, ngang 3.8m dài 11m, đúc 4 tầng BTCT kiên cố mới tinh dọn vào ở ngay. Hẻm 3m sạch sẽ an ninh, thích hợp mua ở định cư lâu dài hoặc cho thuê văn phòng. Giá bán 8.5 tỷ có bớt lộc.",
        "Nhà hẻm xe hơi đường Nguyễn Thiện Thuật, Quận 3. Diện tích khuôn viên 35m2, 3.5x10m, cấu trúc 3 tầng lầu đúc. Nhà hơi cũ tiện cải tạo làm căn hộ dịch vụ dòng tiền hoặc xây dựng mới theo sở thích. Giá chào 7.8 tỷ TL trực tiếp.",
        "Nhà phố Phan Xích Long, Phú Nhuận. Diện tích đất 48m2 (4x12m), kết cấu 3 tầng kiên cố, thiết kế hiện đại, đầy đủ công năng với 3 phòng ngủ thoáng đãng. Vị trí vàng gần khu ẩm thực Phan Xích Long sầm uất. Giá chào bán 9.2 tỷ.",
        "Bán gấp biệt thự mini hẻm lớn đường Lê Quang Định, Bình Thạnh. Diện tích 70m2, ngang 5m dài 14m, kết cấu 3 lầu cực đẹp có giếng trời thoáng mát. Khu vực an ninh, dân trí cao toàn nhà cao tầng. Sổ hồng chính chủ giao dịch nhanh, giá 11.5 tỷ."
    ]
    
    print(f"\n[Bước 1] Tiến hành dịch ngược {len(sample_ground_truths)} Ground Truth mẫu để tạo dữ liệu Train thô...")
    dataset_pairs = []
    
    for idx, gt in enumerate(sample_ground_truths):
        print(f" - Đang xử lý mẫu #{idx+1}...")
        # Gọi làm thô tin
        raw_listing = generate_raw_listing_via_gemini(gt)
        print(f"   => Tin thô tạo ra: {raw_listing[:120]}...")
        
        dataset_pairs.append({
            "id": idx + 1,
            "raw_input": raw_listing,
            "ground_truth": gt,
            "source_type": "Back-Translated"
        })
        time.sleep(1) # Tránh rate limit API free
        
    # 2. Tạo DataFrame và xuất file
    df_train = pd.DataFrame(dataset_pairs)
    
    # Chia tập dữ liệu giả lập (Train 3, Val 1, Test 1)
    df_train["split"] = ["train", "train", "train", "val", "test"]
    
    output_path = "dataset_fsb_realestate.csv"
    df_train.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"\n[Thành công] Đã xuất file CSV chuẩn hóa cho cả nhóm tại: {os.path.abspath(output_path)}")
    print("Trang có thể mở file này bằng Excel trên Windows mà không lo bị lỗi font Việt vì đã dùng mã hóa utf-8-sig!")
    
    print("\n[Chi tiết dữ liệu mẫu tạo ra]:")
    print(df_train[["id", "raw_input", "ground_truth", "split"]].to_string())
