import os
from typing import Optional

from backend.utils.path_utils import get_embedding_models_path, get_data_path
from backend.utils.settings_manager import settings_manager

from .EmbeddingModel import EmbeddingModel
from .LocalLLM import LocalLLM
from .VectorStore import VectorStore


class SystemManager:
    _instance = None

    def __init__(self):
        self.embedding_model: Optional[EmbeddingModel] = None
        self.vector_store: Optional[VectorStore] = None
        self.local_llm: Optional[LocalLLM] = None
        self.is_initialized = False
        self.auto_loaded = False
        self.current_model_name: Optional[str] = None
        self.current_llm_name: Optional[str] = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = SystemManager()
            cls._instance.auto_load_model()
        return cls._instance

    def auto_load_model(self):
        if self.auto_loaded:
            return

        try:
            print("Starting program, auto-loading embedding model...")
            self.initialize()
            self.auto_loaded = True
            print("Model auto-loading completed")
        except Exception as e:
            print(f"Model auto-loading failed: {e}")
            print("Note: Will manually load on first use")

    def initialize(self, model_name: str | None = None):
        """Initialize system core components (embedding model and vector database)."""
        if model_name is None:
            model_name = settings_manager.load().get("embedding_model", "bge-m3")

        if self.is_initialized:
            print("System already initialized, skipping...")
            return

        print(f"Initializing system core components... Model: {model_name}")

        models_dir = get_embedding_models_path()
        model_path = get_embedding_models_path(model_name)

        if os.path.exists(model_path):
            if not self.embedding_model:
                print("Loading embedding model...")
                self.embedding_model = EmbeddingModel(model_name)
                print("Embedding model loaded")
        else:
            if os.path.exists(models_dir):
                available_models = [d for d in os.listdir(models_dir) if os.path.isdir(os.path.join(models_dir, d))]
                if available_models:
                    fallback_model = available_models[0]
                    print(f"Specified model {model_name} not found, using first available: {fallback_model}")
                    if not self.embedding_model:
                        print("Loading available model...")
                        self.embedding_model = EmbeddingModel(fallback_model)
                        model_name = fallback_model
                        print("Available model loaded")
                else:
                    print(f"No local models found, will try to download from HuggingFace: {model_name}")
                    if not self.embedding_model:
                        print("Loading from HuggingFace...")
                        self.embedding_model = EmbeddingModel(model_name)
                        print("HuggingFace model loaded")
            else:
                if not self.embedding_model:
                    print("Creating default model...")
                    self.embedding_model = EmbeddingModel(model_name)
                    print("Default model loaded")

        self.current_model_name = model_name

        try:
            if hasattr(self.embedding_model.model, "get_sentence_embedding_dimension"):
                dimension = self.embedding_model.model.get_sentence_embedding_dimension()
                print(f"Got dimension using model method: {dimension}")
            else:
                sample_vector = self.embedding_model.encode(["test"])[0]
                dimension = len(sample_vector)
                print(f"Got dimension by sample encoding: {dimension}")
        except Exception as e:
            print(f"Failed to get dimension, using default: {e}")
            dimension = 1024

        index_path = get_data_path("faiss_index.bin")
        metadata_path = get_data_path("metadata.json")
        index_type = settings_manager.load().get("index_type", "IndexFlatL2")

        self.vector_store = VectorStore(
            dimension=dimension,
            index_path=index_path,
            metadata_path=metadata_path,
            index_type=index_type,
        )

        self.is_initialized = True
        print("System core components initialized")

    def reload_embedding_system(self, model_name: str | None = None):
        if model_name is None:
            model_name = settings_manager.load().get("embedding_model", "bge-m3")

        print(f"Reloading embedding system with model: {model_name}")
        self.embedding_model = None
        self.vector_store = None
        self.is_initialized = False
        self.current_model_name = None
        self.initialize(model_name=model_name)

    def ensure_embedding_model(self, model_name: str | None = None):
        if model_name is None:
            model_name = settings_manager.load().get("embedding_model", "bge-m3")

        if not self.is_initialized or not self.embedding_model:
            self.initialize(model_name=model_name)
            return

        if self.current_model_name != model_name:
            self.reload_embedding_system(model_name=model_name)

    def get_embedding_model(self) -> EmbeddingModel:
        self.ensure_embedding_model()

        if not self.is_initialized:
            print("System not initialized, initializing...")
            self.initialize()

        if not self.embedding_model:
            print("Embedding model not loaded, trying manual load...")
            self.initialize()

        return self.embedding_model

    def get_vector_store(self) -> VectorStore:
        self.ensure_embedding_model()

        if not self.is_initialized:
            self.initialize()
        return self.vector_store

    def load_local_llm(self, model_name: str | None = None, device: str | None = None) -> LocalLLM:
        if model_name is None:
            model_name = settings_manager.load().get("llm_model", "")

        if not model_name:
            raise ValueError("No LLM model configured")

        if self.local_llm and self.current_llm_name == model_name:
            return self.local_llm

        self.local_llm = LocalLLM(model_name=model_name, device=device)
        self.current_llm_name = model_name
        return self.local_llm

    def unload_local_llm(self):
        if self.local_llm is not None:
            self.local_llm = None
            self.current_llm_name = None

    def generate_with_llm(
        self,
        prompt: str,
        system_prompt: str = "",
        model_name: str | None = None,
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        device: str | None = None,
    ) -> str:
        llm = self.load_local_llm(model_name=model_name, device=device)
        return llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
        )


system = SystemManager.get_instance()
