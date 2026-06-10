import os
import shutil
import subprocess
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

try:
    from huggingface_hub import snapshot_download
except ImportError:
    print("错误: 未安装 huggingface_hub。")
    print("请先运行 backend\\venv\\Scripts\\pip install huggingface-hub")
    sys.exit(1)



def download_model(model_id, local_dir):
    print(f"正在下载模型 {model_id} 到 {local_dir}...")
    print("这可能需要一些时间，请耐心等待...")

    try:
        snapshot_download(
            repo_id=model_id,
            local_dir=local_dir,
            local_dir_use_symlinks=False,
            resume_download=True,
        )
        print(f"\n下载完成，模型已保存到: {local_dir}")
        print("现在可以在程序设置里的模型列表中看到它。")
        return
    except Exception as first_error:
        print(f"\nHub 下载失败: {first_error}")


if __name__ == "__main__":
    print("=" * 50)
    print("AI File Searcher - 模型下载助手")
    print("=" * 50)
    print("请选择要下载的模型类型:")
    print("1. 嵌入模型 (Embedding Models)")
    print("2. LLM模型 (Language Models)")
    
    type_choice = input("\n请输入选项 (1 或 2): ").strip()
    
    embedding_models = {
        "1": "BAAI/bge-small-zh-v1.5",
        "2": "BAAI/bge-large-zh-v1.5",
        "3": "BAAI/bge-m3",
        "4": "BAAI/bge-small-en-v1.5",
        "5": "intfloat/multilingual-e5-base",
        "7": "Alibaba-NLP/gte-Qwen2-1.5B-instruct",
    }
    
    llm_models = {
        "1": "Qwen/Qwen2-0.5B-Instruct",
        "2": "Qwen/Qwen2-1.5B-Instruct",
        "3": "Qwen/Qwen2-7B-Instruct",
        "4": "Qwen/Qwen2.5-0.5B-Instruct",
        "5": "Qwen/Qwen2.5-1.5B-Instruct",
        "6": "Qwen/Qwen2.5-3B-Instruct",
        "7": "Qwen/Qwen2.5-7B-Instruct",
        "8": "THUDM/glm-4-9b-chat",
        "9": "THUDM/chatglm3-6b",
        "10": "microsoft/Phi-3-mini-4k-instruct",
        "11": "mistralai/Mistral-7B-Instruct-v0.2",
        "12": "mistralai/Mistral-7B-Instruct-v0.1",
    }
    
    if type_choice == "2":
        print("\n" + "=" * 50)
        print("LLM 模型列表:")
        print("注意: LLM模型通常较大(1GB-15GB)，请确保有足够的磁盘空间和网络带宽")
        print("=" * 50)
        for k, v in llm_models.items():
            print(f"{k}. {v}")
        print("0. 自定义输入模型 ID")
        
        choice = input("\n请输入选项: ").strip()
        
        if choice == "0":
            model_id = input("请输入 HuggingFace 模型 ID: ").strip()
        else:
            model_id = llm_models.get(choice)
            
        if not model_id:
            print("无效选项，程序退出。")
            sys.exit(1)
            
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        models_root = os.path.join(project_root, "models", "LLM")
        save_name = model_id.split("/")[-1]
        save_path = os.path.join(models_root, save_name)
        
    else:
        print("\n" + "=" * 50)
        print("嵌入模型列表:")
        print("=" * 50)
        for k, v in embedding_models.items():
            print(f"{k}. {v}")
        print("0. 自定义输入模型 ID")
        
        choice = input("\n请输入选项 (默认 1): ").strip()
        if not choice:
            choice = "1"
        
        if choice == "0":
            model_id = input("请输入 HuggingFace 模型 ID: ").strip()
        else:
            model_id = embedding_models.get(choice)
            
        if not model_id:
            print("无效选项，程序退出。")
            sys.exit(1)
            
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        models_root = os.path.join(project_root, "models", "embedding")
        save_name = model_id.split("/")[-1]
        save_path = os.path.join(models_root, save_name)

    if not os.path.exists(models_root):
        os.makedirs(models_root)

    download_model(model_id, save_path)
