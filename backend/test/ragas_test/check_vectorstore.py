"""检查向量存储状态"""
import sys
import os

# 切换到 backend 目录并添加路径
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.getcwd())

# 设置 PYTHONPATH
os.environ['PYTHONPATH'] = os.getcwd()

from utils.path_utils import ensure_project_path
ensure_project_path()

from RAG.SystemManager import SystemManager

sm = SystemManager.get_instance()
store = sm.get_vector_store()

print("=" * 60)
print("Vector Store Status")
print("=" * 60)
print(f"Index type: {type(store.index).__name__}")
print(f"Total vectors: {store.index.ntotal if store.index else 0}")
print(f"Metadata entries: {len(store.metadata)}")
print()

# 检查是否有测试文件
test_found = []
for m in store.metadata:
    fp = m.get("file_path", "")
    if "testFiles" in fp or "testfiles" in fp.lower():
        test_found.append(fp)

if test_found:
    print(f"Found {len(test_found)} test files in metadata")
    for fp in test_found[:5]:
        print(f"  - {fp}")
else:
    print("No testFiles found in metadata!")

print("\nFirst 3 metadata entries:")
for i, m in enumerate(store.metadata[:3]):
    fp = m.get("file_path", "N/A")
    ct = m.get("chunk_text", "N/A")
    print(f"{i+1}. file: {fp}")
    print(f"   chunk: {ct[:60]}...")
