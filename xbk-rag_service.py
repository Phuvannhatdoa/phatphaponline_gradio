# rag_service.py

import os
import json
import requests
import chromadb
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import logging # <--- THÊM DÒNG NÀY
import sys
load_dotenv() # Tải biến môi trường

# Cấu hình logging cơ bản (THÊM PHẦN NÀY)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Cấu hình ---
CHATLING_API_KEY = os.getenv("CHATLING_API_KEY")
CHATLING_BOT_ID = os.getenv("CHATLING_BOT_ID")
CHATLING_AI_MODEL_ID = os.getenv("CHATLING_AI_MODEL_ID")

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR")
COLLECTION_NAME_CHROMA = os.getenv("COLLECTION_NAME_CHROMA")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME")

# Định nghĩa các thông báo lỗi đặc biệt (để khớp với app_gradio.py)
NO_INFO_ANSWER = "Xin lỗi, tôi không tìm thấy thông tin đủ chi tiết trong các Kinh đã được cung cấp để trả lời câu hỏi này."
RAG_ERROR_ANSWER_PREFIX = "Xin lỗi, có lỗi xảy ra khi xử lý yêu cầu của bạn:"

# Kiểm tra các biến môi trường cần thiết
if not all([CHATLING_API_KEY, CHATLING_BOT_ID, CHATLING_AI_MODEL_ID,
             CHROMA_PERSIST_DIR, COLLECTION_NAME_CHROMA, EMBEDDING_MODEL_NAME]):
    logging.error("Vui lòng thiết lập đầy đủ các biến môi trường trong file .env") # Thay raise ValueError bằng logging.error và thoát
    sys.exit(1) # Thoát nếu thiếu biến môi trường

# --- Khởi tạo các thành phần RAG toàn cục ---
try:
    logging.info(f"[RAG Service] Đang tải mô hình embedding: {EMBEDDING_MODEL_NAME}...") # <--- THAY ĐỔI
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    logging.info("[RAG Service] Mô hình embedding đã tải.") # <--- THAY ĐỔI
except Exception as e:
    logging.error(f"[RAG Service] Lỗi khi tải mô hình embedding: {e}", exc_info=True) # <--- THAY ĐỔI
    sys.exit(f"Không thể khởi tạo mô hình embedding: {e}. Vui lòng kiểm tra tên mô hình và kết nối internet.") # <--- THAY ĐỔI


try:
    logging.info(f"[RAG Service] Đang kết nối tới ChromaDB tại: {CHROMA_PERSIST_DIR}...") # <--- THAY ĐỔI
    chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    chroma_collection = chroma_client.get_collection(name=COLLECTION_NAME_CHROMA)
    logging.info(f"[RAG Service] Đã kết nối tới ChromaDB collection '{COLLECTION_NAME_CHROMA}'. Tổng số documents: {chroma_collection.count()}") # <--- THAY ĐỔI
    if chroma_collection.count() == 0:
        logging.warning("[RAG Service] Cảnh báo: ChromaDB collection rỗng. Vui lòng chạy embed_to_chroma.py để nạp dữ liệu.") # <--- THAY ĐỔI
except Exception as e:
    logging.error(f"[RAG Service] Lỗi khi kết nối hoặc tải ChromaDB collection: {e}", exc_info=True) # <--- THAY ĐỔI
    logging.error("[RAG Service] Đảm bảo bạn đã chạy embed_to_chroma.py để tạo dữ liệu.") # <--- THAY ĐỔI
    sys.exit(f"Không thể kết nối tới ChromaDB: {e}. Vui lòng kiểm tra đường dẫn và đảm bảo đã chạy embed_to_chroma.py.") # <--- THAY ĐỔI


# --- Hàm để tải collection ChromaDB (cho Gradio app) ---
def load_chroma_collection():
    return chroma_collection

