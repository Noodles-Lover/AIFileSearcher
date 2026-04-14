"""
调试维度问题
"""
import os
import sys
import io
import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))
sys.path.insert(0, project_root)

from backend.utils.path_utils import ensure_project_path, get_data_path
ensure_project_path()

from backend.RAG.SystemManager import SystemManager

print("=" * 50)
print("Debug Dimension")
print("=" * 50)

sm = SystemManager.get_instance()
embedder = sm.get_embedding_model()
store = sm.get_vector_store()

print(f"Store dimension: {store.dimension}")
print(f"Store index.ntotal: {store.index.ntotal}")
print(f"Index type: {type(store.index).__name__}")

# 测试向量
vec = embedder.encode(["hello"])
print(f"\nEncoded vector type: {type(vec)}")
print(f"Encoded vector length: {len(vec)}")
if vec:
    print(f"First element type: {type(vec[0])}")
    print(f"First element length: {len(vec[0])}")
