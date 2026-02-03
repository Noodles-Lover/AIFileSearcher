import sys
import os
import threading
import uvicorn

# 将 backend 目录添加到 sys.path，以便导入 api 模块
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from api.server import app as fastapi_app
from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtWebEngineWidgets import QWebEngineView

def run_api_server():
    """在后台线程运行 FastAPI 服务"""
    # log_level="error" 让控制台清爽一些，port 8000
    uvicorn.run(fastapi_app, host="127.0.0.1", port=8000, log_level="info")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 设置窗口标题
        self.setWindowTitle("AI File Searcher")
        
        # 设置窗口初始大小
        self.resize(1200, 800)
        
        # 创建 Web 视图
        self.browser = QWebEngineView()
        
        # 加载 React 开发服务器地址 (Vite 默认是 5173)
        self.browser.setUrl(QUrl("http://localhost:5173/"))
        
        # 将 Web 视图设置为中心组件，填满窗口
        self.setCentralWidget(self.browser)

def main():
    # 1. 启动 API 服务线程
    api_thread = threading.Thread(target=run_api_server, daemon=True)
    api_thread.start()
    print("Backend API server started on http://127.0.0.1:8000")

    # 2. 启动 GUI
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
