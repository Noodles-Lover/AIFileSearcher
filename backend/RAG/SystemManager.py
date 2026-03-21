import os
from typing import Optional
from backend.utils.path_utils import get_project_root, get_models_path, get_data_path

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
            print("Starting program, auto-loading embedding model...")
            self.initialize()
            self.auto_loaded = True
            print("Model auto-loading completed")
        except Exception as e:
            print(f"Model auto-loading failed: {e}")
            print("Note: Will manually load on first use")

    def initialize(self, model_name: str = "bge-m3"):
        """Initialize system core components (embedding model and vector database)"""
        if self.is_initialized:
            print("System already initialized, skipping...")
            return

        print(f"Initializing system core components... Model: {model_name}")
        
        # 1. Initialize embedding model
        models_dir = get_models_path()
        model_path = get_models_path(model_name)
        
        if os.path.exists(model_path):
            if not self.embedding_model:  # Avoid duplicate loading
                print("Loading embedding model...")
                self.embedding_model = EmbeddingModel(model_name)
                print("Embedding model loaded")
            else:
                print("Embedding model already exists, skipping")
        else:
            if os.path.exists(models_dir):
                available_models = [d for d in os.listdir(models_dir) if os.path.isdir(os.path.join(models_dir, d))]
                if available_models:
                    print(f"Specified model {model_name} not found, using first available: {available_models[0]}")
                    if not self.embedding_model:
                        print("Loading available model...")
                        self.embedding_model = EmbeddingModel(available_models[0])
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

        # 2. Initialize vector database
        # Try to get dimension
        try:
            # Method 1: Use model method
            if hasattr(self.embedding_model.model, 'get_sentence_embedding_dimension'):
                dimension = self.embedding_model.model.get_sentence_embedding_dimension()
                print(f"Got dimension using model method: {dimension}")
            else:
                # Method 2: Get dimension by encoding a sample
                sample_vector = self.embedding_model.encode(["test"])[0]
                dimension = len(sample_vector)
                print(f"Got dimension by sample encoding: {dimension}")
        except Exception as e:
            print(f"Failed to get dimension, using default: {e}")
            dimension = 1024  # Default dimension

        # Data stored in data folder under project root
        data_dir = os.path.dirname(get_data_path("dummy"))
        
        index_path = get_data_path("faiss_index.bin")
        metadata_path = get_data_path("metadata.json")
        
        self.vector_store = VectorStore(
            dimension=dimension,
            index_path=index_path,
            metadata_path=metadata_path
        )
        
        self.is_initialized = True
        print("System core components initialized")

    def get_embedding_model(self) -> EmbeddingModel:
        """Get embedding model, ensure loaded"""
        if not self.is_initialized:
            print("System not initialized, initializing...")
            self.initialize()
        
        if not self.embedding_model:
            print("Embedding model not loaded, trying manual load...")
            self.initialize()
        
        return self.embedding_model

    def get_vector_store(self) -> VectorStore:
        if not self.is_initialized:
            self.initialize()
        return self.vector_store

# Global singleton
system = SystemManager.get_instance()
