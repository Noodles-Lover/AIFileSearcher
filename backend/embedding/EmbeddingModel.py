import os
from typing import List, Union
from sentence_transformers import SentenceTransformer

class EmbeddingModel:
    """
    通用嵌入模型加載器
    支持加載根目錄 models/ 下的本地模型
    """
    def __init__(self, model_name: str, device: str = "cpu"):
        """
        初始化嵌入模型
        :param model_name: 模型名稱 (文件夾名) 或 HuggingFace ID
        :param device: 運行設備 ('cpu', 'cuda', 'mps')
        """
        self.model_name = model_name
        self.device = device
        self.model = self._load_model()

    def _load_model(self) -> SentenceTransformer:
        """
        加載模型，優先查找本地 models/ 目錄
        """
        # 1. 構建本地模型路徑
        # 假設當前文件在 backend/embedding/EmbeddingModel.py
        # 項目根目錄在 ../../
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, "../../"))
        local_model_path = os.path.join(project_root, "models", self.model_name)

        if os.path.exists(local_model_path):
            print(f"Loading local embedding model from: {local_model_path}")
            return SentenceTransformer(local_model_path, device=self.device)
        
        # 2. 如果本地不存在，嘗試從 HuggingFace 加載 (或者報錯，取決於需求)
        # 這裡我們允許回退到在線加載，但通常用戶會希望使用本地模型
        print(f"Local model not found at {local_model_path}, trying to load from HuggingFace Hub: {self.model_name}")
        return SentenceTransformer(self.model_name, device=self.device)

    def encode(self, texts: Union[str, List[str]]) -> List[List[float]]:
        """
        將文本轉換為向量
        :param texts: 單個字符串或字符串列表
        :return: 向量列表
        """
        if isinstance(texts, str):
            texts = [texts]
            
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        
        # 轉換為 Python list
        return embeddings.tolist()

if __name__ == "__main__":
    # 測試代碼
    try:
        # 假設 models/ 下有一個名為 'test-model' 的文件夾 (實際使用時請替換為真實模型)
        # 這裡我們用一個不存在的模型名來觸發在線加載測試，或者你可以手動放入一個模型
        embedder = EmbeddingModel("all-MiniLM-L6-v2") 
        vectors = embedder.encode(["你好", "世界"])
        print(f"Vector dimension: {len(vectors[0])}")
        print(f"Vectors: {vectors}")
    except Exception as e:
        print(f"Error: {e}")
