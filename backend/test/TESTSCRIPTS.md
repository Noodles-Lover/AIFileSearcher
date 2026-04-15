# 测试脚本说明

本文件夹包含 AI 文件搜索器的所有测试脚本，按功能分类：

## 算法测试

| 脚本 | 说明 | 运行命令 |
|------|------|----------|
| `test_algorithm_simple.py` | 动态分块提取算法测试 | `python test_algorithm_simple.py` |
| `test_decay_rates.py` | 衰减率参数测试 | `python test_decay_rates.py` |
| `test_decay_mapping.py` | 衰减率映射测试 | `python test_decay_mapping.py` |

## 功能测试

| 脚本 | 说明 | 运行命令 |
|------|------|----------|
| `test_file_merge.py` | 文件合并功能测试 | `python test_file_merge.py` |
| `test_local_data.py` | 本地数据功能测试 | `python test_local_data.py` |
| `test_list_api.py` | 文件列表 API 测试 | `python test_list_api.py` |
| `test_icon_fix.py` | 图标功能测试 | `python test_icon_fix.py` |
| `test_search_content.py` | 搜索内容测试 | `python test_search_content.py` |

## 核心组件测试

| 脚本 | 说明 | 运行命令 |
|------|------|----------|
| `test_embedding.py` | 嵌入模型测试 | `python test_embedding.py` |
| `test_faiss.py` | FAISS 向量搜索测试 | `python test_faiss.py` |
| `test_sse.py` | SSE 实时推送测试 | `python test_sse.py` |

## LLM 模型测试

| 脚本 | 说明 | 运行命令 |
|------|------|----------|
| `test_llm.py` | LLM 模型测试 | `python test_llm.py` |

## RAG 评估测试

| 脚本 | 说明 | 运行命令 |
|------|------|----------|
| `ragas_test/ragas_retrieval_eval.py` | RAG 检索评估 | 详见 [评估指南](ragas_test/EVAL_GUIDE.md) |

### 评估测试用例

| 测试类型 | 分类数 | 每类用例数 | 总用例数 |
|----------|--------|-----------|---------|
| txt | 6 | 5 | 30 |
| md | 5 | 5 | 25 |

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
