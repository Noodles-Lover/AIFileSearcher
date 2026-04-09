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


def download_with_git_mirror(model_id, local_dir):
    mirror_url = f"https://hf-mirror.com/{model_id}"
    print(f"\n切换到 git 镜像下载: {mirror_url}")

    if os.path.exists(local_dir):
        if os.path.isdir(local_dir) and not os.listdir(local_dir):
            os.rmdir(local_dir)
        else:
            raise RuntimeError(f"目标目录已存在且非空，无法继续镜像下载: {local_dir}")

    clone_result = subprocess.run(
        ["git", "clone", mirror_url, local_dir],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if clone_result.returncode != 0:
        raise RuntimeError(clone_result.stderr.strip() or clone_result.stdout.strip() or "git clone failed")

    lfs_result = subprocess.run(
        ["git", "-C", local_dir, "lfs", "pull"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if lfs_result.returncode != 0:
        raise RuntimeError(lfs_result.stderr.strip() or lfs_result.stdout.strip() or "git lfs pull failed")


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

        try:
            download_with_git_mirror(model_id, local_dir)
            print(f"\n镜像下载完成，模型已保存到: {local_dir}")
            print("现在可以在程序设置里的模型列表中看到它。")
            return
        except Exception as second_error:
            if os.path.isdir(local_dir) and not os.listdir(local_dir):
                shutil.rmtree(local_dir, ignore_errors=True)

            print(f"\n镜像下载也失败: {second_error}")
            print("请检查网络连接、镜像可达性，或稍后重试。")


if __name__ == "__main__":
    models = {
        "1": "BAAI/bge-small-zh-v1.5",
        "2": "BAAI/bge-large-zh-v1.5",
        "3": "BAAI/bge-m3",
        "4": "Alibaba-NLP/gte-Qwen2-1.5B-instruct",
        "5": "sentence-transformers/clip-ViT-B-32",
        "6": "sentence-transformers/clip-ViT-L-14",
    }

    print("=" * 50)
    print("AI File Searcher - 嵌入模型下载助手")
    print("=" * 50)
    print("请选择要下载的模型:")
    for k, v in models.items():
        print(f"{k}. {v}")
    print("0. 自定义输入模型 ID")

    choice = input("\n请输入选项 (默认 1): ").strip()
    if not choice:
        choice = "1"

    if choice == "0":
        model_id = input("请输入 HuggingFace 模型 ID: ").strip()
    else:
        model_id = models.get(choice)

    if not model_id:
        print("无效选项，程序退出。")
        sys.exit(1)

    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    models_root = os.path.join(project_root, "models")

    save_name = model_id.split("/")[-1]
    save_path = os.path.join(models_root, save_name)

    if not os.path.exists(models_root):
        os.makedirs(models_root)

    download_model(model_id, save_path)
