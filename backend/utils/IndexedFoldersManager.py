"""
已索引文件夹管理模块
用于管理和追踪已索引的文件夹路径及其索引完整性
"""
import os
import json
from typing import Dict

from .path_utils import get_data_path

INDEXED_FOLDERS_FILE = "indexed_folders.json"

class IndexedFoldersManager:
    """
    已索引文件夹管理器
    负责记录、读取和管理已索引的文件夹路径及其是否完整索引
    """

    def __init__(self):
        """初始化文件夹管理器"""
        self.file_path = get_data_path(INDEXED_FOLDERS_FILE)

    def get_indexed_folders(self) -> Dict[str, bool]:
        """
        获取所有已索引的文件夹路径及其完整性

        Returns:
            Dict[str, bool]: {文件夹路径: 是否完整索引}
        """
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    # 新格式：{path: {"complete": bool}}
                    return {str(k): bool(v.get("complete", True)) for k, v in data.items()}
                # 旧格式（纯路径列表）：全部视为完整索引
                return {str(p): True for p in data}
            except Exception as e:
                print(f"加载已索引文件夹记录失败: {e}")
                return {}
        return {}

    def add_folder(self, folder_path: str, complete: bool = True) -> None:
        """
        添加/更新一个已索引的文件夹

        Args:
            folder_path: 文件夹路径
            complete: 是否完整索引（取消的索引记为 False，增量续传完成前保持 False）
        """
        folders = self.get_indexed_folders()
        normalized_path = os.path.normpath(folder_path)
        folders[normalized_path] = complete
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
            p: v for p, v in folders.items()
            if not (p == normalized or p.startswith(normalized + os.sep))
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

    def _save(self, folders: Dict[str, bool]) -> None:
        """
        保存已索引文件夹记录（先写临时文件再替换，避免写一半损坏）

        Args:
            folders: {文件夹路径: 是否完整索引}
        """
        try:
            payload = {path: {"complete": complete} for path, complete in sorted(folders.items())}
            tmp_path = self.file_path + ".tmp"
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, self.file_path)
        except Exception as e:
            print(f"保存已索引文件夹记录失败: {e}")

# 单例实例
folders_manager = IndexedFoldersManager()
