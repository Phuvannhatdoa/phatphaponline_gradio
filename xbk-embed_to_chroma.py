# embed_to_chroma.py
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
import chromadb
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv() # Tải biến môi trường

# --- Cấu hình ---
MONGO_URI = os.getenv('MONGO_URI')
DB_NAME = os.getenv('DB_NAME')
COLLECTION_SOURCE = os.getenv('COLLECTION_SOURCE')

PERSIST_DIRECTORY = os.getenv('CHROMA_PERSIST_DIR')
client_chroma = chromadb.PersistentClient(path=PERSIST_DIRECTORY)

COLLECTION_NAME_CHROMA = os.getenv('COLLECTION_NAME_CHROMA')
EMBEDDING_MODEL_NAME = os.getenv('EMBEDDING_MODEL_NAME')

# --- Hàm hỗ trợ ---
def get_documents_from_mongo(mongo_uri, db_name, collection_name):
    client = MongoClient(mongo_uri)
    db = client[db_name]
    collection = db[collection_name]
    documents = []
    print(f"Đang lấy dữ liệu từ MongoDB ({db_name}.{collection_name})...")
    for doc in collection.find({}, {'_id': 1, 'content': 1, 'metadata': 1, 'last_updated': 1}):
        doc['_id'] = str(doc['_id']) # Chuyển ObjectId sang string để làm ID cho ChromaDB
        documents.append(doc)
    client.close()
    return documents

def parse_last_updated(value):
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace('Z', '+00:00')) # Xử lý định dạng ISO
        except ValueError:
            pass
    return datetime.min # Trả về ngày nhỏ nhất nếu không thể parse

# --- Hàm chính để tạo và lưu Embeddings ---
def create_embeddings_and_store_in_chroma():
    print(f"Đang tải mô hình embedding: {EMBEDDING_MODEL_NAME}...")
    try:
        model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        print("Đã tải mô hình embedding thành công.")
    except Exception as e:
        print(f"Lỗi khi tải mô hình embedding: {e}")
        return

    mongo_docs = get_documents_from_mongo(MONGO_URI, DB_NAME, COLLECTION_SOURCE)
    print(f"Đã lấy {len(mongo_docs)} đoạn văn từ MongoDB.")

    if not mongo_docs:
        print("Không có document nào để xử lý trong MongoDB.")
        return

    collection_chroma = client_chroma.get_or_create_collection(name=COLLECTION_NAME_CHROMA)
    print(f"Đã kết nối hoặc tạo ChromaDB collection: '{COLLECTION_NAME_CHROMA}'.")

    print("Đang lấy thông tin các document hiện có trong ChromaDB...")
    existing_chroma_data = {} # {id_mongo: last_updated_datetime}
    try:
        all_chroma_results = collection_chroma.get(ids=None, include=['metadatas'])
        for i, _id in enumerate(all_chroma_results.get('ids', [])):
            metadata = all_chroma_results['metadatas'][i]
            if metadata and 'last_updated' in metadata:
                existing_chroma_data[_id] = parse_last_updated(metadata['last_updated'])
            else:
                existing_chroma_data[_id] = datetime.min # Coi như rất cũ nếu không có timestamp
        print(f"Tìm thấy {len(existing_chroma_data)} document hiện có trong ChromaDB.")
    except Exception as e:
        print(f"Cảnh báo: Không thể lấy ID/metadata từ ChromaDB. Lỗi: {e}. Có thể collection rỗng.")
        existing_chroma_data = {}

    docs_to_add = []
    docs_to_update = []

    print("Đang phân loại các đoạn văn cần thêm/cập nhật...")
    for doc in mongo_docs:
        doc_id = doc['_id']
        mongo_last_updated = parse_last_updated(doc.get('last_updated', datetime.min))
        
        if doc_id not in existing_chroma_data:
            docs_to_add.append(doc)
        elif mongo_last_updated > existing_chroma_data[doc_id]:
            docs_to_update.append(doc)
    
    print(f"Tìm thấy {len(docs_to_add)} đoạn văn mới cần thêm.")
    print(f"Tìm thấy {len(docs_to_update)} đoạn văn cần cập nhật.")

    if docs_to_add:
        print("Đang tạo embeddings và thêm các đoạn văn mới vào ChromaDB...")
        batch_size = 100 
        for i in range(0, len(docs_to_add), batch_size):
            batch_docs = docs_to_add[i:i+batch_size]
            batch_contents = [d.get('content', '') for d in batch_docs]
            batch_embeddings = model.encode(batch_contents, show_progress_bar=False).tolist()
            batch_ids = [d['_id'] for d in batch_docs]
            batch_metadatas = []
            for d in batch_docs:
                filtered_meta = {k: v for k, v in d['metadata'].items() if isinstance(v, (str, int, float, bool))}
                if 'last_updated' in d and isinstance(d['last_updated'], (str, datetime)):
                    filtered_meta['last_updated'] = str(d['last_updated']) # Đảm bảo là string
                batch_metadatas.append(filtered_meta)

            try:
                collection_chroma.add(
                    embeddings=batch_embeddings,
                    documents=batch_contents,
                    metadatas=batch_metadatas,
                    ids=batch_ids
                )
                print(f"  Đã thêm {len(batch_contents)} embeddings mới (Batch {i//batch_size + 1}/{len(docs_to_add)//batch_size + 1})")
            except Exception as e:
                print(f"Lỗi khi thêm batch vào ChromaDB (add): {e}")
                print(f"  Batch IDs gây lỗi: {batch_ids}")
                # Có thể log chi tiết hơn hoặc bỏ qua lỗi để tiếp tục với các batch khác
                
    if docs_to_update:
        print("Đang tạo embeddings và cập nhật các đoạn văn trong ChromaDB...")
        batch_size = 100
        for i in range(0, len(docs_to_update), batch_size):
            batch_docs = docs_to_update[i:i+batch_size]
            batch_contents = [d.get('content', '') for d in batch_docs]
            batch_embeddings = model.encode(batch_contents, show_progress_bar=False).tolist()
            batch_ids = [d['_id'] for d in batch_docs]
            batch_metadatas = []
            for d in batch_docs:
                filtered_meta = {k: v for k, v in d['metadata'].items() if isinstance(v, (str, int, float, bool))}
                if 'last_updated' in d and isinstance(d['last_updated'], (str, datetime)):
                    filtered_meta['last_updated'] = str(d['last_updated']) # Đảm bảo là string
                batch_metadatas.append(filtered_meta)

            try:
                collection_chroma.upsert(
                    embeddings=batch_embeddings,
                    documents=batch_contents,
                    metadatas=batch_metadatas,
                    ids=batch_ids
                )
                print(f"  Đã cập nhật {len(batch_contents)} embeddings (Batch {i//batch_size + 1}/{len(docs_to_update)//batch_size + 1})")
            except Exception as e:
                print(f"Lỗi khi cập nhật batch vào ChromaDB (upsert): {e}")
                print(f"  Batch IDs gây lỗi: {batch_ids}")
                # Có thể log chi tiết hơn hoặc bỏ qua lỗi để tiếp tục với các batch khác

    if not docs_to_add and not docs_to_update:
        print("Không có đoạn văn mới hoặc cập nhật nào để xử lý.")

    print("\n--- Hoàn tất quá trình đồng bộ embeddings vào ChromaDB ---")
    print(f"Tổng số document trong ChromaDB collection '{COLLECTION_NAME_CHROMA}': {collection_chroma.count()}")

if __name__ == "__main__":
    create_embeddings_and_store_in_chroma()