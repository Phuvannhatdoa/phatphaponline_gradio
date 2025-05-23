# app_test.py
import gradio as gr
import sys
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler(sys.stdout)])

def chat_response(message, history):
    # Lịch sử là list các cặp [user_message, bot_message]
    # message là tin nhắn mới nhất của người dùng
    
    # Bạn có thể thêm logic xử lý của mình ở đây
    # Ví dụ đơn giản:
    return f"Bạn hỏi: {message}"

with gr.Blocks(title="Custom Chatbot") as app:
    gr.Markdown(
        """
        # Minimal Chatbot with Blocks
        Đây là một chatbot Gradio tối thiểu để kiểm tra.
        """
    )
    chatbot = gr.Chatbot(height=400)
    msg = gr.Textbox(placeholder="Nhập câu hỏi...", container=False, scale=7)
    clear = gr.ClearButton([msg, chatbot])

    def user_message(user_message, history):
        return "", history + [[user_message, None]]

    msg.submit(user_message, [msg, chatbot], [msg, chatbot], queue=False).then(
        chat_response, chatbot, chatbot
    )

    clear.click(lambda: (None, None), None, [msg, chatbot], queue=False)

# KHÔNG DÙNG .launch() ở đây vì Uvicorn sẽ chạy app
# app.launch() # Không kích hoạt dòng này