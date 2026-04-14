import os
from typing import Optional

from backend.utils.path_utils import get_embedding_models_path, get_data_path
from backend.utils.settings_manager import settings_manager

from .EmbeddingModel import EmbeddingModel
from .LocalLLM import LocalLLM
from .VectorStore import VectorStore


class SystemManager:
    """
    系统管理器 - 负责加载和管理 EmbeddingModel、LocalLLM、VectorStore 实例
    """
    _instance = None

    def __init__(self):
        self.embedding_model: Optional[EmbeddingModel] = None
        self.vector_store: Optional[VectorStore] = None
        self.local_llm: Optional[LocalLLM] = None
        self.current_embedding_model_name: Optional[str] = None
        self.current_llm_name: Optional[str] = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = SystemManager()
            cls._instance._auto_load()
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """重置单例实例，用于清空所有加载的组件"""
        if cls._instance is not None:
            if cls._instance.vector_store:
                cls._instance.vector_store.index = None
                cls._instance.vector_store.metadata = []
            cls._instance.embedding_model = None
            cls._instance.vector_store = None
            cls._instance.local_llm = None
            cls._instance.current_embedding_model_name = None
            cls._instance.current_llm_name = None
            cls._instance = None

    def _auto_load(self):
        try:
            print("🚀 程序启动，自动加载模型...")
            self.load_embedding_model()
            self.load_llm()
            print("✅ 模型加载完成")
        except Exception as e:
            print(f"❌ 模型加载失败: {e}")

    def load_embedding_model(self, model_name: str | None = None, force: bool = False):
        if model_name is None:
            model_name = settings_manager.load().get("embedding_model", "bge-m3")

        if not force and self.embedding_model and self.current_embedding_model_name == model_name:
            return self.embedding_model

        print(f"📊 加载嵌入模型: {model_name}...")
        self.embedding_model = EmbeddingModel(model_name)
        self.current_embedding_model_name = model_name
        print(f"✅ 嵌入模型 [{model_name}] 加载成功")
        return self.embedding_model

    def reload_embedding_model(self, model_name: str | None = None):
        """强制重新加载嵌入模型"""
        return self.load_embedding_model(model_name=model_name, force=True)

    def get_embedding_model(self) -> EmbeddingModel:
        if not self.embedding_model:
            self.load_embedding_model()
        return self.embedding_model

    def init_vector_store(self, dimension: int | None = None):
        if dimension is None:
            sample_vector = self.get_embedding_model().encode(["test"])[0]
            dimension = len(sample_vector)

        index_path = get_data_path("faiss_index.bin")
        metadata_path = get_data_path("metadata.json")
        index_type = settings_manager.load().get("index_type", "IndexFlatL2")

        self.vector_store = VectorStore(
            dimension=dimension,
            index_path=index_path,
            metadata_path=metadata_path,
            index_type=index_type,
        )
        return self.vector_store

    def get_vector_store(self) -> VectorStore:
        if not self.vector_store:
            self.init_vector_store()
        return self.vector_store

    def load_llm(self, model_name: str | None = None, force: bool = False):
        if model_name is None:
            model_name = settings_manager.load().get("llm_model", "")

        if not model_name:
            print("⚠️ 未配置 LLM 模型")
            return None

        if not force and self.local_llm and self.current_llm_name == model_name:
            return self.local_llm

        print(f"🤖 加载 LLM 模型: {model_name}...")
        self.local_llm = LocalLLM(model_name=model_name)
        self.current_llm_name = model_name
        print(f"✅ LLM 模型 [{model_name}] 加载成功")
        return self.local_llm

    def reload_llm(self, model_name: str | None = None):
        """强制重新加载 LLM"""
        return self.load_llm(model_name=model_name, force=True)

    def unload_llm(self):
        self.local_llm = None
        self.current_llm_name = None

    def get_llm(self) -> Optional[LocalLLM]:
        if not self.local_llm:
            self.load_llm()
        return self.local_llm

    def generate_with_llm(self, prompt: str, system_prompt: str = "") -> str:
        llm = self.get_llm()
        if not llm:
            raise ValueError("LLM 未加载")
        return llm.generate(prompt=prompt, system_prompt=system_prompt)
