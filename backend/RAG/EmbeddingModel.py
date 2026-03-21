import os
import numpy as np
from typing import List, Union
from sentence_transformers import SentenceTransformer
from backend.utils.path_utils import get_project_root, get_models_path

class EmbeddingModel:
    """
    Embedding model class for text vectorization
    """
    def __init__(self, model_name: str = "bge-m3", device: str = "cpu"):
        """
        Initialize embedding model
        :param model_name: Model name or path
        :param device: Running device (cpu/cuda)
        """
        # Build local model path
        local_model_path = get_models_path(model_name)
        
        print(f"Checking local model path: {local_model_path}")
        
        if os.path.exists(local_model_path):
            model_path = local_model_path
            print(f"Loading local model: {model_path}")
        else:
            model_path = model_name
            print(f"Loading remote model: {model_path}")
        
        self.model = SentenceTransformer(model_path, device=device)
        self.device = device
    
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

if __name__ == "__main__":
    # Test code
    try:
        embedder = EmbeddingModel("bge-m3")
        vectors = embedder.encode(["hello", "world"])
        print(f"Vector dimension: {len(vectors[0])}")
        print(f"Vectors: {vectors}")
    except Exception as e:
        print(f"Error: {e}")
