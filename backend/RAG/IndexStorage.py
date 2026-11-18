import json
import os

import faiss


class IndexStorage:
    """索引持久化唯一入口：faiss_index.bin + index_state.json

    保存时先替换 bin、最后替换 state，state 完整存在即代表这一代数据完整；
    加载时校验两者属于同一代，不一致直接报错而不是静默清空。
    state 记录 embedding_model，模型与索引不匹配时整库失效。
    """

    def __init__(self, index_path: str, state_path: str, embedding_model: str = ""):
        self.index_path = index_path
        self.state_path = state_path
        self.embedding_model = embedding_model

    def load(self) -> dict:
        """加载数据；全新库返回空数据；文件损坏或两代不一致时抛异常"""
        if not (os.path.exists(self.index_path) and os.path.exists(self.state_path)):
            print("索引文件不存在，将创建新的索引")
            return {"index": None, "chunks": {}, "next_id": 0, "files": {}, "index_type": None}

        with open(self.state_path, "r", encoding="utf-8") as f:
            state = json.load(f)

        # 索引由另一个嵌入模型建立时，向量处于不同语义空间，整库失效
        stored_model = state.get("embedding_model", "")
        if stored_model and self.embedding_model and stored_model != self.embedding_model:
            print(f"⚠️ 索引由嵌入模型 [{stored_model}] 建立，当前模型为 [{self.embedding_model}]，索引已失效")
            return {
                "index": None, "chunks": {}, "next_id": 0, "files": {}, "index_type": None,
                "model_mismatch": True,
            }

        index = faiss.read_index(self.index_path)
        chunks = {int(k): v for k, v in state["chunks"].items()}
        files = state.get("files", {})

        bin_ids = set(int(v) for v in faiss.vector_to_array(index.id_map))
        if bin_ids != set(chunks.keys()):
            raise ValueError("faiss_index.bin 与 index_state.json 不属于同一代数据，请重建索引")

        referenced_ids = set()
        for record in files.values():
            referenced_ids.update(record.get("vector_ids", []))
        if not referenced_ids <= set(chunks.keys()):
            raise ValueError("文件缓存引用了不存在的向量 ID，请重建索引")

        print(f"向量存儲已加載: {index.ntotal} 個向量，指數類型: {state.get('index_type', 'IndexFlatL2')}")
        return {
            "index": index,
            "chunks": chunks,
            "next_id": int(state["next_id"]),
            "files": files,
            "index_type": state.get("index_type"),
        }

    def save(self, store, cache) -> None:
        """原子保存：先写临时文件再替换；先替换 bin，最后替换 state（提交标记）"""
        state = {
            "index_type": store.index_type,
            "dimension": store.dimension,
            "embedding_model": self.embedding_model,
            "next_id": store.next_id,
            "chunks": store.metadata,
            "files": cache.export(),
        }

        tmp_bin = self.index_path + ".tmp"
        faiss.write_index(store.index, tmp_bin)
        os.replace(tmp_bin, self.index_path)

        tmp_state = self.state_path + ".tmp"
        with open(tmp_state, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        os.replace(tmp_state, self.state_path)
