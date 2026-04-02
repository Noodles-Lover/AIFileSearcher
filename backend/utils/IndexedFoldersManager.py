"""
已索引文件夹管理模块
用于管理和追踪已索引的文件夹路径
"""
import os
import json
from typing import Set

from .path_utils import get_data_path

INDEXED_FOLDERS_FILE = "indexed_folders.json"

class IndexedFoldersManager:
    """
    已索引文件夹管理器
    负责记录、读取和管理已索引的文件夹路径
    """
    
    def __init__(self):
        """初始化文件夹管理器"""
        self.file_path = get_data_path(INDEXED_FOLDERS_FILE)
    
    def get_indexed_folders(self) -> Set[str]:
        """
        获取所有已索引的文件夹路径
        
        Returns:
            Set[str]: 已索引文件夹路径的集合
        """
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return set(json.load(f))
            except Exception as e:
                print(f"加载已索引文件夹记录失败: {e}")
                return set()
        return set()
    
    def add_folder(self, folder_path: str) -> None:
        """
        添加一个已索引的文件夹
        
        Args:
            folder_path: 文件夹路径
        """
        folders = self.get_indexed_folders()
        normalized_path = os.path.normpath(folder_path)
        folders.add(normalized_path)
        self._save(folders)
    
    def remove_folder(self, folder_path: str) -> None:
        """
        移除一个已索引的文件夹及其子文件夹
        
        Args:
            folder_path: 文件夹路径
        """
        folders = self.get_indexed_folders()
        normalized = os.path.normpath(folder_path)
        # 移除该文件夹及其所有子文件夹的记录
        folders = {
            f for f in folders 
            if not (f == normalized or f.startswith(normalized + os.sep))
        }
        self._save(folders)
    
    def clear(self) -> None:
        """
        清空所有已索引文件夹记录
        """
        if os.path.exists(self.file_path):
            try:
                os.remove(self.file_path)
            except Exception as e:
                print(f"清空已索引文件夹记录失败: {e}")
    
    def _save(self, folders: Set[str]) -> None:
        """
        保存已索引文件夹记录
        
        Args:
            folders: 已索引文件夹路径的集合
        """
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(sorted(folders), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存已索引文件夹记录失败: {e}")

# 单例实例
folders_manager = IndexedFoldersManager()