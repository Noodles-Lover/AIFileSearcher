import os
import base64
from PyQt6.QtWidgets import QFileIconProvider
from PyQt6.QtCore import QFileInfo, QIODevice, QBuffer
from PyQt6.QtGui import QIcon, QPixmap

class SystemIconManager:
    """
    系統圖標管理器：負責獲取、緩存和轉換系統原生圖標
    策略：
    - 目錄：統一使用 __folder__ 鍵
    - 唯一圖標 (.exe, .lnk等)：使用完整路徑作為鍵
    - 通用圖標：使用擴展名作為鍵
    """
    def __init__(self):
        self.icon_provider = QFileIconProvider()
        self.cache = {} # Key: CacheKey, Value: Base64 String

    def get_icon_base64(self, path: str):
        # 1. 預處理
        if not os.path.exists(path):
            return None
        
        is_dir = os.path.isdir(path)
        ext = os.path.splitext(path)[1].lower()
        
        # 2. 生成緩存鍵 (Generate Key)
        if is_dir:
            cache_key = "__folder__"
        elif ext in ['.exe', '.lnk', '.ico', '.cur', '.ani']:
            cache_key = path # 唯一圖標使用完整路徑
        else:
            cache_key = ext # 通用圖標使用擴展名

        # 3. 查詢緩存
        if cache_key in self.cache:
            return self.cache[cache_key]

        # 4. 調用系統獲取圖標 (QFileIconProvider 內部調用 SHGetFileInfo)
        file_info = QFileInfo(path)
        icon = self.icon_provider.icon(file_info)
        
        if icon.isNull():
            return None

        # 將 QIcon 轉換為 Base64 (32x32)
        pixmap = icon.pixmap(32, 32)
        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        pixmap.save(buffer, "PNG")
        base64_data = base64.b64encode(buffer.data().data()).decode()
        
        # 5. 更新緩存
        self.cache[cache_key] = base64_data
        return base64_data

# 全局單例
icon_manager = SystemIconManager()
