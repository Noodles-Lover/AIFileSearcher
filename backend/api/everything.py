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
                timeout=2 # 缩短超时时间
            )
            response.raise_for_status()
            
            data = response.json()
            return self._format_results(data.get('results', []))
            
        except requests.exceptions.ConnectionError:
            print(f"Error: 無法連接到 Everything HTTP 伺服器 ({self.base_url})。")
            print("請確保 Everything 正在運行，並且已在 [工具 -> 選項 -> HTTP 伺服器] 中啟用服務。")
            return "CONNECTION_ERROR" # 返回特殊標識
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to Everything Server: {e}")
            return []
        except json.JSONDecodeError:
            print("Error parsing JSON response")
            return []

    def get_files_in_folder(self, folder_path, recursive=False):
        """
        获取指定文件夹下的所有文件
        :param folder_path: 文件夹路径
        :param recursive: 是否递归搜索子目录
        """
        # 如果路径包含空格，用双引号包裹
        clean_path = folder_path.strip('"')
        
        if recursive:
            # 递归搜索：直接使用路径加反斜杠，Everything 会匹配该路径下的所有内容
            if not clean_path.endswith('\\'):
                clean_path += '\\'
            query = f'"{clean_path}" !folder:'
        else:
            # 非递归：使用 parent: 语法
            query = f'parent:"{clean_path}" !folder:'
            
        return self.search(query)

    def _format_results(self, results):
        formatted = []
        for item in results:
            # 安全地获取并转换文件大小
            size_raw = item.get('size')
            try:
                # 只有当 size_raw 存在且不为空字符串时才尝试转换
                size_bytes = int(size_raw) if size_raw else 0
            except (ValueError, TypeError):
                size_bytes = 0

            # 判断类型：Everything 的 attributes 中 16 (0x10) 代表目录
            # 也可以通过 size 是否为 None 或是否存在特定属性来辅助判断
            attributes = int(item.get('attributes', 0))
            is_folder = (attributes & 16) != 0
            
            # 过滤掉文件夹
            if is_folder:
                continue

            # 提取扩展名 (包含点，例如 .jpg)
            name = item.get('name', '')
            extension = os.path.splitext(name)[1].lower() if not is_folder else ''

            # 如果没有 attributes，尝试通过 size 辅助判断 (Everything 文件夹通常 size 为空)
            if attributes == 0 and item.get('size') is None:
                is_folder = True
                extension = ''
                # 过滤掉文件夹
                continue

            formatted.append({
                'name': name,
                'path': f"{item.get('path')}\{name}" if item.get('path') else name,
                'size': self._format_size(size_bytes),
                'size_bytes': size_bytes,
                'modified': self._filetime_to_datetime(item.get('date_modified')),
                'created': self._filetime_to_datetime(item.get('date_created')),
                'extension': extension,
                'type': 'folder' if is_folder else 'file'
            })
        return formatted

    def _filetime_to_datetime(self, filetime):
        """
        将 Windows FILETIME 转换为 Python datetime
        FILETIME 是从 1601-01-01 开始的 100 纳秒间隔
        """
        if not filetime:
            return None
        
        try:
            filetime = int(filetime)
            # 1601 到 1970 的秒数差
            EPOCH_DIFF = 11644473600
            # 转换为秒 (除以 10,000,000)
            seconds = (filetime / 10000000) - EPOCH_DIFF
            if seconds < 0: return None
            return datetime.fromtimestamp(seconds).strftime('%Y-%m-%d %H:%M:%S')
        except:
            return None

    def _format_size(self, size_bytes):
        """将字节转换为易读格式"""
        try:
            size = float(size_bytes)
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if size < 1024.0:
                    return f"{size:.2f} {unit}"
                size /= 1024.0
            return f"{size:.2f} PB"
        except:
            return "0 B"
