import os
import sys
import shutil

# 將 backend 的上一級目錄添加到路徑，以便導入 backend 模塊
# 當前腳本在 backend/test/test_faiss.py
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(backend_dir)
sys.path.append(project_root)

from backend.embedding.EmbeddingModel import EmbeddingModel
from backend.embedding.VectorStore import VectorStore

def test_faiss_workflow():
    print("="*50)
    print("FAISS 向量存儲集成測試")
    print("="*50)

    # 1. 準備模型
    # 自動掃描 models 目錄
    models_dir = os.path.join(project_root, "models")
    if not os.path.exists(models_dir):
        print("錯誤: models 目錄不存在，請先下載模型")
        return
        
    available_models = [d for d in os.listdir(models_dir) if os.path.isdir(os.path.join(models_dir, d))]
    if not available_models:
        print("錯誤: 沒有找到模型")
        return
        
    model_name = available_models[0]
    print(f"[1/4] 加載嵌入模型: {model_name}")
    embedder = EmbeddingModel(model_name)
    
    # 2. 準備測試數據
    texts = [
        "蘋果是一種水果",
        "香蕉也是水果",
        "Python 是編程語言",
        "Java 和 C++ 常用於後端開發",
        "今天天氣真好"
    ]
    metas = [
        {"id": 1, "content": "蘋果是一種水果", "category": "fruit"},
        {"id": 2, "content": "香蕉也是水果", "category": "fruit"},
        {"id": 3, "content": "Python 是編程語言", "category": "tech"},
        {"id": 4, "content": "Java 和 C++ 常用於後端開發", "category": "tech"},
        {"id": 5, "content": "今天天氣真好", "category": "daily"}
    ]
    
    # 3. 生成向量
    print(f"[2/4] 生成向量 ({len(texts)} 條文本)...")
    vectors = embedder.encode(texts)
    dimension = len(vectors[0])
    print(f"      向量維度: {dimension}")

    # 4. 初始化 FAISS 並存儲
    print(f"[3/4] 初始化 FAISS 並存儲...")
    
    # 將測試文件保存在 backend/test/ 目錄下
    test_index_path = os.path.join(current_dir, "test_index.bin")
    test_metadata_path = os.path.join(current_dir, "test_metadata.json")

    # 清理舊的索引文件以確保測試乾淨
    if os.path.exists(test_index_path): os.remove(test_index_path)
    if os.path.exists(test_metadata_path): os.remove(test_metadata_path)
    
    store = VectorStore(dimension, index_path=test_index_path, metadata_path=test_metadata_path)
    
    # 打印當前索引類型
    print(f"      FAISS 索引類型: {type(store.index).__name__} (L2 Distance)")
    print(f"      索引文件路徑: {test_index_path}")
    
    store.add(vectors, metas)
    print(f"      已存儲 {store.index.ntotal} 條向量")

    # 5. 執行語義搜索
    print("\n" + "="*30)
    user_query = "編程語言"
    print(f"[4/4] 執行搜索: '{user_query}'")
    
    query_vec = embedder.encode(user_query)[0]
    results = store.search(query_vec, k=3)
    
    print("\n搜索結果:")
    if not results:
        print("未找到匹配結果")
    else:
        for i, res in enumerate(results):
            print(f"  {i+1}. 內容: {res['content']}")
            print(f"     分類: {res['category']}")
            print(f"     距離: {res['score']:.4f} (越小越相似)")
            print("-" * 30)

if __name__ == "__main__":
    test_faiss_workflow()
