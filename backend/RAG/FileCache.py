import os
import json
import time
from typing import Dict, List, Set

class FileCache:
    def __init__(self, cache_path: str):
        self.cache_path = cache_path
        self.cache: Dict[str, int] = {}  # {file_path: last_modified}
        self.file_to_vectors: Dict[str, List[int]] = {}  # {file_path: [vector_indices]}
        self.load_cache()
    
    def load_cache(self):
        """加载缓存文件"""
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.cache = data.get('cache', {})
                    self.file_to_vectors = data.get('file_to_vectors', {})
                    print(f"📂 加载文件缓存: {len(self.cache)} 个文件")
            except Exception as e:
                print(f"⚠️ 缓存文件损坏，重新创建: {e}")
                self.cache = {}
                self.file_to_vectors = {}
        else:
            print("📂 创建新的文件缓存")
    
    def save_cache(self):
        """保存缓存文件"""
        try:
            data = {
                'cache': self.cache,
                'file_to_vectors': self.file_to_vectors
            }
            with open(self.cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ 缓存保存失败: {e}")
    
    def should_process_file(self, file_path: str) -> tuple[bool, str]:
        """判断是否需要处理文件"""
        try:
            current_mtime = int(os.path.getmtime(file_path))
        except FileNotFoundError:
            # 文件不存在，返回false但不删除缓存
            return False, "文件不存在"
        
        if file_path not in self.cache:
            return True, "新文件"
        
        if self.cache[file_path] != current_mtime:
            return True, "文件已修改"
        
        return False, "文件未修改"
    
    def update_file_cache(self, file_path: str, vector_indices: List[int]):
        """更新文件缓存记录"""
        try:
            current_mtime = int(os.path.getmtime(file_path))
            self.cache[file_path] = current_mtime
            self.file_to_vectors[file_path] = vector_indices
            self.save_cache()
        except Exception as e:
            print(f"⚠️ 更新文件缓存失败: {e}")
    
    def get_file_vectors(self, file_path: str) -> List[int]:
        """获取文件对应的向量索引"""
        return self.file_to_vectors.get(file_path, [])
    
    def remove_file_cache(self, file_path: str) -> List[int]:
        """删除文件缓存记录，返回要删除的向量索引"""
        vector_indices = self.file_to_vectors.get(file_path, [])
        
        if file_path in self.cache:
            del self.cache[file_path]
        
        if file_path in self.file_to_vectors:
            del self.file_to_vectors[file_path]
        
        self.save_cache()
        return vector_indices
    
    def get_all_files(self) -> Set[str]:
        """获取缓存中所有文件路径"""
        return set(self.cache.keys())
    
    def clean_orphaned_files(self, existing_files: Set[str]):
        """清理不存在文件的缓存记录"""
        orphaned_files = self.get_all_files() - existing_files
        
        for file_path in orphaned_files:
            if file_path in self.cache:
                del self.cache[file_path]
            if file_path in self.file_to_vectors:
                del self.file_to_vectors[file_path]
        
        if orphaned_files:
            self.save_cache()
    
    def clean_nonexistent_files(self):
        """清理真正不存在的文件缓存记录（检查文件系统）"""
        files_to_remove = []
        
        for file_path in self.cache.keys():
            # 使用更可靠的文件存在性检查
            if not os.path.exists(file_path):
                files_to_remove.append(file_path)
        
        for file_path in files_to_remove:
            if file_path in self.cache:
                del self.cache[file_path]
            if file_path in self.file_to_vectors:
                del self.file_to_vectors[file_path]
        
        if files_to_remove:
            self.save_cache()
            print(f"🧹 清理了 {len(files_to_remove)} 个无用文件缓存记录")
        
        return len(files_to_remove)
    
    def get_stats(self) -> Dict[str, int]:
        """获取缓存统计信息"""
        return {
            'total_files': len(self.cache),
            'total_vectors': sum(len(indices) for indices in self.file_to_vectors.values())
        }
