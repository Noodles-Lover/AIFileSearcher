import os
import torch
import numpy as np
from typing import Any, List, Union
from sentence_transformers import SentenceTransformer
from backend.utils.path_utils import get_embedding_models_path

class EmbeddingModel:
    """
    Embedding model class for text vectorization
    Supports automatic GPU detection for acceleration.
    """
    def __init__(self, model_name: str = "bge-m3", device: str = None):
        """
        Initialize embedding model
        :param model_name: Model name or path
        :param device: Running device (cpu/cuda). If None, auto-detect GPU.
        """
        # Auto-detect GPU if device not specified
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        
        self.device = device
        
        # Build local model path
        local_model_path = get_embedding_models_path(model_name)
        
        print(f"Checking local model path: {local_model_path}")
        print(f"Embedding model using device: {device}")
        
        if os.path.exists(local_model_path):
            model_path = local_model_path
            print(f"Loading local model: {model_path}")
        else:
            model_path = model_name
            print(f"Loading remote model: {model_path}")
        
        self.model = SentenceTransformer(model_path, device=device)
    
    def encode(self, texts: Union[str, List[str]]) -> List[List[float]]:
        """
        Convert text to vectors
        :param texts: Single string or string list
        :return: Vector list
        """
        result = self.model.encode(texts, convert_to_numpy=True)
        # Ensure returning list of lists
        if isinstance(result, np.ndarray):
            if result.ndim == 1:
                # Single string input, return list containing single vector
                return [result.tolist()]
            else:
                # String list input, return vector list
                return result.tolist()
        return []

    def encode_images(self, images: Union[Any, List[Any]]) -> List[List[float]]:
        """
        Convert image inputs to vectors.
        This only works when the underlying model supports multimodal/image
        inputs, such as CLIP-style sentence-transformers models.
        """
        image_list = images if isinstance(images, list) else [images]

        try:
            result = self.model.encode(image_list, convert_to_numpy=True)
        except Exception as exc:
            raise ValueError(
                "Current embedding model does not support image encoding. "
                "Please use a multimodal model before indexing images."
            ) from exc

        if isinstance(result, np.ndarray):
            if result.ndim == 1:
                return [result.tolist()]
            return result.tolist()
        return []

if __name__ == "__main__":
    # Test code
    try:
        embedder = EmbeddingModel("bge-m3")
        vectors = embedder.encode(["hello", "world"])
        print(f"Vector dimension: {len(vectors[0])}")
        print(f"Vectors: {vectors}")
    except Exception as e:
        print(f"Error: {e}")
