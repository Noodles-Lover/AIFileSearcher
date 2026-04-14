"""
RAG 评估测试脚本

使用本地 Hugging Face 模型进行 ragas 评估

模型位置: d:/_Programming/CompleteProjects/AIFileSearcher/models/LLM/
"""

import os
import sys
import io

# 设置 UTF-8 编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加 backend 目录到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from datasets import Dataset

import ragas
from ragas.llms import InstructorLLM
from pydantic import BaseModel, Field
from typing import List, Optional


# ============================================================
# 本地 LLM 配置
# ============================================================

LOCAL_LLM_PATH = "d:/_Programming/CompleteProjects/AIFileSearcher/models/LLM/Qwen2.5-3B-Instruct"
# 也可以使用其他模型:
# LOCAL_LLM_PATH = "d:/_Programming/CompleteProjects/AIFileSearcher/models/LLM/Phi-3-mini-4k-instruct"
# LOCAL_LLM_PATH = "d:/_Programming/CompleteProjects/AIFileSearcher/models/LLM/Qwen2.5-7B-Instruct"


def get_device():
    """获取设备"""
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


class LocalInstructorLLM(InstructorLLM):
    """
    使用 instructor 包装本地 Hugging Face 模型
    使其适配 ragas 的 InstructorLLM 接口
    """

    def __init__(self, model_path: str, device: str = None):
        self.model_path = model_path
        self.device = device or get_device()

        print(f"Loading local model from: {model_path}")
        print(f"Using device: {self.device}")

        # 加载 tokenizer 和模型
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            trust_remote_code=True
        )

        if self.device == "cuda" and torch.cuda.is_available():
            self.model = AutoModelForCausalLM.from_pretrained(
                model_path,
                trust_remote_code=True,
                torch_dtype=torch.float16,
                device_map="auto",
            )
        else:
            self.model = AutoModelForCausalLM.from_pretrained(
                model_path,
                trust_remote_code=True,
                torch_dtype=torch.float32,
            )
            self.model.to(self.device)

        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        print("Model loaded successfully!")

    def _generate_response(self, prompt: str, **kwargs) -> str:
        """生成文本响应"""
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True)
        inputs = {k: v.to(self.model.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=kwargs.get("max_tokens", 512),
                temperature=kwargs.get("temperature", 0.1),
                do_sample=kwargs.get("temperature", 0.1) > 0,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )

        response = self.tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[1]:],
            skip_special_tokens=True
        ).strip()
        return response


def create_local_llm() -> LocalInstructorLLM:
    """创建本地 LLM 实例"""
    return LocalInstructorLLM(LOCAL_LLM_PATH)


# ============================================================
# 测试数据
# ============================================================

TEST_DATA = {
    "user_input": [
        "What is Python programming language?",
        "How does machine learning work?",
        "What are the benefits of renewable energy?",
    ],
    "retrieved_contexts": [
        [
            "Python is a high-level, interpreted programming language known for its readable syntax. It was created by Guido van Rossum and first released in 1991. Python supports multiple programming paradigms.",
            "Python is widely used in web development, data analysis, AI, and automation."
        ],
        [
            "Machine learning is a subset of AI that enables systems to learn from data. It uses algorithms to identify patterns.",
            "There are three main types: supervised, unsupervised, and reinforcement learning."
        ],
        [
            "Renewable energy comes from natural sources that are constantly replenished. Solar, wind, hydro are primary sources.",
            "Benefits include reduced carbon emissions, lower pollution, and decreased dependence on fossil fuels."
        ],
    ],
    "response": [
        "Python is a high-level programming language created by Guido van Rossum in 1991, known for its readable syntax.",
        "Machine learning is a branch of AI that allows systems to learn from data through various algorithms.",
        "Renewable energy from sources like solar and wind offers environmental benefits."
    ],
    "ground_truth": [
        "Python is a programming language developed by Guido van Rossum in 1991.",
        "Machine learning enables systems to learn from data through algorithms.",
        "Renewable energy provides sustainable energy while reducing emissions."
    ],
}


# ============================================================
# 主程序
# ============================================================

def run_evaluation():
    """运行评估（供外部调用）"""
    from ragas.metrics.collections import (
        ContextRelevance,
        ContextRecall,
        AnswerRelevancy,
    )

    print("=" * 60)
    print("RAG Evaluation Test - Local Model")
    print("=" * 60)
    print(f"\nModel: {LOCAL_LLM_PATH}")
    print(f"Ragas version: {ragas.__version__}")
    print("\nMetrics:")
    print("  1. Context Relevance")
    print("  2. Context Recall")
    print("  3. Answer Relevancy")
    print("=" * 60)

    # 初始化本地 LLM
    print("\nLoading local model (this may take a moment)...")
    try:
        llm = create_local_llm()
        print("LLM loaded successfully!")
    except Exception as e:
        print(f"\nFailed to load model: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # 创建数据集
    dataset = Dataset.from_dict(TEST_DATA)

    # 运行评估
    print("\nRunning evaluation...")
    try:
        metrics = [
            ContextRelevance(llm=llm),
            ContextRecall(llm=llm),
            AnswerRelevancy(llm=llm),
        ]

        from ragas import evaluate
        result = evaluate(dataset=dataset, metrics=metrics)

        # 输出结果
        print("\n" + "=" * 60)
        print("Evaluation Results")
        print("=" * 60)
        print(result)

        # 详细分数
        print("\n" + "-" * 60)
        print("Detailed Scores:")
        print("-" * 60)

        result_df = result.to_pandas()
        for idx, row in result_df.iterrows():
            q = row['user_input'][:50]
            print(f"\n[{idx + 1}] {q}...")
            print(f"    Context Relevance: {row['context_relevance']:.4f}")
            print(f"    Context Recall:    {row['context_recall']:.4f}")
            print(f"    Answer Relevancy: {row['answer_relevancy']:.4f}")

        print("\n" + "=" * 60)
        print("Evaluation completed!")
        print("=" * 60)

    except Exception as e:
        print(f"\nError during evaluation: {e}")
        import traceback
        traceback.print_exc()
        return False
    return True


if __name__ == "__main__":
    success = run_evaluation()
    sys.exit(0 if success else 1)
