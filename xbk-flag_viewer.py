import gradio as gr
import pandas as pd
import os
import glob

# Đường dẫn đến thư mục chứa các file flagged data
# Đảm bảo đường dẫn này đúng với vị trí thư mục .gradio/flagged/ của bạn
# (Sau khi đã di chuyển nó vào thư mục Mongo-Rag hoặc vị trí chính xác trên server)
FLAGGED_DATA_DIR = os.path.join(os.path.dirname(__file__), '.gradio', 'flagged') 
# Nếu bạn vẫn chưa di chuyển .gradio vào Mongo-Rag, hãy dùng đường dẫn tuyệt đối:
# FLAGGED_DATA_DIR = "/root/.gradio/flagged/"


def read_flagged_data():
    """
    Đọc dữ liệu từ file datasetX.csv mới nhất, sắp xếp theo timestamp và trả về dưới dạng chuỗi HTML.
    """
    if not os.path.exists(FLAGGED_DATA_DIR):
        return f"<h3>Không tìm thấy thư mục dữ liệu được gắn cờ tại:</h3><p>{FLAGGED_DATA_DIR}</p>"

    # Tìm tất cả các file CSV trong thư mục, ưu tiên datasetX.csv
    csv_files = glob.glob(os.path.join(FLAGGED_DATA_DIR, 'dataset*.csv'))
    
    if not csv_files:
        return "<h3>Không tìm thấy file CSV nào trong thư mục đã gắn cờ. Vui lòng đảm bảo bạn đã nhấn nút 'Flag' trong ứng dụng chính.</h3>"

    # Sắp xếp các file theo thời gian sửa đổi để lấy file mới nhất
    latest_csv_file = max(csv_files, key=os.path.getmtime)
    
    try:
        df = pd.read_csv(latest_csv_file)
        
        if df.empty:
            return f"<h3>File '{os.path.basename(latest_csv_file)}' trống. Chưa có dữ liệu nào được 'Flag'.</h3>"

        # Cập nhật: Xử lý cột 'timestamp' theo định dạng thực tế
        if 'timestamp' in df.columns:
            # Chuyển đổi sang định dạng datetime, Gradio đang ghi là string
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce') 
            
            # Xóa các dòng có timestamp không hợp lệ (nếu có)
            df.dropna(subset=['timestamp'], inplace=True) 
            
            # Sắp xếp mới nhất lên đầu
            df = df.sort_values(by='timestamp', ascending=False) 
            
            # Định dạng lại cột timestamp để hiển thị đẹp hơn (tùy chọn)
            df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        else:
            print("Cột 'timestamp' không tìm thấy trong file CSV.") # Để debug nếu cần

        # Định dạng DataFrame thành HTML để hiển thị đẹp hơn
        html_table = df.to_html(index=False, escape=False) 
        return f"<h3>Dữ liệu được gắn cờ từ Gradio (từ file: {os.path.basename(latest_csv_file)}):</h3>{html_table}"

    except pd.errors.EmptyDataError:
        return f"<h3>File '{os.path.basename(latest_csv_file)}' trống. Chưa có dữ liệu nào được 'Flag'.</h3>"
    except Exception as e:
        return f"<h3>Lỗi khi đọc file CSV '{os.path.basename(latest_csv_file)}':</h3><p>{str(e)}</p>"

# Tạo giao diện Gradio
iface = gr.Interface(
    fn=read_flagged_data,
    inputs=[],
    outputs=gr.HTML(label="Báo cáo Dữ liệu Gắn cờ"),
    title="📊 Trình xem Dữ liệu Gắn cờ (Flagged Data Viewer)",
    description="Xem lại các lượt 'gắn cờ' từ ứng dụng tra cứu Kinh điển.",
    theme="soft"
)

if __name__ == "__main__":
    iface.launch(server_name="0.0.0.0", server_port=7861)