# 测试脚本说明

本文件夹包含 AI 文件搜索器的所有测试脚本，按功能分类：

## 核心组件测试

| 脚本 | 说明 | 运行命令 |
|------|------|----------|
| `test_embedding.py` | 嵌入模型测试 | `python test_embedding.py` |
| `test_faiss.py` | FAISS 向量搜索测试 | `python test_faiss.py` |
| `test_sse.py` | SSE 实时推送测试 | `python test_sse.py` |

## 算法测试

| 脚本 | 说明 | 运行命令 |
|------|------|----------|
| `test_algorithm_simple.py` | 动态分块提取算法测试 | `python test_algorithm_simple.py` |
| `test_decay_rates.py` | 衰减率参数测试 | `python test_decay_rates.py` |
| `test_decay_mapping.py` | 衰减率映射测试 | `python test_decay_mapping.py` |
| `test_dynamic_algorithm.py` | 动态算法测试 | `python test_dynamic_algorithm.py` |

## 功能测试

| 脚本 | 说明 | 运行命令 |
|------|------|----------|
| `test_file_merge.py` | 文件合并功能测试 | `python test_file_merge.py` |
| `test_local_data.py` | 本地数据功能测试 | `python test_local_data.py` |
| `test_list_api.py` | 文件列表 API 测试 | `python test_list_api.py` |
| `test_icon_fix.py` | 图标功能测试 | `python test_icon_fix.py` |
| `test_search_content.py` | 搜索内容测试 | `python test_search_content.py` |

## LLM 模型测试

| 脚本 | 说明 | 运行命令 |
|------|------|----------|
| `test_llm.py` | LLM 模型测试 | `python test_llm.py` |

## RAG 评估测试

详见 [评估指南](ragas_test/EVAL_GUIDE.md)

| 脚本 | 说明 |
|------|------|
| `ragas_test/ragas_retrieval_eval.py` | RAG 检索评估主脚本 |
| `ragas_test/ragas_evaluation.py` | 评估指标计算 |
| `ragas_test/eval_reporter.py` | 结果导出模块 |
| `ragas_test/summarize_results.py` | 结果汇总脚本 |
| `ragas_test/eval_config.py` | 评估配置 |
| `ragas_test/test_cases.json` | 测试用例集 |

### 评估测试用例

| 测试类型 | 分类数 | 每类用例数 | 总用例数 |
|----------|--------|-----------|---------|
| mixed | 10 | 5 | 50 |
| txt | 6 | 5 | 30 |
| md | 5 | 5 | 25 |
| pdf | 5 | 5 | 25 |
| doc | 5 | 5 | 25 |
| ppt | 5 | 5 | 25 |

## 运行方式

### 运行单个测试

```bash
cd backend/test
python test_embedding.py
```

### 运行所有功能测试

```bash
cd backend/test
python test_file_merge.py && python test_local_data.py && python test_list_api.py
```

### 运行 RAG 评估

```powershell
cd backend/test/ragas_test
python ragas_retrieval_eval.py
```
