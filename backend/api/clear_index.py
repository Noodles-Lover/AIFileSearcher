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

router = APIRouter()

@router.post("/api/clear_index")
def clear_index():
    """
    清空向量索引
    """
    try:
        # 直接删除文件，不需要初始化系统
        index_path = os.path.join(project_root, "data", "faiss_index.bin")
        metadata_path = os.path.join(project_root, "data", "metadata.json")
        
        files_deleted = []
        
        if os.path.exists(index_path):
            os.remove(index_path)
            files_deleted.append("faiss_index.bin")
            
        if os.path.exists(metadata_path):
            os.remove(metadata_path)
            files_deleted.append("metadata.json")
        
        # 清空系统管理器中的向量存储实例（如果已初始化）
        if system.is_initialized and system.vector_store:
            system.vector_store.index = None
            system.vector_store.metadata = []
        
        # 重置系统初始化状态，强制重新初始化
        system.is_initialized = False
        system.embedding_model = None
        system.vector_store = None
        
        print(f"索引已清空，删除文件: {', '.join(files_deleted)}")
        
        return {"success": True, "message": f"索引已清空，删除了 {len(files_deleted)} 个文件"}
        
    except Exception as e:
        print(f"清空索引时出错: {e}")
        return {"error": f"清空索引失败: {str(e)}"}
