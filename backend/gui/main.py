import os
import sys
import threading
from pathlib import Path

import uvicorn
from PyQt6.QtCore import QObject, QUrl, pyqtSlot
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QApplication, QMainWindow

# Add backend directory to sys.path so API modules can be imported.
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(parent_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from api.server import app as fastapi_app
def run_api_server():
    uvicorn.run(fastapi_app, host="127.0.0.1", port=8000, log_level="info")


class FileBridge(QObject):
    def _resolve_path(self, relative_path: str) -> Path:
        root_path = Path(project_root).resolve()
        target_path = (root_path / relative_path).resolve()

        if target_path != root_path and root_path not in target_path.parents:
            raise ValueError("Access outside project root is not allowed")

        return target_path

    @pyqtSlot(str, result=str)
    def readTextFile(self, relative_path: str):
        try:
            file_path = self._resolve_path(relative_path)
            if not file_path.exists():
                return ""
            return file_path.read_text(encoding="utf-8")
        except Exception:
            return ""

    @pyqtSlot(str, str, result=bool)
    def writeTextFile(self, relative_path: str, content: str):
        try:
            file_path = self._resolve_path(relative_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            return True
        except Exception:
            return False

    @pyqtSlot(str, result=str)
    def listDirectories(self, relative_path: str):
        try:
            import json

            dir_path = self._resolve_path(relative_path)
            if not dir_path.exists() or not dir_path.is_dir():
                return "[]"

            directories = []
            for item in dir_path.iterdir():
                if not item.is_dir():
                    continue

                has_weights = False
                for root, _, files in os.walk(item):
                    for filename in files:
                        lower_name = filename.lower()
                        if lower_name.endswith(".safetensors") or lower_name == "pytorch_model.bin":
                            has_weights = True
                            break
                    if has_weights:
                        break

                if has_weights:
                    directories.append(item.name)

            directories.sort(key=str.lower)
            return json.dumps(directories, ensure_ascii=False)
        except Exception:
            return "[]"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI File Searcher")
        self.resize(1000, 600)

        self.browser = QWebEngineView()
        self.channel = QWebChannel(self.browser.page())
        self.file_bridge = FileBridge()
        self.channel.registerObject("fileBridge", self.file_bridge)
        self.browser.page().setWebChannel(self.channel)
        self.browser.setUrl(QUrl("http://localhost:5173/"))
        self.setCentralWidget(self.browser)


def main():
    api_thread = threading.Thread(target=run_api_server, daemon=True)
    api_thread.start()
    print("Backend API server started on http://127.0.0.1:8000")

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
