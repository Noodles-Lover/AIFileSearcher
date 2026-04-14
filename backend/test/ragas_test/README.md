# RAG 检索评估

## 使用方法

**1. 运行命令**
```powershell
$env:PYTHONIOENCODING="utf-8"
$env:PYTHONUTF8="1"
D:/_Programming/CompleteProjects/AIFileSearcher/backend/venv/Scripts/python.exe `
    D:/_Programming/CompleteProjects/AIFileSearcher/backend/test/ragas_test/ragas_retrieval_eval.py
```

**2. 切换测试类型**

在 `ragas_retrieval_eval.py` 中修改：
```python
CURRENT_TEST_TYPE = "txt"  # 或 "md"
```

**3. LLM 类型选择**
```python
LLM_TYPE = "deepseek"  # API 调用，速度快，质量好（默认）
LLM_TYPE = "local"     # 本地模型，需要加载 2-3 分钟
```

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

## 评估指标

| 指标 | 说明 |
|------|------|
| Precision@1 | Top-1 准确率 |
| Precision@3 | Top-3 准确率 |
| MRR | 平均倒数排名 |
| Hit Rate@3 | Top-3 命中率 |

## 测试用例结构

**txt (18个用例)**: 健康医疗、娱乐休闲、学习资料、工作文档、生活记录、财务管理 各3个

**md (15个用例)**: 会议纪要、创意写作、报告分析、知识笔记、需求文档 各3个

## 文件说明

| 文件 | 说明 |
|------|------|
| `ragas_retrieval_eval.py` | 评估脚本 |
| `test_cases.json` | 测试用例集 |
| `DeepSeekLLM.py` | DeepSeek API 封装（自动禁用系统代理） |
