"""
调试脚本 - 检查 store 状态
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
print("Debug Store")
print("=" * 50)

# 检查文件
data_path = get_data_path("")
print(f"\nData path: {data_path}")
for f in os.listdir(data_path):
    fp = os.path.join(data_path, f)
    print(f"  {f}: {os.path.getsize(fp)} bytes")

# 重置
SystemManager.reset_instance()

# 获取
sm = SystemManager.get_instance()
store = sm.get_vector_store()

print(f"\nStore state:")
print(f"  dimension: {store.dimension}")
print(f"  index type: {type(store.index).__name__}")
print(f"  index.ntotal: {store.index.ntotal}")
print(f"  metadata len: {len(store.metadata)}")

# 测试向量
embedder = sm.get_embedding_model()
vec = embedder.encode(["hello"])[0]
print(f"\nEncoded vector:")
print(f"  type: {type(vec)}")
print(f"  length: {len(vec)}")

vec_np = np.array([vec], dtype=np.float32)
print(f"  numpy shape: {vec_np.shape}")
