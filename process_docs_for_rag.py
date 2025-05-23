from docx import Document
import json
import os
import re
from unidecode import unidecode
import google.generativeai as genai
from tqdm import tqdm
import time

# --- Cấu hình ---
# Đặt API Key của Google trực tiếp vào đây cho mục đích TEST.
# LƯU Ý: KHÔNG NÊN làm như vậy trong môi trường sản phẩm thực tế để bảo mật.
genai.configure(api_key="AIzaSyBawka11YkJOO24NGOZl87dJKnz-D-nOI4") # API Key của bạn

# Khởi tạo mô hình Gemini
LLM_MODEL = genai.GenerativeModel('gemini-pro')

# Đường dẫn thư mục đầu vào và đầu ra
INPUT_DIR = "input_docs" # Đặt các file .docx của bạn vào đây
OUTPUT_DIR = "output_json_segments" # Các file JSON của từng chương/phẩm sẽ được lưu ở đây
FULL_DOC_JSON_DIR = "output_full_doc_json" # Thư mục lưu JSON của toàn bộ file DOCX
METADATA_CACHE_FILE = "metadata_dai_chanh.json" # File cache metadata chung cho các bộ kinh

# Ánh xạ tên file DOCX tới tên kinh đầy đủ (nếu tên file không đủ rõ ràng để LLM nhận diện)
FILE_TO_META_KEY = {
    # "Kinh-Truong-A-Ham-HT-Tue-Sy-Dich.docx": "Trường A Hàm",
    # "Kinh Tang Nhat A Ham.docx": "Tăng Nhất A Hàm",
    # Thêm các ánh xạ khác nếu cần. LLM sẽ được hỏi dựa trên giá trị bên phải.
}

# Template cho tất cả các khóa metadata mong muốn trong output JSON
META_KEYS_TEMPLATE = [
    "STT", "Tên Tạng", "Bộ", "Tập Số (Đại Chánh)", "Số Hiệu (Đại Chánh)", "Việt Dịch (Số tập)",
    "Tên Kinh Đầy Đủ", "Tên Tiếng Hán", "Tên Kinh rút gọn", "Hán Dịch", "Việt Dịch",
    "Khảo Dịch - Hiệu đính", "Năm xuất bản", "Số Quyển", "Chủ đề chính", "Từ khóa liên quan", "ONIX tương ứng (gợi ý)", "Ghi chú",
    "Tên Kinh Nhỏ", "Số Phẩm", "Chia Đoạn" # Các trường này sẽ được điền từ DOCX hoặc là "Not_Available"
]


## Hàm tiện ích và quản lý cache

def print_status(msg, status="INFO"):
    """In thông báo trạng thái ra console với màu sắc."""
    color_map = {"INFO": "\033[94m", "OK": "\033[92m", "WARN": "\033[93m", "ERR": "\033[91m"}
    reset_color = "\033[0m"
    print(f"{color_map.get(status, '')}[{status}]{reset_color} {msg}")

def normalize_text(s):
    """Chuẩn hóa chuỗi: lowercase, bỏ dấu, bỏ khoảng trắng/dấu gạch ngang."""
    if not isinstance(s, str):
        return ""
    s = s.lower()
    s = unidecode(s) # Bỏ dấu tiếng Việt
    s = re.sub(r'[^a-z0-9]', '', s) # Chỉ giữ lại chữ và số
    return s

def load_metadata_cache(path):
    """Tải chỉ mục metadata từ file JSON, chuẩn hóa các khóa."""
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                normalized_data = {normalize_text(k): v for k, v in data.items()}
                print_status(f"Đã tải cache metadata từ '{path}'.", "OK")
                return normalized_data
        except json.JSONDecodeError as e:
            print_status(f"Lỗi đọc file JSON '{path}': {e}. Đang tạo cache rỗng.", "ERR")
            return {}
    print_status(f"Không tìm thấy cache metadata tại '{path}'. Đang tạo cache rỗng.", "INFO")
    return {}

