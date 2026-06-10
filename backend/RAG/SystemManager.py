import os
from typing import Optional, Union

from backend.utils.path_utils import get_embedding_models_path, get_llm_models_path, get_data_path
from backend.utils.settings_manager import settings_manager

from .EmbeddingModel import EmbeddingModel
from .LocalLLM import LocalLLM
from .DeepSeekLLM import DeepSeekLLM
from .VectorStore import VectorStore

# LLM 类型别名
LLMType = Union[LocalLLM, DeepSeekLLM]


class SystemManager:
    """
    系统管理器 - 负责加载和管理 EmbeddingModel、LLM、VectorStore 实例
    支持本地模型和 DeepSeek API
    """
    _instance = None

    def __init__(self):
        self.embedding_model: Optional[EmbeddingModel] = None
        self.vector_store: Optional[VectorStore] = None
        self.llm: Optional[LLMType] = None  # 统一 LLM 实例（本地或 DeepSeek）
        self.current_embedding_model_name: Optional[str] = None
        self.current_llm_provider: Optional[str] = None
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
            cls._instance.llm = None
            cls._instance.current_embedding_model_name = None
            cls._instance.current_llm_provider = None
            cls._instance.current_llm_name = None
            cls._instance = None

    def _auto_load(self):
        try:
            print("🚀 程序启动，检查模型状态...")

            # 检查嵌入模型是否存在
            settings = settings_manager.load()
            embedding_model_name = settings.get("embedding_model", "bge-m3")
            embedding_model_path = get_embedding_models_path(embedding_model_name)

            if os.path.exists(embedding_model_path):
                print(f"📊 发现本地嵌入模型: {embedding_model_name}")
                self.load_embedding_model()
            else:
                print(f"⚠️ 未找到嵌入模型: {embedding_model_name}")
                print(f"   模型路径: {embedding_model_path}")
                print(f"   请通过设置页面下载模型")

            # 不自动加载 LLM（避免启动慢）
            print("✅ 启动检查完成（LLM 将在首次使用时加载）")
        except Exception as e:
            print(f"❌ 启动检查失败: {e}")

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
        """
        加载 LLM 模型（本地或 DeepSeek API）
        """
        settings = settings_manager.load()
        llm_provider = settings.get("llm_provider", "local")

        # 如果指定了 model_name，说明是本地模型
        if model_name:
            llm_provider = "local"

        if llm_provider == "deepseek":
            api_key = settings.get("deepseek_api_key", "")
            if not api_key:
                print("⚠️ 未配置 DeepSeek API Key")
                return None

            if not force and isinstance(self.llm, DeepSeekLLM):
                return self.llm

            print(f"🤖 初始化 DeepSeek API...")
            self.llm = DeepSeekLLM(api_key=api_key)
            self.current_llm_provider = "deepseek"
            self.current_llm_name = "deepseek-chat"
            print(f"✅ DeepSeek API 初始化成功")
            return self.llm

        else:  # local
            if model_name is None:
                model_name = settings.get("llm_model", "")

            if not model_name:
                print("⚠️ 未配置本地 LLM 模型")
                return None

            if not force and isinstance(self.llm, LocalLLM) and self.current_llm_name == model_name:
                return self.llm

            print(f"🤖 加载本地 LLM 模型: {model_name}...")
            self.llm = LocalLLM(model_name=model_name)
            self.current_llm_provider = "local"
            self.current_llm_name = model_name
            print(f"✅ 本地 LLM 模型 [{model_name}] 加载成功")
            return self.llm

    def reload_llm(self, model_name: str | None = None):
        """强制重新加载 LLM"""
        return self.load_llm(model_name=model_name, force=True)

    def unload_llm(self):
        """卸载 LLM"""
        self.llm = None
        self.current_llm_provider = None
        self.current_llm_name = None

    def get_llm(self) -> Optional[LLMType]:
        if not self.llm:
            self.load_llm()
        return self.llm

    @property
    def is_deepseek(self) -> bool:
        """检查当前 LLM 是否为 DeepSeek"""
        return isinstance(self.llm, DeepSeekLLM)

    def generate_with_llm(self, prompt: str, system_prompt: str = "") -> str:
        llm = self.get_llm()
        if not llm:
            raise ValueError("LLM 未加载")
        return llm.generate(prompt=prompt, system_prompt=system_prompt)
