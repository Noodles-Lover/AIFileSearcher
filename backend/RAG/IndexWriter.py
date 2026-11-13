from typing import Any, Dict, Iterable, List

from backend.RAG.FileCache import FileCache
from backend.RAG.VectorStore import VectorStore


class IndexWriter:
    """向量索引与文件缓存的统一写入口"""

    def __init__(self, store: VectorStore, cache: FileCache):
        self.store = store
        self.cache = cache

    def write_file(
        self,
        file_path: str,
        vectors: List[List[float]],
        metas: List[Dict[str, Any]],
    ) -> List[int]:
        """替换一个文件的全部向量：先删旧，再写新，并更新缓存"""
        self.store.remove_by_ids(self.cache.get_vector_ids(file_path))
        vector_ids = self.store.add(vectors, metas)
        self.cache.update_file_cache(file_path, vector_ids)
        return vector_ids

    def remove_files(self, file_paths: Iterable[str]) -> int:
        """删除一组文件的向量与缓存记录，返回实际删除的向量数"""
        file_paths = list(file_paths)

        ids_to_remove = set()
        for file_path in file_paths:
            ids_to_remove.update(self.cache.get_vector_ids(file_path))

        removed = 0
        if ids_to_remove:
            removed = self.store.remove_by_ids(list(ids_to_remove))

        for file_path in file_paths:
            self.cache.remove_file_cache(file_path)
        return removed
