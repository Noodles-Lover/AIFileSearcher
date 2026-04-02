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
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # 向后兼容：处理旧格式
                    if 'fileData' in data:
                        self.fileData = data.get('fileData', {})
                    else:
                        # 从旧格式迁移到新格式
                        self.fileData = {}
                        old_cache = data.get('cache', {})
                        old_file_to_vectors = data.get('file_to_vectors', {})
                        
                        for file_path, modified_time in old_cache.items():
                            self.fileData[file_path] = {
                                'vectors': old_file_to_vectors.get(file_path, []),
                                'fileSize': 0,  # 旧格式没有文件大小，设为0
                                'modified_time': modified_time
                            }
                    
                    print(f"File cache loaded: {len(self.fileData)} files")
            except Exception as e:
                print(f"Cache file corrupted, recreating: {e}")
                self.fileData = {}
        else:
            print("Creating new file cache")
    
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
    
    def update_file_cache(self, file_path: str, vector_indices: List[int]):
        """Update file cache record"""
        try:
            current_mtime = int(os.path.getmtime(file_path))
            current_size = os.path.getsize(file_path)
            
            self.fileData[file_path] = {
                'vectors': vector_indices,
                'fileSize': current_size,
                'modified_time': current_mtime
            }
            
            self.save_cache()
        except Exception as e:
            print(f"Failed to update file cache: {e}")
    
    def get_file_vectors(self, file_path: str) -> List[int]:
        """Get vector indices for file"""
        return self.fileData.get(file_path, {}).get('vectors', [])
    
    def remove_file_cache(self, file_path: str) -> List[int]:
        """Remove file cache record and return vector indices to delete"""
        vector_indices = self.fileData.get(file_path, {}).get('vectors', [])
        
        if file_path in self.fileData:
            del self.fileData[file_path]
            self.save_cache()
        
        return vector_indices
    
    def get_all_files(self) -> Set[str]:
        """Get all file paths in cache"""
        return set(self.fileData.keys())
    
    def clean_orphaned_files(self, existing_files: Set[str]):
        """Clean orphaned files not in existing_files"""
        orphaned_files = self.get_all_files() - existing_files
        
        for file_path in orphaned_files:
            if file_path in self.fileData:
                del self.fileData[file_path]
        
        if orphaned_files:
            self.save_cache()
    
    def clean_nonexistent_files(self):
        """Clean files that don't exist on filesystem"""
        files_to_remove = []
        
        for file_path in self.fileData.keys():
            # 使用更可靠的文件存在性检查
            if not os.path.exists(file_path):
                files_to_remove.append(file_path)
        
        for file_path in files_to_remove:
            if file_path in self.fileData:
                del self.fileData[file_path]
        
        if files_to_remove:
            self.save_cache()
            print(f"Cleaned {len(files_to_remove)} orphaned file cache records")
        
        return len(files_to_remove)
    
    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        total_vectors = sum(len(data.get('vectors', [])) for data in self.fileData.values())
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