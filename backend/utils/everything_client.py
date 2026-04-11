import requests
import json
import base64
import os
from datetime import datetime, timedelta


class EverythingClient:
    """
    Everything HTTP API Python 客户端
    基于官方文档: https://www.voidtools.com/support/everything/http/
    """

    def __init__(self, host='localhost', port=80, username=None, password=None):
        self.base_url = f"http://{host}:{port}"
        self.auth = (username, password) if username and password else None

    def search(self, query, count=1000, offset=0, sort='name', ascending=True):
        """
        执行搜索请求
        """
        params = {
            'search': query,
            'json': 1,
            'count': count,
            'offset': offset,
            'sort': sort,
            'ascending': 1 if ascending else 0,
            'path_column': 1,
            'size_column': 1,
            'date_modified_column': 1,
            'date_created_column': 1,
            'attributes_column': 1
        }

        try:
            response = requests.get(
                self.base_url,
                params=params,
                auth=self.auth,
                timeout=2
            )
            response.raise_for_status()

            data = response.json()
            return self._format_results(data.get('results', []))

        except requests.exceptions.ConnectionError:
            print(f"Error: 無法連接到 Everything HTTP 伺服器 ({self.base_url})。")
            print("請確保 Everything 正在運行，並且已在 [工具 -> 選項 -> HTTP 伺服器] 中啟用服務。")
            return "CONNECTION_ERROR"

    def _format_results(self, results):
        """
        格式化搜索结果
        """
        formatted = []
        for item in results:
            formatted.append({
                'name': item.get('name', ''),
                'path': item.get('path', ''),
                'size': self._format_size(item.get('size', 0)),
                'size_bytes': item.get('size', 0),
                'modified': self._format_datetime(item.get('date_modified', '')),
                'created': self._format_datetime(item.get('date_created', '')),
                'type': 'file'
            })
        return formatted

    def _format_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        size = float(size_bytes)
        while size >= 1024 and i < len(size_names) - 1:
            size /= 1024
            i += 1
        return f"{size:.2f} {size_names[i]}"

    def _format_datetime(self, date_str):
        """格式化日期时间"""
        if not date_str:
            return "-"
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            return date_str

    def get_files_in_folder(self, folder_path, recursive=False):
        """
        获取指定文件夹中的文件
        """
        if not folder_path:
            return []

        if recursive:
            query = f"folder:{folder_path}\\"
        else:
            query = f"parent:{folder_path}"

        return self.search(query)

    def is_available(self):
        """检查 Everything 服务是否可用"""
        try:
            response = requests.get(self.base_url, timeout=1)
            return response.status_code == 200
        except:
            return False
