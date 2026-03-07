import os
import sys

# 嘗試導入 huggingface_hub
try:
    from huggingface_hub import snapshot_download
except ImportError:
    print("錯誤: 未安裝 huggingface_hub 庫。")
    print("請運行: backend\\venv\\Scripts\\pip install huggingface-hub")
    sys.exit(1)

def download_model(model_id, local_dir):
    print(f"正在下載模型 {model_id} 到 {local_dir}...")
    print("這可能需要一些時間，請耐心等待...")
    
    try:
        snapshot_download(
            repo_id=model_id, 
            local_dir=local_dir, 
            local_dir_use_symlinks=False,
            resume_download=True
        )
        print(f"\n下載完成！模型已保存至: {local_dir}")
        print("您現在可以在後端代碼中通過文件夾名稱加載此模型。")
        
    except Exception as e:
        print(f"\n下載失敗: {e}")
        print("請檢查您的網絡連接（可能需要科學上網）或模型 ID 是否正確。")

if __name__ == "__main__":
    # 推薦的嵌入模型列表
    models = {
        "1": "BAAI/bge-small-zh-v1.5",
        "2": "BAAI/bge-large-zh-v1.5",
        "3": "BAAI/bge-m3",
        "4": "Alibaba-NLP/gte-Qwen2-1.5B-instruct" 
    }
    
    print("="*50)
    print("AI File Searcher - 嵌入模型下載助手")
    print("="*50)
    print("請選擇要下載的模型:")
    for k, v in models.items():
        print(f"{k}. {v}")
    print("0. 自定義輸入模型 ID")
    
    choice = input("\n請輸入選項 (默認 1): ").strip()
    if not choice:
        choice = "1"
        
    if choice == "0":
        model_id = input("請輸入 HuggingFace 模型 ID (例如 BAAI/bge-small-zh-v1.5): ").strip()
    else:
        model_id = models.get(choice)
    
    if not model_id:
        print("無效的選項，退出。")
        sys.exit(1)
        
    # 保存路徑：項目根目錄/models/模型名
    # 獲取當前腳本所在目錄 (backend/)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 獲取項目根目錄 (backend/ 的上一級)
    project_root = os.path.dirname(current_dir)
    models_root = os.path.join(project_root, "models")
    
    # 將 '/' 替換為 '_' 或直接取最後一部分，這裡我們保留文件夾結構清晰，直接用最後一部分
    save_name = model_id.split("/")[-1]
    save_path = os.path.join(models_root, save_name)
    
    # 確保 models 目錄存在
    if not os.path.exists(models_root):
        os.makedirs(models_root)
        
    download_model(model_id, save_path)
