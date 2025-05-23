# Hệ thống RAG Tra cứu Kinh điển Phật giáo (Gradio + Chatling AI)

Dự án này triển khai một hệ thống Retrieval-Augmented Generation (RAG) cho phép tra cứu thông tin từ các Kinh điển Phật giáo. Hệ thống sử dụng MongoDB để lưu trữ dữ liệu đã được tiền xử lý, ChromaDB để quản lý các vector embedding cho truy xuất ngữ cảnh, và Chatling.ai làm mô hình ngôn ngữ lớn (LLM) để sinh câu trả lời. Giao diện người dùng được xây dựng bằng Gradio.

## Tính năng

* **Tiền xử lý dữ liệu:** Chuyển đổi file JSON nguồn sang cấu trúc phù hợp và lưu vào MongoDB.
* **Tạo Embeddings:** Tạo vector embeddings từ dữ liệu MongoDB và lưu trữ/quản lý trong ChromaDB.
* **Truy vấn RAG:** Tìm kiếm ngữ cảnh liên quan trong ChromaDB dựa trên câu hỏi của người dùng và chuyển ngữ cảnh đó cùng câu hỏi tới Chatling.ai để sinh câu trả lời.
* **Giao diện người dùng thân thiện:** Sử dụng Gradio để cung cấp một giao diện web đơn giản cho việc tương tác.

## Yêu cầu cài đặt

1.  **Python 3.8+**
2.  **MongoDB:** Đảm bảo MongoDB Server của bạn đang chạy.
3.  **Thư viện Python:**
    ```bash
    pip install gradio requests chromadb sentence-transformers python-dotenv pymongo
    ```

## Cấu trúc dự án
your_rag_project/
├── .env                  # Chứa các biến môi trường (API Keys, cấu hình DB)
├── app_gradio.py         # File chính để chạy ứng dụng Gradio
├── rag_service.py        # Logic RAG cốt lõi (kết nối DB, gọi API LLM)
├── preprocess_mongodb.py # Script tiền xử lý: JSON -> MongoDB
├── embed_to_chroma.py    # Script tạo embeddings: MongoDB -> ChromaDB
├── README.md             # File hướng dẫn này
├── data/
│   └── Doc2Json/
│       └── ... (Các file JSON Kinh điển gốc của bạn)
│   └── Doc2JsonNormalized/
│       └── ... (Thư mục này sẽ được tạo tự động để lưu JSON đã chuẩn hóa)
└── chroma_db_kinhsach/
└── ... (Thư mục lưu trữ cơ sở dữ liệu ChromaDB)


## Hướng dẫn sử dụng

### 1. Chuẩn bị môi trường

* **Tạo và điền file `.env`**:
    Tạo một file tên `.env` trong thư mục gốc của dự án. Điền các thông tin cấu hình và API key của bạn vào đó. **Đảm bảo thay thế các giá trị placeholder** bằng thông tin thực tế.

    ```ini
    # .env
    CHATLING_API_KEY="YOUR_CHATLING_API_KEY_HERE"
    CHATLING_BOT_ID="YOUR_CHATLING_BOT_ID_HERE"
    CHATLING_AI_MODEL_ID="8"

    MONGO_URI='mongodb://localhost:27017/'
    DB_NAME='kinhsachdb'
    COLLECTION_SOURCE='kinhsach_doan'

    CHROMA_PERSIST_DIR="./chroma_db_kinhsach"
    COLLECTION_NAME_CHROMA='kinhsach_embeddings'
    EMBEDDING_MODEL_NAME='intfloat/multilingual-e5-large'
    ```

* **Chuẩn bị dữ liệu JSON:**
    Đặt các file JSON chứa nội dung Kinh điển của bạn vào thư mục `data/Doc2Json/`.

### 2. Tiền xử lý dữ liệu và tạo Embeddings (Chạy một lần ban đầu hoặc khi dữ liệu thay đổi)

Đảm bảo MongoDB Server của bạn đang chạy.

1.  **Chuyển đổi JSON sang MongoDB:**
    Mở terminal và điều hướng đến thư mục gốc của dự án, sau đó chạy:
    ```bash
    python preprocess_mongodb.py
    ```
    Script này sẽ đọc các file JSON từ `data/Doc2Json/`, chuẩn hóa chúng, chunk văn bản, và lưu các đoạn văn đã xử lý vào collection `kinhsach_doan` trong MongoDB.

2.  **Tạo Embeddings và lưu vào ChromaDB:**
    Tiếp tục trong cùng terminal, chạy:
    ```bash
    python embed_to_chroma.py
    ```
    Script này sẽ kết nối với MongoDB, lấy các đoạn văn, tạo vector embeddings bằng `SentenceTransformer` và lưu chúng vào ChromaDB tại thư mục `chroma_db_kinhsach/`.

### 3. Chạy ứng dụng RAG với Gradio

1.  Mở một terminal mới (không đóng terminal MongoDB hoặc các script trên nếu chúng vẫn đang chạy).
2.  Điều hướng đến thư mục gốc của dự án.
3.  Chạy ứng dụng Gradio:
    ```bash
    python app_gradio.py
    ```
    Khi ứng dụng khởi động thành công, Gradio sẽ hiển thị một URL trong terminal (ví dụ: `http://0.0.0.0:7860/` hoặc `http://127.0.0.1:7860/`).

4.  **Mở trình duyệt web:**
    Truy cập URL được cung cấp trong terminal. Bạn sẽ thấy giao diện ứng dụng Gradio, nơi bạn có thể nhập câu hỏi và nhận câu trả lời từ hệ thống RAG của mình.

## Ghi chú quan trọng

* **Tính ổn định:** Đảm bảo MongoDB của bạn đang chạy trước khi chạy `preprocess_mongodb.py` và `embed_to_chroma.py`.
* **Mô hình Embedding:** Tên mô hình `intfloat/multilingual-e5-large` phải khớp chính xác giữa `embed_to_chroma.py` và `rag_service.py` để đảm bảo embeddings tương thích.
* **Kết nối mạng:** Chatling.ai là một dịch vụ API, vì vậy bạn cần kết nối internet ổn định để ứng dụng hoạt động.
* **Gỡ lỗi:** Nếu có lỗi, hãy kiểm tra output trong terminal của các script. Các thông báo `print()` đã được thêm vào để hỗ trợ gỡ lỗi.

Chúc bạn thành công với dự án của mình!