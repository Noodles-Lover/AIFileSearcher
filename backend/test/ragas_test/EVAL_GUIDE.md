# RAG 检索评估指南

本模块用于评估 RAG 检索系统的性能，通过测试不同分块策略下的检索效果，选择最优方案。

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

### 切换测试类型

在 `eval_config.py` 中修改：

```python
CURRENT_TEST_TYPE = "txt"  # 或 "md"
```

### 选择 LLM 类型

```python
LLM_TYPE = "deepseek"  # API 调用，速度快，质量好（默认）
LLM_TYPE = "local"     # 本地模型，需要加载 2-3 分钟
```

### 配置分块策略

在 `eval_config.py` 的 `ALL_CHUNKING_STRATEGIES` 中定义要测试的分块策略。

## 测试用例配置

编辑 `test_cases.json`：

```json
{
  "txt": {
    "path": "testFiles/txt",
    "queries": [
      {"query": "体检报告", "expected_category": "健康医疗"},
      ...
    ]
  },
  "md": { ... }
}
```

### 测试用例数量

| 测试类型 | 分类数 | 每类用例数 | 总用例数 |
|----------|--------|-----------|---------|
| txt | 6 | 5 | 30 |
| md | 5 | 5 | 25 |

## 文件说明

| 文件 | 说明 |
|------|------|
| `ragas_retrieval_eval.py` | 评估脚本主程序 |
| `eval_config.py` | 评估配置（模型、策略、测试类型） |
| `eval_reporter.py` | 结果导出模块 |
| `test_cases.json` | 测试用例集 |
| `DeepSeekLLM.py` | DeepSeek API 封装 |

## 输出结果

评估结果保存在 `result/{类型}/` 目录下：

```
result/
├── txt/
│   ├── bge-m3-IndexFlatL2-FixedSize(size=500)-1.json
│   ├── bge-m3-IndexFlatL2-SlidingWindow(size=500, overlap=50)-1.json
│   └── ...
└── md/
    └── ...
```

每个策略会生成 JSON 和 TXT 两种格式的结果文件。
