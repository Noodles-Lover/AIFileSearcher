import os
import sys
from typing import Optional

# 添加項目根目錄到路徑，以便導入 backend 模塊
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(backend_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from .EmbeddingModel import EmbeddingModel
from .VectorStore import VectorStore

class SystemManager:
    _instance = None
    
    def __init__(self):
        self.embedding_model: Optional[EmbeddingModel] = None
        self.vector_store: Optional[VectorStore] = None
        self.is_initialized = False
        self.auto_loaded = False  # 标记是否已自动加载

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = SystemManager()
            # 启动时自动加载模型
            cls._instance.auto_load_model()
        return cls._instance

    def auto_load_model(self):
        """启动时自动加载模型"""
        if self.auto_loaded:
            return
        
        try:
            print("🚀 启动程序，自动加载embedding模型...")
            self.initialize()
            self.auto_loaded = True
            print("✅ 模型自动加载完成")
        except Exception as e:
            print(f"⚠️ 模型自动加载失败: {e}")
            print("💡 提示：将在首次使用时手动加载")

    def initialize(self, model_name: str = "bge-m3"):
        """初始化系統核心組件 (嵌入模型和向量數據庫)"""
        if self.is_initialized:
            print("🔧 系统已初始化，跳过重复初始化")
            return

        print(f"正在初始化系統核心組件... 模型: {model_name}")
        
        # 1. 初始化嵌入模型
        models_dir = os.path.join(project_root, "models")
        model_path = os.path.join(models_dir, model_name)
        
        if os.path.exists(model_path):
            if not self.embedding_model:  # 避免重复加载
                print("📥 加载embedding模型...")
                self.embedding_model = EmbeddingModel(model_name)
                print("✅ Embedding模型加载完成")
            else:
                print("🔧 Embedding模型已存在，跳过加载")
        else:
            if os.path.exists(models_dir):
                available_models = [d for d in os.listdir(models_dir) if os.path.isdir(os.path.join(models_dir, d))]
                if available_models:
                    print(f"指定模型 {model_name} 不存在，使用第一個可用模型: {available_models[0]}")
                    if not self.embedding_model:
                        print("📥 加载可用模型...")
                        self.embedding_model = EmbeddingModel(available_models[0])
                        print("✅ 可用模型加载完成")
                else:
                    print(f"未找到本地模型，將嘗試從 HuggingFace 下載: {model_name}")
                    if not self.embedding_model:
                        print("📥 从HuggingFace加载模型...")
                        self.embedding_model = EmbeddingModel(model_name)
                        print("✅ HuggingFace模型加载完成")
            else:
                if not self.embedding_model:
                    print("📥 创建默认模型...")
                    self.embedding_model = EmbeddingModel(model_name)
                    print("✅ 默认模型加载完成")

        # 2. 初始化向量數據庫
        # 尝试获取维度
        try:
            # 方法 1: 使用模型的方法
            if hasattr(self.embedding_model.model, 'get_sentence_embedding_dimension'):
                dimension = self.embedding_model.model.get_sentence_embedding_dimension()
                print(f"使用模型方法獲取維度: {dimension}")
            else:
                # 方法 2: 通过编码一个样本获取维度
                sample_vector = self.embedding_model.encode(["test"])[0]
                dimension = len(sample_vector)
                print(f"通过样本编码獲取維度: {dimension}")
        except Exception as e:
            print(f"获取维度失败，使用默认值: {e}")
            dimension = 1024  # 默认维度

        # 數據存儲在根目錄的 data 文件夾下
        data_dir = os.path.join(project_root, "data")
        os.makedirs(data_dir, exist_ok=True)
        
        index_path = os.path.join(data_dir, "faiss_index.bin")
        metadata_path = os.path.join(data_dir, "metadata.json")
        
        self.vector_store = VectorStore(
            dimension=dimension,
            index_path=index_path,
            metadata_path=metadata_path
        )
        
        self.is_initialized = True
        print("系統核心組件初始化完成")

    def get_embedding_model(self) -> EmbeddingModel:
        """获取嵌入模型，确保已加载"""
        if not self.is_initialized:
            print("🔄 系统未初始化，正在初始化...")
            self.initialize()
        
        if not self.embedding_model:
            print("⚠️ 嵌入模型未加载，尝试手动加载...")
            self.initialize()
        
        return self.embedding_model

    def get_vector_store(self) -> VectorStore:
        if not self.is_initialized:
            self.initialize()
        return self.vector_store

# 全局單例
system = SystemManager.get_instance()
