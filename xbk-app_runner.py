# app_runner.py
import uvicorn
from main_app import app # Import FastAPI app từ main_app.py

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