# --- Hàm gọi Chatling.ai API (ĐÃ CẬP NHẬT) ---
def get_chatling_response(question: str, context_docs: list, ai_model_id: str) -> str:
    url = f"https://api.chatling.ai/v2/chatbots/{CHATLING_BOT_ID}/ai/kb/chat"
    headers = {
        "Authorization": f"Bearer {CHATLING_API_KEY}",
        "Content-Type": "application/json"
    }

    context_string = "\n".join(context_docs).strip()

    if context_string:
        prompt_message = (
            f"Dựa vào các đoạn văn sau, hãy trả lời câu hỏi: '{question}'. "
            "Nếu câu trả lời không thể tìm thấy trực tiếp hoặc suy luận rõ ràng từ các đoạn văn được cung cấp, "
            "hãy nói chính xác: 'Xin lỗi, tôi không tìm thấy thông tin đủ chi tiết trong các Kinh đã được cung cấp để trả lời câu hỏi này.' "
            "Không suy diễn thông tin từ kiến thức chung của bạn. "
            "\n\nCác đoạn văn được cung cấp:\n"
            f"'''\n{context_string}\n'''"
        )
        payload_context = []
    else:
        prompt_message = question
        payload_context = []

    payload = json.dumps({
        "message": prompt_message,
        "context": payload_context,
        "ai_model_id": int(ai_model_id),
        "context_strategy": "strict"
    })

    try:
        logging.info(f"[Chatling API] Gửi yêu cầu tới Chatling.ai cho câu hỏi: '{question}'...") # <--- THAY ĐỔI
        response = requests.post(url, headers=headers, data=payload, timeout=90)
        response.raise_for_status()

        json_response = response.json()
        answer = json_response.get("data", {}).get("response")

        # Thêm log để xem phản hồi từ Chatling API
        logging.info(f"[Chatling API] Phản hồi từ Chatling.ai (một phần): {json_response}") # <--- THÊM LOG NÀY

        if not answer or answer.strip() == "" or \
           NO_INFO_ANSWER.lower() in answer.lower() or \
           "tôi không tìm thấy thông tin" in answer.lower() or \
           "không có thông tin này" in answer.lower():
            logging.info("[Chatling API] Chatling.ai trả về câu trả lời không có thông tin hoặc rỗng.") # <--- THÊM LOG NÀY
            return NO_INFO_ANSWER

        return answer
    except requests.exceptions.RequestException as e:
        logging.error(f"[Chatling API] Lỗi khi gọi Chatling.ai API: {e}", exc_info=True) # <--- THAY ĐỔI
        if 'response' in locals() and response is not None: # Kiểm tra biến response có tồn tại không
            logging.error(f"[Chatling API] Nội dung phản hồi: {response.text}") # <--- THAY ĐỔI
        return RAG_ERROR_ANSWER_PREFIX + str(e)
    except json.JSONDecodeError as e:
        logging.error(f"[Chatling API] Lỗi giải mã JSON từ Chatling.ai: {e}", exc_info=True) # <--- THAY ĐỔI
        return "Xin lỗi, có lỗi khi nhận câu trả lời từ dịch vụ AI."
    except Exception as e: # Bắt các lỗi chung khác
        logging.error(f"[Chatling API] Lỗi không xác định trong get_chatling_response: {e}", exc_info=True)
        return RAG_ERROR_ANSWER_PREFIX + "Lỗi không xác định khi gọi AI."


# --- Hàm RAG chính ---
def rag_query(user_query: str, num_results: int = 5) -> tuple:
    logging.info(f"[RAG Query] Bắt đầu xử lý truy vấn RAG cho: '{user_query}'") # <--- THÊM LOG
    try:
        # 1. Tạo embedding cho câu hỏi
        logging.info("[RAG Query] Tạo embedding cho câu hỏi...") # <--- THAY ĐỔI
        query_embedding = model.encode(user_query).tolist()
        logging.info("[RAG Query] Đã tạo embedding cho câu hỏi.") # <--- THÊM LOG

        # 2. Tìm kiếm các đoạn văn liên quan trong ChromaDB
        logging.info(f"[RAG Query] Đang tìm kiếm {num_results} đoạn văn liên quan trong ChromaDB cho: '{user_query}'") # <--- THAY ĐỔI
        results_from_chroma = chroma_collection.query(
            query_embeddings=[query_embedding],
            n_results=num_results,
            include=["documents", "metadatas", "distances"]
        )
        context_docs = results_from_chroma["documents"][0] if results_from_chroma and results_from_chroma["documents"] and results_from_chroma["documents"][0] else []
        logging.info(f"[RAG Query] Đã tìm thấy {len(context_docs)} đoạn văn từ ChromaDB.") # <--- THÊM LOG

        if not context_docs:
            logging.warning("[RAG Query] Không tìm thấy ngữ cảnh nào trong ChromaDB cho câu hỏi này.")
            # Trả về kết quả rỗng và thông báo "không tìm thấy thông tin"
            return {}, NO_INFO_ANSWER

        # 3. Gửi câu hỏi và context tới Chatling.ai
        logging.info("[RAG Query] Gửi câu hỏi và ngữ cảnh tới Chatling.ai...") # <--- THÊM LOG
        answer = get_chatling_response(user_query, context_docs, CHATLING_AI_MODEL_ID)
        logging.info(f"[RAG Query] Nhận được câu trả lời từ Chatling.ai (một phần): {answer[:50]}...") # <--- THÊM LOG

        return results_from_chroma, answer
    except Exception as e:
        logging.error(f"[RAG Query] Lỗi không xác định trong hàm rag_query: {e}", exc_info=True) # <--- THÊM LOG LỖI TỔNG QUÁT
        return {}, RAG_ERROR_ANSWER_PREFIX + "Lỗi không xác định trong quá trình RAG."


# (Phần này không thay đổi, chỉ để hoàn chỉnh file)
if __name__ == "__main__":
    logging.info("Đây là module RAG Service. Vui lòng chạy app_gradio.py để tương tác.") # <--- THAY ĐỔI