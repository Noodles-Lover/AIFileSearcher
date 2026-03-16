import faiss
import numpy as np
import os
import json
from typing import List, Dict, Any, Optional

class VectorStore:
    """
    FAISS 向量存儲封裝
    """
    def __init__(self, dimension: int, index_path: str = "faiss_index.bin", metadata_path: str = "metadata.json"):
        """
        初始化向量存儲
        :param dimension: 向量維度 (例如 BGE-M3 為 1024)
        :param index_path: 索引保存路徑
        :param metadata_path: 元數據保存路徑
        """
        self.dimension = dimension
        self.index_path = index_path
        self.metadata_path = metadata_path
        self.metadata: List[Dict[str, Any]] = []
        
        # 初始化 FAISS 索引 (使用最簡單的 L2 距離索引)
        # 注意: 實際生產中可能需要 IndexIVFFlat 等更高級的索引
        self.index = faiss.IndexFlatL2(dimension)
        
        # 嘗試加載現有索引
        self.load()

    def add(self, vectors: List[List[float]], metas: List[Dict[str, Any]], current_file: str = "") -> int:
        """
        添加向量和元數據到索引
        :param vectors: 向量列表
        :param metas: 元數據列表
        :param current_file: 當前處理的文件名
        :return: 添加的向量數量
        """
        if len(vectors) == 0:
            return 0

        # 轉換為 numpy float32 數組
        vectors_np = np.array(vectors).astype('float32')
        
        # 添加到 FAISS 索引
        self.index.add(vectors_np)
        
        # 保存元數據
        self.metadata.extend(metas)
        
        # 自動保存
        self.save(current_file, len(vectors))
        
        # 返回添加的向量數量
        return len(vectors)

    def search(self, query_vector: List[float], k: int = 5) -> List[Dict[str, Any]]:
        """
        搜索最近鄰
        :param query_vector: 查詢向量
        :param k: 返回結果數量
        :return: 包含元數據和距離的結果列表
        """
        if self.index.ntotal == 0:
            return []
            
        try:
            # 轉換查詢向量
            query_np = np.array([query_vector]).astype('float32')
            
            # 執行搜索
            # D: 距離 (L2距離，越小越相似)
            # I: 索引 ID
            D, I = self.index.search(query_np, k)
            
            results = []
            for i, idx in enumerate(I[0]):
                if idx != -1 and idx < len(self.metadata):
                    item = self.metadata[idx].copy()
                    item['score'] = float(D[0][i]) # L2 距離
                    results.append(item)
                    
            return results
        except Exception as e:
            print(f"搜索過程中出現錯誤: {e}")
            # 嘗試重建索引
            self.index = faiss.IndexFlatL2(self.dimension)
            self.metadata = []
            self.save()
            return []

    def save(self, current_file: str = None, current_vectors: int = None):
        """保存索引和元數據到磁盤"""
        faiss.write_index(self.index, self.index_path)
        with open(self.metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)
        
        if current_file and current_vectors is not None:
            print(f"向量存儲已更新: {self.index.ntotal} 個向量已保存 (當前文件: {current_file}, 新增: {current_vectors} 個向量)")
        elif current_file:
            print(f"向量存儲已更新: {self.index.ntotal} 個向量已保存 (當前文件: {current_file})")
        else:
            print(f"向量存儲已更新: {self.index.ntotal} 個向量已保存")

    def load(self):
        """從磁盤加載索引和元數據"""
        if os.path.exists(self.index_path) and os.path.exists(self.metadata_path):
            try:
                self.index = faiss.read_index(self.index_path)
                with open(self.metadata_path, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
                print(f"向量存儲已加載: {self.index.ntotal} 個向量")
            except Exception as e:
                print(f"加載向量存儲時出錯: {e}")
                # 如果加載失敗，重建索引
                print("重建索引...")
                self.index = faiss.IndexFlatL2(self.dimension)
                self.metadata = []
                self.save()  # 重建时不显示当前文件
        else:
            print("向量存儲文件不存在，將創建新的索引")
            # 确保索引已初始化
            if self.index is None:
                self.index = faiss.IndexFlatL2(self.dimension)
