import faiss
import numpy as np
import os
import json
from typing import List, Dict, Any


SUPPORTED_INDEX_TYPES = [
    "IndexFlatL2",
    "IndexFlatIP",
    "IndexIVFFlat",
    "IndexHNSWFlat",
    "IndexLSH",
]

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
    FAISS 向量存儲封裝
    """

    def __init__(
        self,
        dimension: int,
        index_path: str = "faiss_index.bin",
        metadata_path: str = "metadata.json",
        index_type: str = "IndexFlatL2",
    ):
        """
        初始化向量存儲
        :param dimension: 向量維度
        :param index_path: 索引保存路徑
        :param metadata_path: 元數據保存路徑
        :param index_type: 索引類型
        """
        self.dimension = dimension
        self.index_path = index_path
        self.metadata_path = metadata_path
        self.index_type = index_type
        self.metadata: Dict[int, Dict[str, Any]] = {}
        self.next_id = 0

        self.index = create_index_with_ids(index_type, dimension)
        self.load()

    def change_index_type(self, new_index_type: str) -> bool:
        """
        更改索引類型（會清除所有現有數據）

        :param new_index_type: 新的索引類型
        :return: 是否成功
        """
        if new_index_type == self.index_type:
            return True

        if new_index_type not in SUPPORTED_INDEX_TYPES:
            print(f"不支援的索引類型: {new_index_type}")
            return False

        print(f"更換索引類型: {self.index_type} -> {new_index_type}")
        print("警告：更換索引類型會清除所有現有數據！")

        self.index_type = new_index_type
        self._reset()
        print("索引已重建")
        return True

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
        self.save()
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
        self.save()
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

    def save(self):
        """保存索引、元数据和 ID 分配进度"""
        index_info = {
            "index_type": self.index_type,
            "dimension": self.dimension,
        }
        state = {
            "next_id": self.next_id,
            "chunks": self.metadata,
        }
        faiss.write_index(self.index, self.index_path)
        with open(self.metadata_path, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

        with open(self.index_path + ".info", 'w', encoding='utf-8') as f:
            json.dump(index_info, f, ensure_ascii=False, indent=2)

    def load(self):
        """加载索引与元数据；格式不兼容时以空索引重建"""
        info_path = self.index_path + ".info"

        if not (os.path.exists(self.index_path) and os.path.exists(self.metadata_path)):
            print("向量存儲文件不存在，將創建新的索引")
            return

        try:
            index = faiss.read_index(self.index_path)
            with open(self.metadata_path, 'r', encoding='utf-8') as f:
                state = json.load(f)

            # 裸索引或列表元数据以物理位置为身份，无法映射成稳定 ID
            if not isinstance(index, faiss.IndexIDMap2) or not isinstance(state, dict) or "chunks" not in state:
                raise ValueError("索引格式不兼容")

            self.index = index
            self.metadata = {int(k): v for k, v in state["chunks"].items()}
            self.next_id = int(state["next_id"])

            if os.path.exists(info_path):
                with open(info_path, 'r', encoding='utf-8') as f:
                    self.index_type = json.load(f).get("index_type", "IndexFlatL2")

            print(f"向量存儲已加載: {self.index.ntotal} 個向量，指數類型: {self.index_type}")
        except Exception as e:
            print(f"加載向量存儲時出錯: {e}")
            print("重建索引，請重新建立索引")
            self._reset()

    def _reset(self):
        self.index = create_index_with_ids(self.index_type, self.dimension)
        self.metadata = {}
        self.next_id = 0
        self.save()

    def clear(self):
        """清除所有索引和元数据"""
        self._reset()
        print("索引已清除")
