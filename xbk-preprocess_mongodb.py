# preprocess_mongodb.py
import os
import json
import datetime
from pymongo import MongoClient
import unicodedata
import re

# --- Cấu hình ---
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/') # Lấy từ env hoặc dùng default
DB_NAME = os.getenv('DB_NAME', 'kinhsachdb')
COLLECTION_SOURCE = os.getenv('COLLECTION_SOURCE', 'kinhsach_doan')

JSON_FOLDER = "data/Doc2Json"  # Thư mục chứa các file JSON gốc
NORMALIZED_JSON_FOLDER = "data/Doc2JsonNormalized" # Thư mục lưu JSON đã chuẩn hóa

MAX_TEXT_LENGTH = 512 # Độ dài tối đa của mỗi chunk văn bản

# --- Hàm kiểm tra và chuẩn hóa mã hóa ---
def check_and_normalize_encoding(input_folder, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    file_names = [f for f in os.listdir(input_folder) if f.endswith(".json")]
    print(f"Bắt đầu chuẩn hóa encoding cho {len(file_names)} files JSON.")
    for file_name in file_names:
        input_path = os.path.join(input_folder, file_name)
        output_path = os.path.join(output_folder, file_name)
        try:
            with open(input_path, 'r', encoding='utf-8') as infile:
                content = infile.read()
                normalized_content = unicodedata.normalize('NFC', content)
            with open(output_path, 'w', encoding='utf-8') as outfile:
                outfile.write(normalized_content)
        except UnicodeDecodeError:
            print(f"Cảnh báo: File '{file_name}' không phải là UTF-8 chuẩn. Vui lòng kiểm tra.")
        except Exception as e:
            print(f"Lỗi khi xử lý file '{file_name}': {e}")
    print("Hoàn tất chuẩn hóa encoding.")

# --- Hàm chunk văn bản ---
def chunk_text(text, max_length=MAX_TEXT_LENGTH):
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-ZĐ])', text) 
    chunks = []
    current_chunk = ""
    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 1 <= max_length:
            current_chunk += sentence + " "
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence + " "
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

# --- Hàm trích xuất nội dung và metadata ---
def extract_content_and_metadata(data, file_name):
    contents = []
    metadatas = []
    
    allowed_types = ["van_xuoi", "paragraph", "tieu_de_pham", "tieu_de_chuong", "tieu_de_bai_kinh", "tụng"]

    def extract_from_item(item, current_metadata, unique_texts, doan_so_counter):
        if isinstance(item, dict):
            new_metadata = current_metadata.copy()
            for key, value in item.items():
                if isinstance(value, (str, int, float, bool, type(None))):
                    new_metadata[key] = value

            text_to_extract = item.get("text") or item.get("tieu_de")

            if text_to_extract and item.get("type") in allowed_types and text_to_extract.strip():
                text_to_extract = text_to_extract.strip()
                if text_to_extract not in unique_texts:
                    chunks = chunk_text(text_to_extract)
                    for chunk in chunks:
                        contents.append(chunk)
                        meta_for_chunk = new_metadata.copy()
                        meta_for_chunk['doan_so'] = next(doan_so_counter) # Gán số đoạn tăng dần
                        metadatas.append(meta_for_chunk)
                    unique_texts.add(text_to_extract)
            
            if isinstance(item.get("content"), list):
                for sub_item in item["content"]:
                    extract_from_item(sub_item, new_metadata, unique_texts, doan_so_counter)
            elif isinstance(item.get("Noi_Dung"), list):
                for sub_item in item["Noi_Dung"]:
                    extract_from_item(sub_item, new_metadata, unique_texts, doan_so_counter)

    extracted_texts_set = set()
    from itertools import count
    doan_so_counter = count(1) # Bộ đếm số đoạn văn
    
    initial_metadata = {"source_file": file_name}

    if isinstance(data, dict):
        if "Noi_Dung" in data and isinstance(data["Noi_Dung"], list):
            for item in data["Noi_Dung"]:
                extract_from_item(item, initial_metadata, extracted_texts_set, doan_so_counter)
        else:
            extract_from_item(data, initial_metadata, extracted_texts_set, doan_so_counter)
    elif isinstance(data, list):
        for item in data:
            extract_from_item(item, initial_metadata, extracted_texts_set, doan_so_counter)
    else:
        print(f"Cảnh báo: Dữ liệu trong '{file_name}' không phải là dictionary hoặc list ở cấp cao nhất.")

    return contents, metadatas

# --- Hàm chính để xử lý JSON và lưu vào MongoDB ---
def process_json_to_mongodb():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    kinhsach_doan_collection = db[COLLECTION_SOURCE]

    # Xóa collection cũ để đảm bảo dữ liệu mới nhất
    kinhsach_doan_collection.drop()
    print(f"Collection '{COLLECTION_SOURCE}' trong MongoDB đã được xóa.")

    # Bước 1: Chuẩn hóa encoding các file JSON
    check_and_normalize_encoding(JSON_FOLDER, NORMALIZED_JSON_FOLDER)

    file_names = [f for f in os.listdir(NORMALIZED_JSON_FOLDER) if f.endswith(".json")]
    
    total_docs_added = 0
    for file_name in file_names:
        file_path = os.path.join(NORMALIZED_JSON_FOLDER, file_name)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            contents, metadatas = extract_content_and_metadata(data, file_name)
            
            docs_to_insert = []
            for i in range(len(contents)):
                doc_to_insert = {
                    'content': contents[i],
                    'metadata': metadatas[i],
                    'last_updated': datetime.datetime.now() # Thêm timestamp
                }
                docs_to_insert.append(doc_to_insert)
            
            if docs_to_insert:
                kinhsach_doan_collection.insert_many(docs_to_insert)
                total_docs_added += len(docs_to_insert)
                print(f"Đã thêm {len(docs_to_insert)} đoạn văn từ '{file_name}' vào MongoDB.")

        except Exception as e:
            print(f"Lỗi khi đọc hoặc xử lý file '{file_name}': {e}")
    
    print(f"\n--- Hoàn tất xử lý JSON và lưu vào MongoDB ---")
    print(f"Tổng số đoạn văn đã thêm vào collection '{COLLECTION_SOURCE}': {total_docs_added}")
    client.close()

if __name__ == "__main__":
    process_json_to_mongodb()