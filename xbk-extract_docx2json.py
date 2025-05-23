import docx
import json
import os
import re
import unicodedata
import sys
from tqdm import tqdm

# Ánh xạ tên file sang tên metadata chuẩn (có thể mở rộng nếu cần)
# Mục đích: Đảm bảo tên file được ánh xạ chính xác tới "Tên Kinh Đầy Đủ" trong metadata_index
FILE_TO_META_KEY = {
    "Kinh-Truong-A-Ham-HT-Tue-Sy-Dich": "Trường A Hàm",
    # Thêm các file khác nếu có quy tắc ánh xạ cụ thể
}

def load_metadata_index(path):
    """
    Tải và tiền xử lý chỉ mục metadata từ file JSON.
    Tiền xử lý bằng cách chuẩn hóa các khóa để tìm kiếm hiệu quả hơn.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Chuẩn hóa tất cả các khóa trong metadata_index một lần để tìm kiếm nhanh chóng
        normalized_data = {normalize(k): v for k, v in data.items()}
        print_status(f"Đã tải chỉ mục metadata từ '{path}'.", "OK")
        return normalized_data
    except FileNotFoundError:
        print_status(f"Không tìm thấy file metadata tại '{path}'. Vui lòng kiểm tra lại đường dẫn.", "ERR")
        sys.exit(1) # Thoát chương trình nếu không tìm thấy metadata
    except json.JSONDecodeError:
        print_status(f"Lỗi đọc file JSON metadata tại '{path}'. Đảm bảo file đúng định dạng.", "ERR")
        sys.exit(1)
    except Exception as e:
        print_status(f"Lỗi không xác định khi tải metadata: {e}", "ERR")
        sys.exit(1)


def normalize(s):
    """
    Chuẩn hóa chuỗi: chuyển sang chữ thường, loại bỏ dấu, khoảng trắng và ký tự đặc biệt.
    Mục đích: Giúp so sánh chuỗi không phân biệt chữ hoa, dấu và khoảng trắng.
    """
    s = str(s).lower() # Đảm bảo đầu vào là chuỗi
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn') # Loại bỏ dấu
    s = re.sub(r'[\s_\-]', '', s) # Loại bỏ khoảng trắng, gạch dưới, gạch ngang
    return s

def get_onix_metadata(ten_kinh_day_du, metadata_index):
    """
    Tìm kiếm và trả về metadata ONIX cho một tên kinh đầy đủ.
    Sử dụng chỉ mục metadata đã được chuẩn hóa để tìm kiếm.
    """
    norm_name = normalize(ten_kinh_day_du)
    # Các khóa metadata cần trích xuất. Thêm/bớt tùy theo cấu trúc metadata_index.json của bạn.
    meta_keys = [
        "STT", "Tên Tạng", "Bộ", "Tập Số (Đại Chánh)", "Số Hiệu (Đại Chánh)", "Việt Dịch (Số tập)",
        "Tên Kinh Đầy Đủ", "Tên Tiếng Hán", "Tên Kinh rút gọn", "Hán Dịch", "Việt Dịch",
        "Khảo Dịch - Hiệu đính", "Năm xuất bản", "Số Quyển", "Tên Kinh Nhỏ", "Số Phẩm",
        "Chia Đoạn", "Chủ đề chính", "Từ khóa liên quan", "ONIX tương ứng (gợi ý)", "Ghi chú"
    ]

    # Tìm kiếm trực tiếp trong metadata_index đã được chuẩn hóa
    if norm_name in metadata_index:
        return {k: metadata_index[norm_name].get(k, "Not_Available") for k in meta_keys}

    print_status(f"==> Không tìm thấy metadata cho '{ten_kinh_day_du}' (normalize: '{norm_name}')!", "WARN")
    # Trả về dictionary với "Not_Available" cho tất cả các khóa nếu không tìm thấy
    return {k: "Not_Available" for k in meta_keys}

def print_status(msg, status="INFO"):
    """
    In thông báo trạng thái với màu sắc tương ứng.
    """
    if status == "INFO":
        print(f"[INFO] {msg}")
    elif status == "OK":
        print(f"\033[92m[OK]\033[0m {msg}") # Màu xanh lá
    elif status == "WARN":
        print(f"\033[93m[WARN]\033[0m {msg}") # Màu vàng
    elif status == "ERR":
        print(f"\033[91m[ERR]\033[0m {msg}") # Màu đỏ
    else:
        print(f"[{status}] {msg}")

def extract_data_from_docx(docx_file_path, output_dir, ten_kinh_day_du, ten_kinh_filename, metadata_index):
    """
    Trích xuất dữ liệu từ file DOCX, phân chia theo phẩm/kinh và lưu dưới dạng JSON.
    """
    try:
        doc = docx.Document(docx_file_path)
        print_status(f"Đang xử lý file DOCX: {docx_file_path}", "INFO")
    except Exception as e:
        print_status(f"Không thể mở hoặc đọc file DOCX '{docx_file_path}': {e}", "ERR")
        return

    pham_title = "Không xác định"
    pham_idx = 0
    kinh_title = "Không xác định"
    kinh_idx = 0
    current_kinh_content = []
    
    # Lấy metadata ONIX một lần cho toàn bộ kinh
    onix_meta = get_onix_metadata(ten_kinh_day_du, metadata_index)
    
    found_pham_structure = False
    found_kinh_structure = False
    chia_doan = "Không xác định"

    def save_kinh_segment(content, pham_t, pham_i, kinh_t, kinh_i, ch_doan):
        """
        Lưu một phân đoạn kinh (kinh nhỏ) vào file JSON.
        """
        if not content or kinh_t == "Không xác định":
            return

        # Loại bỏ các dòng "--- o0o ---" hoặc "---o0o---" ở cuối content
        while content and content[-1].strip().replace(" ", "").replace("\t", "") in ["---o0o---", "o0o"]:
            content.pop()
        
        # Nếu sau khi loại bỏ mà content rỗng, bỏ qua
        if not content:
            return

        # Định dạng tên file: Kinh_<tên file gốc>_pham_<idx>_kinh_<idx>.json
        # Đảm bảo tên file hợp lệ
        safe_kinh_t = re.sub(r'[\\/:*?"<>|]', '_', kinh_t) # Loại bỏ ký tự không hợp lệ trong tên file
        file_name = f"{ten_kinh_filename}_pham_{pham_i:02d}_kinh_{kinh_i:03d}_{safe_kinh_t[:50]}.json" # Giới hạn độ dài tên kinh
        output_path = os.path.join(output_dir, file_name)

        metadata = onix_meta.copy()
        metadata.update({
            "Tên Kinh Nhỏ": kinh_t,
            "Số Phẩm": pham_t, # Có thể là "PHẨM X" hoặc "PHẦN Y"
            "Chia Đoạn": ch_doan,
        })
        json_data = {
            "metadata": metadata,
            "noi_dung": content
        }
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)
            print_status(f"Đã lưu file: {file_name}", "OK")
        except IOError as e:
            print_status(f"Không thể ghi file '{output_path}': {e}", "ERR")

    # Bắt đầu duyệt từng đoạn văn trong tài liệu
    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if not text:
            continue

        # Kiểm tra tiêu đề PHẨM
        # Có thể là "PHẨM X", "X. PHẨM Y", "PHẦN Z"
        match_pham = re.match(r"^(?:\d{1,2}\.\s*)?PHẨM\s+(.+)$", text, re.IGNORECASE)
        match_phan = re.match(r"^PHẦN\s+(\d+)$", text, re.IGNORECASE)
        
        # Kiểm tra tiêu đề KINH
        # Có thể là "X. KINH Y", "KINH Z"
        match_kinh = re.match(r"^(\d{1,3})\.\s*KINH\s+(.+)$", text, re.IGNORECASE)
        
        # Ưu tiên PHẨM/PHẦN, sau đó đến KINH
        if match_pham or match_phan:
            # Lưu kinh hiện tại trước khi chuyển sang phẩm/phần mới
            if current_kinh_content and kinh_title != "Không xác định":
                save_kinh_segment(current_kinh_content, pham_title, pham_idx, kinh_title, kinh_idx, chia_doan)
            
            # Cập nhật thông tin phẩm/phần mới
            pham_idx += 1
            if match_pham:
                pham_title = match_pham.group(0).strip()
                print_status(f"Nhận diện PHẨM: {pham_title}", "INFO")
                found_pham_structure = True
            elif match_phan:
                pham_title = match_phan.group(0).strip()
                print_status(f"Nhận diện PHẦN: {pham_title}", "INFO")
                found_pham_structure = True # Coi PHẦN như một dạng cấu trúc phẩm

            kinh_title = "Không xác định" # Reset kinh_title khi gặp phẩm/phần mới
            kinh_idx = 0
            current_kinh_content = []
            continue # Tiếp tục vòng lặp, không xử lý đoạn này là nội dung

        elif match_kinh:
            # Lưu kinh hiện tại trước khi chuyển sang kinh mới
            if current_kinh_content and kinh_title != "Không xác định":
                save_kinh_segment(current_kinh_content, pham_title, pham_idx, kinh_title, kinh_idx, chia_doan)
            
            # Cập nhật thông tin kinh mới
            kinh_idx += 1
            kinh_title = match_kinh.group(0).strip()
            print_status(f"Nhận diện KINH: {kinh_title}", "INFO")
            found_kinh_structure = True
            current_kinh_content = []
            continue # Tiếp tục vòng lặp, không xử lý đoạn này là nội dung

        # Nếu là dấu phân đoạn, bỏ qua
        if text.strip().replace(" ", "").replace("\t", "") in ["---o0o---", "o0o"]:
            continue
        
        # Chỉ thêm nội dung nếu đã tìm thấy ít nhất một tiêu đề KINH
        # Hoặc nếu không có cấu trúc PHẨM/KINH nào được tìm thấy,
        # coi tất cả nội dung là một "kinh" duy nhất
        if kinh_title != "Không xác định" or (not found_pham_structure and not found_kinh_structure and not current_kinh_content):
             current_kinh_content.append(text)
        elif not found_pham_structure and not found_kinh_structure:
            # Trường hợp không có tiêu đề KINH hay PHẨM, nhưng có nội dung
            # Cần một cách để gán nội dung vào một "kinh" mặc định
            if kinh_title == "Không xác định": # Gán tên kinh mặc định nếu chưa có
                kinh_title = ten_kinh_day_du + "_full" # Sử dụng tên kinh đầy đủ làm tên kinh nhỏ mặc định
                kinh_idx = 1 # Coi là kinh đầu tiên
            current_kinh_content.append(text)


    # Xác định 'Chia Đoạn' sau khi đã duyệt qua toàn bộ tài liệu
    if found_pham_structure and found_kinh_structure:
        chia_doan = "Theo phẩm, theo kinh nhỏ"
    elif found_pham_structure:
        chia_doan = "Theo phẩm"
    elif found_kinh_structure:
        chia_doan = "Theo kinh nhỏ"
    else:
        chia_doan = "Không xác định" # Giữ nguyên nếu không tìm thấy cấu trúc

    # Lưu phân đoạn kinh cuối cùng (nếu có)
    if current_kinh_content and kinh_title != "Không xác định":
        save_kinh_segment(current_kinh_content, pham_title, pham_idx, kinh_title, kinh_idx, chia_doan)
    elif current_kinh_content and kinh_title == "Không xác định":
        # Xử lý trường hợp có nội dung nhưng không có tiêu đề kinh nào được tìm thấy
        # Gán tên kinh mặc định nếu chưa có
        kinh_title = ten_kinh_day_du + "_full"
        kinh_idx = 1
        save_kinh_segment(current_kinh_content, pham_title, pham_idx, kinh_title, kinh_idx, chia_doan)


if __name__ == "__main__":
    # Cấu hình các thư mục và đường dẫn file
    input_dir = "/root/SQLite/Doc2Json/"  # Thư mục chứa các file .docx
    output_dir = "/root/SQLite/Doc2Json/" # Thư mục để lưu các file JSON đầu ra
    metadata_index_path = "/root/SQLite/Doc2Json/metadata_index.json" # Đường dẫn đến file metadata

    # Tạo thư mục đầu ra nếu nó chưa tồn tại
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print_status(f"Đã tạo thư mục đầu ra: {output_dir}", "INFO")

    # Tải và tiền xử lý chỉ mục metadata
    metadata_index = load_metadata_index(metadata_index_path)

    # Lấy danh sách các file .docx trong thư mục đầu vào
    files_to_process = [f for f in os.listdir(input_dir) if f.lower().endswith(".docx")]

    if not files_to_process:
        print_status(f"Không tìm thấy file DOCX nào trong thư mục '{input_dir}'.", "WARN")
        sys.exit(0) # Thoát nếu không có file để xử lý

    # Duyệt qua từng file DOCX và xử lý
    for filename in tqdm(files_to_process, desc="Đang tách file DOCX"):
        docx_file_path = os.path.join(input_dir, filename)
        
        # Lấy tên kinh đầy đủ từ tên file (không có phần mở rộng)
        base_filename = os.path.splitext(filename)[0]
        
        # Ánh xạ tên file sang tên chuẩn Đại Chánh Tân Tu nếu có trong FILE_TO_META_KEY
        # Nếu không có, sử dụng tên file làm "Tên Kinh Đầy Đủ" để tìm metadata
        meta_key = FILE_TO_META_KEY.get(base_filename, base_filename)
        
        # Tạo tên file output an toàn
        ten_kinh_filename = base_filename.replace(" ", "_").replace("-", "_")

        print_status(f"Bắt đầu xử lý file: {filename}", "INFO")
        extract_data_from_docx(docx_file_path, output_dir, meta_key, ten_kinh_filename, metadata_index)
        print_status(f"Đã hoàn thành xử lý file: {filename}\n", "OK")

    print_status("Tất cả các file DOCX đã được trích xuất và chia thành các file JSON.", "OK")