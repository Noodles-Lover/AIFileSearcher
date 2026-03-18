"""
RAG (Retrieval-Augmented Generation) 模块

包含向量检索相关的核心组件：
- EmbeddingModel: 文本嵌入模型
- VectorStore: FAISS向量存储
- SystemManager: 系统管理器
- FileCache: 文件缓存管理
"""

from .EmbeddingModel import EmbeddingModel
from .VectorStore import VectorStore
from .SystemManager import SystemManager, system
from .FileCache import FileCache

__all__ = ['EmbeddingModel', 'VectorStore', 'SystemManager', 'system', 'FileCache']
