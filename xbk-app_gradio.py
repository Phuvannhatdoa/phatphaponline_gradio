# app_gradio.py
import gradio as gr
import sys
from fastapi import FastAPI
import uvicorn
from rag_service import load_chroma_collection, rag_query

# Load collection khi khởi động
try:
    _ = load_chroma_collection()
    print("[Gradio App] ChromaDB collection đã được tải thành công.")
except Exception as e:
    print(f"[Gradio App] Lỗi nghiêm trọng khi tải ChromaDB: {e}")
    print("[Gradio App] Ứng dụng sẽ không hoạt động nếu không có cơ sở dữ liệu. Vui lòng kiểm tra logs.")
    sys.exit(1)

NO_INFO_ANSWER = "Xin lỗi, tôi không tìm thấy thông tin đủ chi tiết trong các Kinh đã được cung cấp để trả lời câu hỏi này."
RAG_ERROR_ANSWER_PREFIX = "Xin lỗi, có lỗi xảy ra khi xử lý yêu cầu của bạn:"

def query_and_answer(user_input):
    if not user_input.strip():
        return "Vui lòng nhập câu hỏi."

    try:
        results, answer = rag_query(user_input)

        is_no_info_response = (answer == NO_INFO_ANSWER)
        is_rag_error_response = answer.startswith(RAG_ERROR_ANSWER_PREFIX)

        final_output = f"🧠 **Câu trả lời từ AI:**\n{answer}\n\n"

        if not is_no_info_response and not is_rag_error_response:
            metadatas = results["metadatas"][0] if results and results["metadatas"] else []
            unique_sources = set()

            if metadatas:
                for metadata in metadatas:
                    bo = metadata.get('Bộ')
                    ten_kinh_day_du = metadata.get('Tên Kinh Đầy Đủ')
                    viet_dich = metadata.get('Việt Dịch')
                    so_pham = metadata.get('Số Phẩm')
                    ten_kinh_nho = metadata.get('Tên Kinh Nhỏ')

                    source_info_parts = []
                    if bo: source_info_parts.append(f"Bộ: {bo}")
                    if ten_kinh_day_du: source_info_parts.append(f"Kinh: {ten_kinh_day_du}")
                    if viet_dich: source_info_parts.append(f"Dịch: {viet_dich}")
                    if so_pham: source_info_parts.append(f"Phần: {so_pham}")
                    if ten_kinh_nho: source_info_parts.append(f"Kinh: {ten_kinh_nho}")

                    source_info = ", ".join(filter(None, source_info_parts))
                    if source_info:
                        unique_sources.add(source_info)

            sorted_unique_sources = sorted(list(unique_sources))

            if sorted_unique_sources:
                context_text = "\n".join([f"_ {s}_" for s in sorted_unique_sources])
                final_output += f"📚 **Ngữ cảnh liên quan từ:**\n{context_text}"
            else:
                final_output += "📚 **Không tìm thấy ngữ cảnh liên quan trong cơ sở dữ liệu.**"
        else:
            final_output += "📚 **Không có ngữ cảnh liên quan được hiển thị do thông tin không đủ hoặc lỗi.**"

        return final_output
    except Exception as e:
        return f"Lỗi khi xử lý: {str(e)}"

# Tạo giao diện Gradio
iface = gr.Interface(
    fn=query_and_answer,
    inputs=gr.Textbox(label="Nhập câu hỏi về Kinh điển", placeholder="Ví dụ: Năm sanh pháp là gì?", lines=2),
    outputs=gr.Textbox(label="Kết quả", lines=10),
    title="📜 Tra cứu Kinh điển Phật giáo (RAG + Chatling AI)",
    description="Hệ thống sử dụng ChromaDB + Chatling AI để trả lời câu hỏi từ dữ liệu Kinh Phật. Vui lòng đợi chút khi ứng dụng khởi động lần đầu.",
    theme="soft"
)

# Tạo FastAPI app và mount Gradio app vào
app = FastAPI()
gradio_app = gr.routes.App.create_app(iface)
gradio_app.blocks.config["dev_mode"] = False  # Tắt dev_mode để tránh reload loop
app.mount("/", gradio_app)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
