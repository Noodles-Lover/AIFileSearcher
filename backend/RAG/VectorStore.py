import faiss
import numpy as np
import os
import json
from typing import List, Dict, Any, Optional


SUPPORTED_INDEX_TYPES = [
    "IndexFlatL2",
    "IndexFlatIP",
    "IndexIVFFlat",
    "IndexHNSWFlat",
]


def create_index(index_type: str, dimension: int, nlist: int = 4) -> faiss.Index:
    """
    根据索引类型创建 FAISS 索引

    :param index_type: 索引类型
    :param dimension: 向量维度
    :param nlist: IVF索引的聚类数量
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
        return faiss.IndexHNSWFlat(dimension, 32)
    else:
        print(f"未知的索引类型 {index_type}，使用 IndexFlatL2")
        return faiss.IndexFlatL2(dimension)


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
        self.metadata: List[Dict[str, Any]] = []

        self.index = create_index(index_type, dimension)
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
        self.index = create_index(new_index_type, self.dimension)
        self.metadata = []

        self.save()
        print("索引已重建")
        return True

    def add(
        self,
        vectors: List[List[float]],
        metas: List[Dict[str, Any]],
        current_file: str = "",
    ) -> int:
        """
        添加向量和元數據到索引
        """
        if len(vectors) == 0:
            return 0

        vectors_np = np.array(vectors).astype('float32')

        if hasattr(self.index, 'is_trained') and not self.index.is_trained:
            self.index.train(vectors_np)

        self.index.add(vectors_np)
        self.metadata.extend(metas)
        self.save(current_file, len(vectors))

        return len(vectors)

    def remove_vectors_by_indices(self, indices: List[int]):
        """
        根据索引列表删除向量
        """
        if not indices or self.index.ntotal == 0:
            return

        try:
            indices_to_keep = [i for i in range(self.index.ntotal) if i not in set(indices)]

            if indices_to_keep:
                vectors_to_keep = self.index.reconstruct_batch(indices_to_keep)
                metadata_to_keep = [self.metadata[i] for i in indices_to_keep]

                self.index = create_index(self.index_type, self.dimension)
                if hasattr(self.index, 'is_trained') and not self.index.is_trained:
                    self.index.train(vectors_to_keep)
                self.index.add(vectors_to_keep)

                self.metadata = metadata_to_keep
            else:
                self.index = create_index(self.index_type, self.dimension)
                self.metadata = []

            self.save()
            return len(indices)
        except Exception as e:
            print(f"⚠️ 删除向量失败: {e}")

    def remove_vectors_by_file(self, file_path: str) -> int:
        """
        根据文件路径删除所有相关向量
        """
        indices_to_remove = []

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
            raise ValueError(
                "向量维度不匹配。可能是使用了不同的嵌入模型创建索引。请重建索引后重试。"
            )
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

    def save(self, current_file: str = None, current_vectors: int = None):
        """保存索引和元數據到磁盤"""
        index_info = {
            "index_type": self.index_type,
            "dimension": self.dimension,
        }
        faiss.write_index(self.index, self.index_path)
        with open(self.metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)

        with open(self.index_path + ".info", 'w', encoding='utf-8') as f:
            json.dump(index_info, f, ensure_ascii=False, indent=2)

    def load(self):
        """從磁盤加載索引和元數據"""
        info_path = self.index_path + ".info"

        if os.path.exists(self.index_path) and os.path.exists(self.metadata_path):
            try:
                self.index = faiss.read_index(self.index_path)

                if os.path.exists(info_path):
                    with open(info_path, 'r', encoding='utf-8') as f:
                        info = json.load(f)
                    self.index_type = info.get("index_type", "IndexFlatL2")

                with open(self.metadata_path, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
                print(f"向量存儲已加載: {self.index.ntotal} 個向量，指數類型: {self.index_type}")
            except Exception as e:
                print(f"加載向量存儲時出錯: {e}")
                print("重建索引...")
                self.index = create_index(self.index_type, self.dimension)
                self.metadata = []
                self.save()
        else:
            print("向量存儲文件不存在，將創建新的索引")
            if self.index is None:
                self.index = create_index(self.index_type, self.dimension)

    def clear(self):
        """清除所有索引和元数据"""
        self.index = create_index(self.index_type, self.dimension)
        self.metadata = []
        self.save()
        print("索引已清除")
