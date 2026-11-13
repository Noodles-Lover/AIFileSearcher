import os
import json
import time
from typing import Dict, List, Set, Any

class FileCache:
    def __init__(self, cache_path: str):
        self.cache_path = cache_path
        self.fileData: Dict[str, Dict[str, Any]] = {}  # {file_path: {vectors: [], fileSize: int, modified_time: int}}
        self.load_cache()
    
    def load_cache(self):
        """Load cache file"""
        if not os.path.exists(self.cache_path):
            print("Creating new file cache")
            return

        try:
            with open(self.cache_path, 'r', encoding='utf-8') as f:
                records = json.load(f).get('fileData', {})

            # 旧缓存记录的是物理下标，不能当作稳定 ID 使用
            if any('vector_ids' not in record for record in records.values()):
                print("File cache schema is incompatible; rebuild the index")
                self.fileData = {}
                return

            self.fileData = records
            print(f"File cache loaded: {len(self.fileData)} files")
        except Exception as e:
            print(f"Cache file corrupted, recreating: {e}")
            self.fileData = {}
    
    def save_cache(self):
        """Save cache to file"""
        try:
            data = {
                'fileData': self.fileData
            }
            with open(self.cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to save cache: {e}")
    
    def should_process_file(self, file_path: str) -> tuple[bool, str]:
        """Check if file needs processing"""
        try:
            current_mtime = int(os.path.getmtime(file_path))
            current_size = os.path.getsize(file_path)
        except FileNotFoundError:
            # 文件不存在，返回false但不删除缓存
            return False, "File not found"
        
        if file_path not in self.fileData:
            return True, "New file"
        
        cached_data = self.fileData[file_path]
        if cached_data['modified_time'] != current_mtime or cached_data['fileSize'] != current_size:
            return True, "File modified"
        
        return False, "File unchanged"
    
    def update_file_cache(self, file_path: str, vector_ids: List[int]):
        """Update file cache record"""
        try:
            current_mtime = int(os.path.getmtime(file_path))
            current_size = os.path.getsize(file_path)
            
            self.fileData[file_path] = {
                'vector_ids': vector_ids,
                'fileSize': current_size,
                'modified_time': current_mtime
            }
            
            self.save_cache()
        except Exception as e:
            print(f"Failed to update file cache: {e}")
    
    def get_vector_ids(self, file_path: str) -> List[int]:
        """Get stable vector IDs for file"""
        return self.fileData.get(file_path, {}).get('vector_ids', [])
    
    def remove_file_cache(self, file_path: str) -> List[int]:
        """Remove file cache record and return stable vector IDs"""
        vector_ids = self.fileData.get(file_path, {}).get('vector_ids', [])
        
        if file_path in self.fileData:
            del self.fileData[file_path]
            self.save_cache()
        
        return vector_ids
    
    def get_all_files(self) -> Set[str]:
        """Get all file paths in cache"""
        return set(self.fileData.keys())

    def get_files_under(self, folder_path: str) -> List[str]:
        """获取缓存中属于指定文件夹（含其子目录）的文件路径"""
        normalized_folder = os.path.normpath(folder_path).replace("/", "\\").lower()
        result = []
        for file_path in self.fileData:
            normalized_file = os.path.normpath(file_path).replace("/", "\\").lower()
            if normalized_file == normalized_folder or normalized_file.startswith(normalized_folder + "\\"):
                result.append(file_path)
        return result

    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        total_vectors = sum(len(data.get('vector_ids', [])) for data in self.fileData.values())
        return {
            'total_files': len(self.fileData),
            'total_vectors': total_vectors
        }
    
    def get_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """Get file metadata"""
        return self.fileData.get(file_path, {})
    
    def get_files_by_extension(self, extension: str) -> List[str]:
        """Get files by extension"""
        extension = extension.lower()
        return [
            file_path for file_path in self.fileData.keys()
            if file_path.lower().endswith(extension)
        ]