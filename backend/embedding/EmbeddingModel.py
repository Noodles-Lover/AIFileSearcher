import os
import sys
import numpy as np
from typing import List, Union
from sentence_transformers import SentenceTransformer

class EmbeddingModel:
    """
    嵌入模型类，用于文本向量化
    """
    def __init__(self, model_name: str = "bge-m3", device: str = "cpu"):
        """
        初始化嵌入模型
        :param model_name: 模型名称或路径
        :param device: 运行设备 (cpu/cuda)
        """
        # 获取当前文件所在目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 获取项目根目录 (backend 的上一级)
        project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
        # 构建本地模型路径
        local_model_path = os.path.join(project_root, "models", model_name)
        
        print(f"检查本地模型路径: {local_model_path}")
        
        if os.path.exists(local_model_path):
            model_path = local_model_path
            print(f"加载本地模型: {model_path}")
        else:
            model_path = model_name
            print(f"加载远程模型: {model_name}")
        
        self.model = SentenceTransformer(model_path, device=device)
        self.device = device
    
    def encode(self, texts: Union[str, List[str]]) -> List[List[float]]:
        """
        将文本转换为向量
        :param texts: 单个字符串或字符串列表
        :return: 向量列表
        """
        result = self.model.encode(texts, convert_to_numpy=True)
        # 确保返回的是列表的列表
        if isinstance(result, np.ndarray):
            if result.ndim == 1:
                # 单个字符串输入，返回包含单个向量的列表
                return [result.tolist()]
            else:
                # 字符串列表输入，返回向量列表
                return result.tolist()
        return []

if __name__ == "__main__":
    # 测试代码
    try:
        embedder = EmbeddingModel("bge-m3")
        vectors = embedder.encode(["你好", "世界"])
        print(f"Vector dimension: {len(vectors[0])}")
        print(f"Vectors: {vectors}")
    except Exception as e:
        print(f"Error: {e}")
