"""
项目路径工具模块
统一处理项目根目录路径计算和导入路径管理
"""
import os
import sys
from typing import Optional


def get_project_root() -> str:
    """
    获取项目根目录路径
    适用于 backend 目录下的任何子模块
    """
    # 从当前文件的路径向上推算
    # backend/utils/path_utils.py -> backend/ -> project_root/
    current_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(current_dir)
    project_root = os.path.dirname(backend_dir)
    return project_root


def ensure_project_path():
    """
    确保项目根目录在 sys.path 中
    """
    project_root = get_project_root()
    if project_root not in sys.path:
        sys.path.append(project_root)
    return project_root


def get_data_path(filename: str) -> str:
    """
    获取 local_data 目录下文件的完整路径
    """
    project_root = get_project_root()
    return os.path.join(project_root, "local_data", filename)


def get_models_path(model_name: str = "") -> str:
    """
    获取 models 目录下模型的完整路径
    """
    project_root = get_project_root()
    if model_name:
        return os.path.join(project_root, "models", model_name)
    return os.path.join(project_root, "models")
