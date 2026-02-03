import requests
import json
import base64
from datetime import datetime, timedelta

class EverythingClient:
    """
    Everything HTTP API Python 客户端
    基于官方文档: https://www.voidtools.com/support/everything/http/
    """
    
    def __init__(self, host='localhost', port=80, username=None, password=None):
        self.base_url = f"http://{host}:{port}"
        self.auth = (username, password) if username and password else None
        
    def search(self, query, count=100, offset=0, sort='name', ascending=True):
        """
        执行搜索请求
        
        :param query: 搜索关键词 (支持 Everything 语法)
        :param count: 返回结果数量限制
        :param offset: 分页偏移量
        :param sort: 排序字段 (name, path, size, date_modified, date_created, etc.)
        :param ascending: 是否升序
        :return: 格式化后的文件列表
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
            'date_modified_column': 1
        }
        
        try:
            response = requests.get(
                self.base_url, 
                params=params, 
                auth=self.auth,
                timeout=5
            )
            response.raise_for_status()
            
            data = response.json()
            return self._format_results(data.get('results', []))
            
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
            query = f'"{clean_path}"'
        else:
            # 非递归：使用 parent: 语法
            query = f'parent:"{clean_path}"'
            
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

            formatted.append({
                'name': item.get('name'),
                'path': f"{item.get('path')}\\{item.get('name')}" if item.get('path') else item.get('name'),
                'size': self._format_size(size_bytes),
                'size_bytes': size_bytes,
                'modified': self._filetime_to_datetime(item.get('date_modified')),
                'type': 'folder' if item.get('type') == 'folder' else 'file' # Everything 可能不直接返回 type，通常通过属性判断，这里简化
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
