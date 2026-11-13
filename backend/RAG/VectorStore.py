import faiss
import numpy as np
from typing import List, Dict, Any, Optional


# IndexIDMap2 包装后仍无法原地删除的索引类型
IN_PLACE_DELETE_TYPES = {"IndexFlatL2", "IndexFlatIP", "IndexLSH"}


def create_index(index_type: str, dimension: int, nlist: int = 4, 
                 hnsw_m: int = None, hnsw_efConstruction: int = None,
                 lsh_nbits: int = None) -> faiss.Index:
    """
    根据索引类型创建 FAISS 索引

    :param index_type: 索引类型
    :param dimension: 向量维度
    :param nlist: IVF索引的聚类数量
    :param hnsw_m: HNSW 每层连接数（默认 32）
    :param hnsw_efConstruction: HNSW 构建时的搜索范围（默认 40）
    :param lsh_nbits: LSH 的位数（默认 dimension // 2）
    :return: FAISS 索引实例
    """
    if index_type == "IndexFlatL2":
        return faiss.IndexFlatL2(dimension)
    elif index_type == "IndexFlatIP":
        return faiss.IndexFlatIP(dimension)
    elif index_type == "IndexIVFFlat":
        quantizer = faiss.IndexFlatL2(dimension)
        return faiss.IndexIVFFlat(quantizer, dimension, nlist)
    elif index_type == "IndexHNSWFlat":
        m = hnsw_m if hnsw_m else 32
        return faiss.IndexHNSWFlat(dimension, m)
    elif index_type == "IndexLSH":
        nbits = lsh_nbits if lsh_nbits else max(32, dimension // 2)
        return faiss.IndexLSH(dimension, nbits)
    else:
        print(f"未知的索引类型 {index_type}，使用 IndexFlatL2")
        return faiss.IndexFlatL2(dimension)


def create_index_with_ids(index_type: str, dimension: int) -> faiss.IndexIDMap2:
    """创建带稳定外部 ID 的索引"""
    return faiss.IndexIDMap2(create_index(index_type, dimension))


class VectorStore:
    """
    FAISS 向量存儲封裝（内存态；持久化由 IndexStorage 统一负责）
    """

    def __init__(
        self,
        dimension: int,
        index_type: str,
        index: Optional[faiss.Index] = None,
        chunks: Optional[Dict[int, Dict[str, Any]]] = None,
        next_id: int = 0,
    ):
        self.dimension = dimension
        self.index_type = index_type
        self.metadata: Dict[int, Dict[str, Any]] = dict(chunks or {})
        self.next_id = next_id
        self.index = index if index is not None else create_index_with_ids(index_type, dimension)

    def add(
        self,
        vectors: List[List[float]],
        metas: List[Dict[str, Any]],
    ) -> List[int]:
        """添加向量并返回分配的稳定 ID"""
        if len(vectors) == 0:
            return []
        if len(vectors) != len(metas):
            raise ValueError("向量与元数据数量不一致")

        vectors_np = np.array(vectors).astype('float32')
        self._ensure_trained(vectors_np)

        ids = list(range(self.next_id, self.next_id + len(vectors_np)))
        self.index.add_with_ids(vectors_np, np.array(ids, dtype='int64'))
        for vector_id, meta in zip(ids, metas):
            self.metadata[vector_id] = meta

        self.next_id += len(vectors_np)
        return ids

    def _ensure_trained(self, vectors_np):
        base_index = faiss.downcast_index(self.index.index)
        if base_index.is_trained:
            return
        nlist = getattr(base_index, 'nlist', 4)
        if len(vectors_np) < nlist:
            base_index.nlist = 1
        base_index.train(vectors_np)

    def remove_by_ids(self, ids: List[int]) -> int:
        """按稳定 ID 删除向量，返回 FAISS 实际删除的数量"""
        if not ids or self.index.ntotal == 0:
            return 0

        if self.index_type not in IN_PLACE_DELETE_TYPES:
            raise NotImplementedError(
                f"{self.index_type} 不支持原地删除，请清空索引后重建"
            )

        removed = int(self.index.remove_ids(np.array(ids, dtype='int64')))
        for vector_id in set(int(i) for i in ids):
            self.metadata.pop(vector_id, None)
        return removed

    def search(self, query_vector: List[float], k: int = 5) -> List[Dict[str, Any]]:
        if self.index.ntotal == 0:
            return []

        query_dim = len(query_vector)
        if query_dim != self.index.d:
            print(f"向量维度不匹配: 查询向量维度: {query_dim}, 索引维度: {self.index.d}")
            raise ValueError(
                "向量维度不匹配。可能是使用了不同的嵌入模型创建索引。请重建索引后重试。"
            )
        try:
            query_np = np.array([query_vector]).astype('float32')
            
            D, I = self.index.search(query_np, k)

            results = []
            for i, idx in enumerate(I[0]):
                if idx < 0:
                    continue
                item = self.metadata.get(int(idx))
                if item is None:
                    continue
                item = item.copy()
                item['score'] = float(D[0][i])
                results.append(item)

            return results
        except Exception as e:
            import traceback

            error_type = type(e).__name__
            error_msg = str(e)

            sep = "=" * 60
            print(sep)
            print(f"[VectorStore.search 错误]")
            print(f"异常类型: {error_type}")
            print(f"异常消息: '{error_msg}'")
            print(f"查询向量维度: {query_dim}")
            print(f"索引维度: {self.index.d if self.index else 'N/A'}")
            print(f"索引向量数: {self.index.ntotal if self.index else 'N/A'}")
            print(f"堆栈跟踪:\n{traceback.format_exc()}")
            print(sep)

            if error_type in ("RuntimeError", "AssertionError") or "dimension" in error_msg.lower() or "size" in error_msg.lower():
                raise ValueError(
                    f"向量维度不匹配: 查询向量维度 {query_dim} 与索引维度 {self.index.d if self.index else 'N/A'} 不匹配。"
                    f"可能是使用了不同的嵌入模型创建索引。请重建索引后重试。"
                ) from e

            raise RuntimeError(f"搜索失败: {error_type} - {error_msg}") from e