def save_metadata_cache(data, path):
    """Lưu cache metadata vào file JSON."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print_status(f"Đã lưu cache metadata vào '{path}'.", "OK")
    except IOError as e:
        print_status(f"Lỗi khi lưu cache metadata vào '{path}': {e}", "ERR")

## Chức năng Làm giàu Metadata từ LLM (Gemini)


def search_dai_chanh_metadata_online(ten_kinh_viet_nam):
    """
    Truy vấn LLM (Gemini) để lấy thông tin metadata chi tiết về bộ kinh.
    Trả về một dictionary chứa metadata hoặc một dictionary rỗng nếu lỗi/không tìm thấy.
    """
    print_status(f"Đang truy vấn Gemini LLM để tìm metadata cho '{ten_kinh_viet_nam}'...", "INFO")
    
    prompt = f"""
    Cung cấp thông tin metadata chi tiết về bộ kinh Phật giáo có tên tiếng Việt là "{ten_kinh_viet_nam}" từ nguồn Đại Chánh Tân Tu (Taisho Tripitaka).
    Vui lòng cung cấp các thông tin sau dưới dạng JSON. Nếu không có thông tin cụ thể cho một trường, hãy để giá trị là "Not_Available".
    Đảm bảo phản hồi chỉ là một đối tượng JSON hợp lệ và không có thêm văn bản nào khác ngoài JSON.

    {{
        "STT": "số thứ tự của kinh trong tạng (nếu có)",
        "Tên Tạng": "Tên tạng kinh (ví dụ: A Hàm, Bát Nhã)",
        "Bộ": "Tên bộ kinh (ví dụ: Trường A Hàm, Trung A Hàm)",
        "Tập Số (Đại Chánh)": "Số tập theo Đại Chánh Tân Tu (ví dụ: T1, T2)",
        "Số Hiệu (Đại Chánh)": "Số hiệu kinh theo Đại Chánh Tân Tu (ví dụ: 1, 125)",
        "Việt Dịch (Số tập)": "Số tập bản dịch tiếng Việt",
        "Tên Kinh Đầy Đủ": "Tên tiếng Việt đầy đủ của kinh",
        "Tên Tiếng Hán": "Tên tiếng Hán (nếu có)",
        "Tên Kinh rút gọn": "Tên rút gọn tiếng Việt",
        "Hán Dịch": "Thông tin Hán dịch (người dịch, đời dịch)",
        "Việt Dịch": "Thông tin Việt dịch (người dịch)",
        "Khảo Dịch - Hiệu đính": "Người khảo dịch hoặc hiệu đính bản Việt",
        "Năm xuất bản": "Năm xuất bản bản dịch tiếng Việt",
        "Số Quyển": "Số quyển của bộ kinh (theo Hán tạng hoặc Việt dịch)",
        "Chủ đề chính": "Các chủ đề chính của kinh",
        "Từ khóa liên quan": "Các từ khóa liên quan (phân cách bằng dấu phẩy)",
        "ONIX tương ứng (gợi ý)": "Thông tin ONIX tương ứng (nếu biết)",
        "Ghi chú": "Các ghi chú khác (ví dụ: nguồn thông tin tra cứu)"
    }}
    """

    try:
        response = LLM_MODEL.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"},
            safety_settings=[
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            ]
        )

        if not response.parts:
            print_status(f"LLM không trả về nội dung cho '{ten_kinh_viet_nam}'.", "WARN")
            return {}

        response_text = response.text.strip()

        # Debug: In ra phản hồi để kiểm tra
        print("\n== RESPONSE TỪ GEMINI ==\n", response_text)

        llm_metadata = json.loads(response_text)
        print_status(f"Đã nhận phản hồi JSON từ Gemini LLM cho '{ten_kinh_viet_nam}'.", "OK")

        # Trả về metadata đã chuẩn hóa theo template
        formatted_meta = {k: llm_metadata.get(k, "Not_Available") for k in META_KEYS_TEMPLATE if k not in ["Tên Kinh Nhỏ", "Số Phẩm", "Chia Đoạn"]}
        return formatted_meta

    except json.JSONDecodeError as e:
        print_status(f"Lỗi phân tích JSON từ phản hồi Gemini LLM: {e}", "ERR")
        return {}
    except Exception as e:
        print_status(f"Lỗi khi truy vấn Gemini hoặc xử lý phản hồi: {e}", "ERR")
        return {}


## Hàm lấy Metadata chung (kết hợp cache và LLM)

def get_main_book_metadata(ten_kinh_day_du, metadata_index_cache, metadata_cache_filepath):
    """
    Lấy metadata của bộ kinh chính. Ưu tiên cache cục bộ, sau đó đến LLM,
    cuối cùng trả về template rỗng.
    """
    norm_name = normalize_text(ten_kinh_day_du)
    
    if norm_name in metadata_index_cache:
        print_status(f"Đã tìm thấy metadata cục bộ cho '{ten_kinh_day_du}'.", "INFO")
        return {k: metadata_index_cache[norm_name].get(k, "Not_Available") for k in META_KEYS_TEMPLATE if k not in ["Tên Kinh Nhỏ", "Số Phẩm", "Chia Đoạn"]}

    online_meta = search_dai_chanh_metadata_online(ten_kinh_day_du)
    if online_meta:
        metadata_index_cache[norm_name] = online_meta
        save_metadata_cache(metadata_index_cache, metadata_cache_filepath)
        return {k: online_meta.get(k, "Not_Available") for k in META_KEYS_TEMPLATE if k not in ["Tên Kinh Nhỏ", "Số Phẩm", "Chia Đoạn"]}
    
    print_status(f"==> Không tìm thấy metadata cho '{ten_kinh_day_du}' ở bất kỳ đâu! Sử dụng template rỗng.", "WARN")
    return {k: "Not_Available" for k in META_KEYS_TEMPLATE if k not in ["Tên Kinh Nhỏ", "Số Phẩm", "Chia Đoạn"]}

# Hàm Lưu đoạn kinh thành JSON

def save_kinh_segment(content_list, pham_title, pham_idx, kinh_title, kinh_idx,
                       chia_doan, main_book_meta, base_filename, output_dir):
    """
    Lưu một đoạn kinh (kinh nhỏ/phẩm) thành file JSON.
    Hợp nhất metadata chung với metadata chi tiết.
    """
    if not content_list:
        return

    cleaned_content = [line for line in content_list if line.strip() and not re.match(r'^(-+o0o-+|-+O0O-+)$', line.strip())]

    if not cleaned_content:
        return

    segment_meta = main_book_meta.copy()
    
    segment_meta["Tên Kinh Nhỏ"] = kinh_title if kinh_title != "Không xác định" else "Not_Available"
    segment_meta["Số Phẩm"] = pham_title if pham_title != "Không xác định" else "Not_Available"
    segment_meta["Chia Đoạn"] = chia_doan

    for key in META_KEYS_TEMPLATE:
        if key not in segment_meta:
            segment_meta[key] = "Not_Available"

    # Tạo tên file JSON khoa học, hợp lý
    # Ví dụ: Kinh_Truong_A_Ham_pham_01_kinh_001_Ten_Kinh_Nho.json
    kinh_slug = normalize_text(kinh_title)[:50] if kinh_title != "Không xác định" else ""
    pham_slug = normalize_text(pham_title)[:50] if pham_title != "Không xác định" else ""

    file_name_parts = [base_filename]
    if pham_idx > 0:
        file_name_parts.append(f"pham_{pham_idx:02d}")
        if pham_slug:
            file_name_parts.append(f"{pham_slug}")
    if kinh_idx > 0:
        file_name_parts.append(f"kinh_{kinh_idx:03d}")
        if kinh_slug:
            file_name_parts.append(f"{kinh_slug}")
    
    # Đảm bảo tên file không quá dài và hợp lệ
    final_json_filename = "_".join(file_name_parts).replace("__", "_").replace(" ", "_")
    final_json_filename = re.sub(r'[\\/:*?"<>|]', '_', final_json_filename)[:200] + ".json"
    
    output_path = os.path.join(output_dir, final_json_filename)

    json_data = {"metadata": segment_meta, "noi_dung": cleaned_content}

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=4, ensure_ascii=False)
        print_status(f"Đã lưu file segment: {os.path.basename(output_path)}", "OK")
    except IOError as e:
        print_status(f"Lỗi khi lưu file segment '{output_path}': {e}", "ERR")

def save_full_doc_json(full_content_list, main_book_meta, base_filename, output_dir):
    """
    Lưu toàn bộ nội dung DOCX và metadata chung vào một file JSON duy nhất.
    """
    if not full_content_list:
        return
    
    # Hợp nhất metadata chung
    full_doc_meta = main_book_meta.copy()
    # Đảm bảo các trường segment-specific là Not_Available nếu không có
    full_doc_meta["Tên Kinh Nhỏ"] = "Not_Available"
    full_doc_meta["Số Phẩm"] = "Not_Available"
    full_doc_meta["Chia Đoạn"] = "Toàn bộ tài liệu" # Hoặc bất kỳ mô tả phù hợp nào

    for key in META_KEYS_TEMPLATE:
        if key not in full_doc_meta:
            full_doc_meta[key] = "Not_Available"

    full_content_string = "\n".join(full_content_list)
    
    output_path = os.path.join(output_dir, f"{base_filename}.json")

    json_data = {"metadata": full_doc_meta, "noi_dung_full_doc": full_content_string}

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=4, ensure_ascii=False)
        print_status(f"Đã lưu file toàn bộ DOCX: {os.path.basename(output_path)}", "OK")
    except IOError as e:
        print_status(f"Lỗi khi lưu file toàn bộ DOCX '{output_path}': {e}", "ERR")

# Hàm Trích xuất dữ liệu chính từ DOCX
def extract_data_from_docx(docx_file_path, base_filename, segment_output_dir, full_doc_output_dir,
                           metadata_index_cache, metadata_cache_filepath):
    """
    Trích xuất dữ liệu từ file DOCX, chia thành các phân đoạn và làm giàu metadata.
    """
    print_status(f"Đang xử lý file DOCX: {docx_file_path}", "INFO")

    try:
        document = Document(docx_file_path)
    except Exception as e:
        print_status(f"Không thể mở file DOCX '{docx_file_path}': {e}", "ERR")
        return

    meta_key_for_llm = FILE_TO_META_KEY.get(os.path.basename(docx_file_path), base_filename.replace("_", " "))
    main_book_meta = get_main_book_metadata(meta_key_for_llm, metadata_index_cache, metadata_cache_filepath)

    all_segments_data = [] # List để lưu trữ tất cả các segment nhỏ
    full_doc_content_lines = [] # List để lưu trữ toàn bộ nội dung DOCX

    current_kinh_content = []
    current_pham_title = "Không xác định"
    current_pham_idx = 0
    current_kinh_title = "Không xác định"
    current_kinh_idx = 0
    
    processing_main_content = False

    found_pham_structure = False
    found_kinh_structure = False

    regex_delimiter = re.compile(r'---o0o---', re.IGNORECASE)
    regex_pham = re.compile(
        r'^(PHẨM|PHẦN|CHƯƠNG)\s+(THỨ\s+)?([IVXLCDM\d]+|[A-ZĐ][a-zđÀ-Ỹ]+)\s*[:\.]?\s*(.*)<span class="math-inline">',
        re.IGNORECASE
    )
    regex_kinh = re.compile(
        r'^((\d+(\.|\s+)?)|(KINH\s+))\s*(.+)</span>',
        re.IGNORECASE
    )

    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        full_doc_content_lines.append(text) # Luôn thêm vào full_doc_content

        if not text:
            continue

        is_delimiter = bool(regex_delimiter.search(text))
        match_pham = regex_pham.match(text)
        match_kinh = regex_kinh.match(text)

        if is_delimiter:
            if not processing_main_content:
                processing_main_content = True
                print_status("Đã phát hiện dấu phân cách '---o0o---', bắt đầu xử lý nội dung chính.", "INFO")
            
            if current_kinh_content:
                all_segments_data.append({
                    "content": current_kinh_content,
                    "pham_title": current_pham_title,
                    "pham_idx": current_pham_idx,
                    "kinh_title": current_kinh_title,
                    "kinh_idx": current_kinh_idx
                })
            current_kinh_content = []
            continue

        if not processing_main_content:
            # Bỏ qua các đoạn trước khi gặp dấu phân cách đầu tiên (ví dụ: mục lục)
            continue
        
        if match_pham:
            pham_type = match_pham.group(1).upper()
            pham_num_raw = match_pham.group(3)
            pham_name = match_pham.group(5) if match_pham.group(5) else ""

            try:
                if re.match(r'^[IVXLCDM]+$', pham_num_raw, re.IGNORECASE):
                    roman_map_simple = {'I':1, 'V':5, 'X':10, 'L':50, 'C':100, 'D':500, 'M':1000}
                    def roman_to_int_val(s):
                        res = 0
                        for i in range(len(s)):
                            val = roman_map_simple.get(s[i],0)
                            if i + 1 < len(s) and val < roman_map_simple.get(s[i+1],0):
                                res -= val
                            else:
                                res += val
                        return res
                    current_pham_idx = roman_to_int_val(pham_num_raw.upper())
                else:
                    current_pham_idx = int(pham_num_raw)
            except ValueError:
                current_pham_idx += 1

            current_pham_title = f"{pham_type} {pham_num_raw.upper()}: {pham_name.strip()}" if pham_name else f"{pham_type} {pham_num_raw.upper()}"
            print_status(f"Nhận diện {pham_type}: {current_pham_title}", "INFO")
            found_pham_structure = True
            current_kinh_title = "Không xác định"
            current_kinh_idx = 0
            current_kinh_content.append(text)
            continue

        if match_kinh:
            current_kinh_idx += 1
            current_kinh_title = text.strip()
            print_status(f"Nhận diện KINH: {current_kinh_title}", "INFO")
            found_kinh_structure = True
            current_kinh_content.append(text)
            continue

        current_kinh_content.append(text)

    # Lưu đoạn kinh cuối cùng sau khi đã duyệt hết tài liệu
    if current_kinh_content:
        all_segments_data.append({
            "content": current_kinh_content,
            "pham_title": current_pham_title,
            "pham_idx": current_pham_idx,
            "kinh_title": current_kinh_title,
            "kinh_idx": current_kinh_idx
        })

    # Xác định cách chia đoạn cuối cùng cho toàn bộ file
    if found_pham_structure and found_kinh_structure:
        final_chia_doan = "Theo phẩm, theo kinh nhỏ"
    elif found_pham_structure:
        final_chia_doan = "Theo phẩm"
    elif found_kinh_structure:
        final_chia_doan = "Theo kinh nhỏ"
    else:
        final_chia_doan = "Không xác định"
    
    # Lưu các segment nhỏ
    for segment in all_segments_data:
        save_kinh_segment(
            segment["content"],
            segment["pham_title"],
            segment["pham_idx"],
            segment["kinh_title"],
            segment["kinh_idx"],
            final_chia_doan,
            main_book_meta,
            base_filename,
            segment_output_dir
        )
    
    # Lưu toàn bộ DOCX
    save_full_doc_json(full_doc_content_lines, main_book_meta, base_filename, full_doc_output_dir)

    print_status(f"Đã hoàn thành xử lý file: {os.path.basename(docx_file_path)}", "OK")

## Hàm xử lý tất cả các file DOCX trong thư mục

def process_all_docs_in_directory(input_dir, segment_output_dir, full_doc_output_dir, metadata_cache_filepath):
    """
    Xử lý tất cả các file .docx trong thư mục đầu vào.
    """
    if not os.path.exists(segment_output_dir):
        os.makedirs(segment_output_dir)
        print_status(f"Đã tạo thư mục đầu ra cho segments: '{segment_output_dir}'", "INFO")
    if not os.path.exists(full_doc_output_dir):
        os.makedirs(full_doc_output_dir)
        print_status(f"Đã tạo thư mục đầu ra cho toàn bộ DOCX: '{full_doc_output_dir}'", "INFO")

    metadata_cache = load_metadata_cache(metadata_cache_filepath)

    doc_files = [f for f in os.listdir(input_dir) if f.endswith(".docx")]
    
    if not doc_files:
        print_status(f"Không tìm thấy file .docx nào trong thư mục '{input_dir}'.", "WARN")
        return

    print_status(f"Tìm thấy {len(doc_files)} file .docx để xử lý.", "INFO")

    for filename in tqdm(doc_files, desc="Đang xử lý DOCX"):
        docx_file_path = os.path.join(input_dir, filename)
        base_filename = os.path.splitext(filename)[0].replace(" ", "_")
        
        extract_data_from_docx(docx_file_path, base_filename, segment_output_dir, full_doc_output_dir,
                               metadata_cache, metadata_cache_filepath)
        print_status(f"Hoàn thành xử lý '{filename}'.", "INFO")
        time.sleep(2) # Giữ độ trễ 2 giây cho Gemini để tránh vượt giới hạn tốc độ API

    print_status("Tất cả các file DOCX đã được trích xuất và làm giàu metadata thành các file JSON.", "OK")


## MAIN EXECUTION

if __name__ == "__main__":
    process_all_docs_in_directory(INPUT_DIR, OUTPUT_DIR, FULL_DOC_JSON_DIR, METADATA_CACHE_FILE)