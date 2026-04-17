# RAG 检索评估指南

本模块用于评估 RAG 检索系统的性能，通过测试不同配置下的检索效果，选择最优方案。

## 评估指标

| 指标 | 中文名 | 说明 |
|------|--------|------|
| P@1 | 精确率@1 | Top-1 结果命中的比例 |
| P@3 | 精确率@3 | Top-3 中命中文件数/3 |
| MRR | 平均倒数排名 | 首个命中位置的倒数均值 |
| Hit Rate@3 | 命中率@3 | Top-3 有命中的查询比例 |

### 指标关系

```
P@1 ≤ Hit Rate@3
P@3 ≤ Hit Rate@3 * 3
MRR ≤ Hit Rate@3
```

## 快速开始

### 运行评估

```powershell
$env:PYTHONIOENCODING="utf-8"
$env:PYTHONUTF8="1"
D:/_Programming/CompleteProjects/AIFileSearcher/backend/venv/Scripts/python.exe `
    D:/_Programming/CompleteProjects/AIFileSearcher/backend/test/ragas_test/ragas_retrieval_eval.py
```

## 配置说明

所有配置集中在 `eval_config.py` 中：

```python
# ============ 遍历配置 ============
# 配置说明：
# - 每个列表放一项则执行一次，放多项则遍历测试
# - 设为 None 则跳过该项，使用默认值

# 所有要测试的嵌入模型
ALL_EMBEDDING_MODELS = ["bge-base-zh-v1.5"]

# 所有要测试的索引类型
ALL_INDEX_TYPES = ["IndexFlatL2", "IndexHNSWFlat"]

# 所有要测试的分块策略
# None = 使用 DEFAULT_STRATEGIES（按扩展名自动选择）
ALL_CHUNKING_STRATEGIES = None

# ============ 其他配置 ============
CURRENT_TEST_TYPE = "mixed"  # 测试类型: txt, md, pdf, ppt, doc, mixed
ENABLE_QUERY_REWRITE = True  # 是否启用 LLM 重写查询
LLM_TYPE = "deepseek"        # "deepseek" (API) 或 "local" (本地模型)
```

### 配置组合示例

**1. 只遍历索引类型（使用默认分块策略）**
```python
ALL_EMBEDDING_MODELS = ["bge-base-zh-v1.5"]
ALL_INDEX_TYPES = ["IndexFlatL2", "IndexHNSWFlat"]
ALL_CHUNKING_STRATEGIES = None  # 按文件类型自动选择
```

**2. 遍历全部组合**
```python
ALL_EMBEDDING_MODELS = ["bge-base-zh-v1.5", "bge-large-zh-v1.5"]
ALL_INDEX_TYPES = ["IndexFlatL2", "IndexHNSWFlat"]
ALL_CHUNKING_STRATEGIES = [
    SlidingWindowChunking(chunk_size=500, overlap=50),
    ParagraphChunking(lines_per_para=5),
]
```

**3. 对所有文件使用同一分块策略**
```python
ALL_EMBEDDING_MODELS = ["bge-base-zh-v1.5"]
ALL_INDEX_TYPES = ["IndexFlatL2"]
ALL_CHUNKING_STRATEGIES = [SentenceChunking(max_chars=500)]  # 所有文件都用句子分块
```

## 测试用例配置

编辑 `test_cases.json`：

```json
{
  "mixed": {
    "path": "testFiles/mixed",
    "queries": [
      {"query": "体检报告在哪里", "expected_category": "健康医疗"},
      {"query": "合同协议模板", "expected_category": "合同"},
      ...
    ]
  },
  "txt": { "path": "testFiles/txt", "queries": [...] },
  "md": { "path": "testFiles/md", "queries": [...] },
  "pdf": { "path": "testFiles/pdf", "queries": [...] },
  "doc": { "path": "testFiles/doc", "queries": [...] },
  "ppt": { "path": "testFiles/ppt", "queries": [...] }
}
```

### 测试用例数量

| 测试类型 | 分类数 | 每类用例数 | 总用例数 |
|----------|--------|-----------|---------|
| mixed | 10 | 5 | 50 |
| txt | 6 | 5 | 30 |
| md | 5 | 5 | 25 |
| pdf | 5 | 5 | 25 |
| doc | 5 | 5 | 25 |
| ppt | 5 | 5 | 25 |

## 文件说明

| 文件 | 说明 |
|------|------|
| `ragas_retrieval_eval.py` | 评估脚本主程序 |
| `eval_config.py` | 评估配置（模型、策略、测试类型） |
| `eval_reporter.py` | 结果导出模块 |
| `ragas_evaluation.py` | 评估指标计算 |
| `summarize_results.py` | 结果汇总脚本 |
| `test_cases.json` | 测试用例集 |
| `EVAL_GUIDE.md` | 本文档 |

## 输出结果

评估结果保存在 `result/{类型}/` 目录下：

```
result/
├── mixed/
│   ├── embedding/
│   │   ├── bge-base-zh-v1.5-IndexFlatL2-Native-1.json
│   │   └── bge-base-zh-v1.5-IndexFlatL2-Native-1.txt
│   └── ...
├── txt/
└── md/
```

每个配置会生成 JSON 和 TXT 两种格式的结果文件。

## 默认分块策略

当 `ALL_CHUNKING_STRATEGIES = None` 时，系统使用 `DEFAULT_STRATEGIES`：

| 文件类型 | 分块策略 | 说明 |
|---------|---------|------|
| .md | ParagraphChunking | 段落分块 |
| .txt | ParagraphChunking | 段落分块 |
| .docx | SlidingWindowChunking | 滑动窗口分块 |
| .doc | SlidingWindowChunking | 滑动窗口分块 |
| .pdf | SentenceChunking | 句子分块 |
| .pptx | SlideChunking | 按幻灯片分块 |
| .ppt | SlideChunking | 按幻灯片分块 |

## FAISS 索引类型

| 索引类型 | 说明 | 特点 |
|---------|------|------|
| IndexFlatL2 | 精确 L2 距离 | 精确但慢 |
| IndexFlatIP | 内积相似度 | 精确但慢 |
| IndexIVFFlat | IVF 聚类加速 | 需训练数据 |
| IndexHNSWFlat | HNSW 图索引 | 高召回高速 |
| IndexLSH | 局部敏感哈希 | 二值向量压缩 |
