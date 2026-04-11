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
        
        # 自動保存（静默）
        self.save(current_file, len(vectors))
        
        # 返回添加的向量數量
        return len(vectors)

    def remove_vectors_by_indices(self, indices: List[int]):
        """
        根据索引列表删除向量
        :param indices: 要删除的向量索引列表
        """
        if not indices or self.index.ntotal == 0:
            return
        
        try:
            # 过滤掉要删除的向量
            indices_to_keep = [i for i in range(self.index.ntotal) if i not in indices]
            
            if indices_to_keep:
                # 重建索引，只保留要保留的向量
                vectors_to_keep = self.index.reconstruct_batch(indices_to_keep)
                metadata_to_keep = [self.metadata[i] for i in indices_to_keep]
                
                # 重新创建FAISS索引
                import faiss
                self.index = faiss.IndexFlatL2(self.dimension)
                self.index.add(vectors_to_keep)
                
                # 更新元数据
                self.metadata = metadata_to_keep
                
                # 保存更新后的索引
                self.save()
                
                # 返回删除的向量数量，由调用方输出
                return len(indices)
            else:
                # 如果没有要保留的向量，创建空索引
                import faiss
                self.index = faiss.IndexFlatL2(self.dimension)
                self.metadata = []
                self.save()
                
                # 返回删除的向量数量，由调用方输出
                return len(indices)
                
        except Exception as e:
            print(f"⚠️ 删除向量失败: {e}")

    def remove_vectors_by_file(self, file_path: str) -> int:
        """
        根据文件路径删除所有相关向量
        :param file_path: 文件路径
        :return: 删除的向量数量
        """
        indices_to_remove = []
        
        # 找出所有属于该文件的向量索引
        for i, meta in enumerate(self.metadata):
            if meta.get('file_path') == file_path:
                indices_to_remove.append(i)
        
        if indices_to_remove:
            self.remove_vectors_by_indices(indices_to_remove)
            
        return len(indices_to_remove)

    def search(self, query_vector: List[float], k: int = 5) -> List[Dict[str, Any]]:
        if self.index.ntotal == 0:
            return []

        query_dim = len(query_vector)
        if query_dim != self.index.d:
            print(f"向量维度不匹配: 查询向量维度: {query_dim}, 索引维度: {self.index.d}")
            raise ValueError("向量维度不匹配。可能是使用了不同的嵌入模型创建索引。请重建索引后重试。")
        try:
            query_np = np.array([query_vector]).astype('float32')

            D, I = self.index.search(query_np, k)

            results = []
            for i, idx in enumerate(I[0]):
                if idx != -1 and idx < len(self.metadata):
                    item = self.metadata[idx].copy()
                    item['score'] = float(D[0][i])
                    results.append(item)

            return results
        except Exception as e:

            if error_type in ("RuntimeError", "AssertionError") or "dimension" in error_msg.lower() or "size" in error_msg.lower():
                raise ValueError(
                    f"向量维度不匹配: 查询向量维度 {query_dim} 与索引维度 {self.index.d if self.index else 'N/A'} 不匹配。"
                    f"可能是使用了不同的嵌入模型创建索引。请重建索引后重试。"
                ) from e

            raise RuntimeError(f"搜索失败: {error_type} - {error_msg}") from e

    def save(self, current_file: str = None, current_vectors: int = None):
        """保存索引和元數據到磁盤"""
        faiss.write_index(self.index, self.index_path)
        with open(self.metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)
        
        # 静默保存，不输出信息

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
