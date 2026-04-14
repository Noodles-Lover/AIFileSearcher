# RAG 评估测试模块

本模块用于使用 ragas 评估 RAG 系统的性能。

## 指标说明

- **Context Relevance（上下文相关性）**: 衡量检索到的上下文与问题的相关程度
- **Context Recall（上下文召回率）**: 衡量检索到的上下文是否包含标准答案中的信息
- **Answer Relevance（答案相关性）**: 衡量生成的答案与问题的相关程度

## 使用方法

```bash
# 设置代理（如需要下载模型）
$env:HTTP_PROXY="http://127.0.0.1:7890"
$env:HTTPS_PROXY="http://127.0.0.1:7890"

# 运行测试
cd d:/_Programming/CompleteProjects/AIFileSearcher/backend
.\venv\Scripts\python -m test.ragas_test.ragas_evaluation
```
