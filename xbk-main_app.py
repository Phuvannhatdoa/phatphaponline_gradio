# main_app.py
from fastapi import FastAPI
import uvicorn
import gradio as gr # Chỉ cần nếu bạn dùng gr.ChatInterface trực tiếp, không cần nếu app_gradio.py đã tạo nó

# Import Gradio app từ app_gradio.py
# app_gradio.py sẽ tạo ra một đối tượng Gradio ChatInterface và gán cho biến `app`
from app_gradio import app as gradio_app_instance

# Khởi tạo FastAPI app
app = FastAPI()

# Mount Gradio app vào FastAPI
# gradio_app_instance là đối tượng gr.ChatInterface từ app_gradio.py
app.mount("/", gradio_app_instance)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860) # <-- DÒNG QUAN TRỌNG NÀY PHẢI CÓ