import sys
import os
import shutil

# 确保项目根目录在路径中
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(backend_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from fastapi import APIRouter
from backend.RAG.SystemManager import system
from backend.RAG.FileCache import FileCache

router = APIRouter()

@router.post("/api/clear_cache")
def clear_cache():
    """
    清理无用文件缓存（真正不存在的文件）
    """
    try:
        cache_path = os.path.join(project_root, "data", "file_cache.json")
        file_cache = FileCache(cache_path)
        
        cleaned_count = file_cache.clean_nonexistent_files()
        
        print(f"🧹 清理了 {cleaned_count} 个无用文件缓存记录")
        
        return {"success": True, "message": f"清理了 {cleaned_count} 个无用文件缓存记录"}
        
    except Exception as e:
        print(f"清理缓存时出错: {e}")
        return {"error": f"清理缓存失败: {str(e)}"}

@router.post("/api/clear_index")
def clear_index():
    """
    清空向量索引
    """
    try:
        # 直接删除文件，不需要初始化系统
        index_path = os.path.join(project_root, "data", "faiss_index.bin")
        metadata_path = os.path.join(project_root, "data", "metadata.json")
        cache_path = os.path.join(project_root, "data", "file_cache.json")
        
        files_deleted = []
        
        if os.path.exists(index_path):
            os.remove(index_path)
            files_deleted.append("faiss_index.bin")
            
        if os.path.exists(metadata_path):
            os.remove(metadata_path)
            files_deleted.append("metadata.json")
        
        # 删除缓存文件
        if os.path.exists(cache_path):
            os.remove(cache_path)
            files_deleted.append("file_cache.json")
        
        # 清空系统管理器中的向量存储实例（如果已初始化）
        if system.is_initialized and system.vector_store:
            system.vector_store.index = None
            system.vector_store.metadata = []
        
        # 重置系统初始化状态，强制重新初始化
        system.is_initialized = False
        system.embedding_model = None
        system.vector_store = None
        
        print(f"索引和缓存已清空，删除文件: {', '.join(files_deleted)}")
        
        return {"success": True, "message": f"索引和缓存已清空，删除了 {len(files_deleted)} 个文件"}
        
    except Exception as e:
        print(f"清空索引时出错: {e}")
        return {"error": f"清空索引失败: {str(e)}"}
