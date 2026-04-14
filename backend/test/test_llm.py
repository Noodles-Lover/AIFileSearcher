import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(backend_dir)
sys.path.append(project_root)

LLM_MODEL_ID = "Qwen2.5-3B-Instruct"

def main():
    from backend.RAG.LocalLLM import LocalLLM

    print("=" * 50)
    print("LLM 测试脚本")
    print(f"模型: {LLM_MODEL_ID}")
    print("输入 0 退出")
    print("=" * 50)

    llm = LocalLLM(LLM_MODEL_ID)

    while True:
        print("\n" + "-" * 40)
        prompt = input("请输入 prompt: ").strip()

        if prompt == "0":
            print("退出测试")
            break

        if not prompt:
            print("prompt 不能为空")
            continue

        try:
            response = llm.generate(prompt)
            print(f"\n回复:\n{response}")
        except Exception as e:
            print(f"生成失败: {e}")

if __name__ == "__main__":
    main()
