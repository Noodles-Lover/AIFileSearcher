import os
import sys

# 將 backend 添加到路徑，以便導入模塊
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from backend.embedding.EmbeddingModel import EmbeddingModel

def test_embedding():
    # 掃描 models 目錄下的所有文件夾
    models_dir = "models"
    if not os.path.exists(models_dir):
        print(f"錯誤: {models_dir} 目錄不存在，請先下載模型。")
        return

    # 獲取所有子文件夾作為模型列表
    available_models = [d for d in os.listdir(models_dir) if os.path.isdir(os.path.join(models_dir, d))]
    
    if not available_models:
        print(f"錯誤: {models_dir} 目錄下沒有找到任何模型文件夾。")
        return

    print(f"發現以下模型: {available_models}")
    
    # 測試文本
    test_texts = [
        "這是一個測試句子。",
        "Python 是一種強大的編程語言。",
        "人工智能正在改變世界。"
    ]
    
    print("\n" + "="*50)
    print("開始測試嵌入模型...")
    print("="*50)

    for model_name in available_models:
        print(f"\n[正在加載模型]: {model_name}")
        try:
            embedder = EmbeddingModel(model_name)
            
            print(f"[正在向量化] 測試文本: {test_texts}")
            vectors = embedder.encode(test_texts)
            
            print(f"[成功]")
            print(f"向量維度: {len(vectors[0])}")
            print(f"返回數量: {len(vectors)}")
            print("-" * 30)
            print("第一句的前 5 維向量預覽:")
            print(vectors[0][:5])
            print("-" * 30)
            
        except Exception as e:
            print(f"[失敗] 模型 {model_name} 加載或運行出錯: {e}")

if __name__ == "__main__":
    test_embedding()
