# 后端开发指南 (Backend Development Guide)

本项目后端使用 Python (FastAPI + PyQt6) 开发，并依赖虚拟环境 (Virtual Environment) 来管理依赖包。

## 1. 虚拟环境 (Virtual Environment)

本项目已在 `backend/venv` 目录下创建了虚拟环境。

**重要提示**: 所有的 Python 命令和包安装 **必须** 使用该虚拟环境。

### 如何使用

*   **Windows (PowerShell)**:
    *   激活虛擬環境 (可選，但在命令行中方便): `backend\venv\Scripts\activate`
    *   直接使用虛擬環境的 Python: `backend\venv\Scripts\python.exe`
    *   直接使用虛擬環境的 Pip: `backend\venv\Scripts\pip.exe`

### 常用命令示例

*   **启动应用**:
    ```powershell
    backend\venv\Scripts\python gui/main.py
    ```

*   **安装依赖**:
    ```powershell
    backend\venv\Scripts\pip install package_name
    ```

*   **导出依赖**:
    ```powershell
    backend\venv\Scripts\pip freeze > requirements.txt
    ```

## 2. 项目结构与功能概述

### `api/` (API 接口层)

负责定义 HTTP 接口，处理前端请求。

| 文件 | 说明 |
|------|------|
| `server.py` | 应用入口，启动 FastAPI 服务，配置 CORS |
| `files.py` | 文件操作接口（预览、打开、图标等） |
| `search.py` | 搜索接口（Everything 搜索、向量搜索） |
| `index.py` | 索引接口（SSE 流式进度反馈） |
| `llm.py` | LLM 模型管理接口 |

### `gui/` (桌面 GUI 层)

负责创建桌面窗口，嵌入 Web 界面。

| 文件 | 说明 |
|------|------|
| `main.py` | 桌面应用入口，启动 FastAPI 线程，创建 PyQt6 窗口 |

### `RAG/` (RAG 系统层)

负责 RAG 系统的核心组件管理和对外接口。

| 文件 | 说明 |
|------|------|
| `SystemManager.py` | 系统管理器（单例模式） |
| `EmbeddingModel.py` | 嵌入模型封装 |
| `LocalLLM.py` | 本地 LLM 封装 |
| `DeepSeekLLM.py` | DeepSeek API 封装 |
| `VectorStore.py` | FAISS 向量存储封装 |
| `FileCache.py` | 文件缓存管理器 |

详见 [RAG 模块文档](RAG/DEVELOPMENT.md)

### `process/` (内容处理层)

负责文件的读取、解析、清洗和分块。

| 目录/文件 | 说明 |
|----------|------|
| `FileProcessor.py` | 文件处理器调度器 |
| `BaseFileProcessor.py` | 文件处理器基类 |
| `text_chunk/` | 文本分块处理器目录 |
| `semi_structured/` | 半结构化描述处理器目录 |
| `binary/` | 二进制文件描述处理器目录 |

详见 [文件处理文档](process/ProcessDocs.md)

### `utils/` (工具层)

通用工具函数。

| 文件 | 说明 |
|------|------|
| `path_utils.py` | 路径工具 |
| `settings_manager.py` | 设置管理器 |
| `model_utils.py` | 模型工具 |
| `IndexedFoldersManager.py` | 索引文件夹管理 |
| `search_utils.py` | 搜索工具 |

### `test/` (测试脚本)

测试脚本目录，详见 [测试脚本说明](test/TESTSCRIPTS.md)

| 目录/文件 | 说明 |
|----------|------|
| `ragas_test/` | RAG 评估框架 |
| `test_embedding.py` | 嵌入模型测试 |
| `test_faiss.py` | FAISS 向量存储测试 |
| `test_llm.py` | LLM 模型测试 |

## 3. 系统启动流程

```
1. 启动 gui/main.py 或 api/server.py
2. FastAPI 服务启动，触发 on_startup 事件
3. SystemManager.get_instance() 获取单例
4. 自动调用 _auto_load() 加载嵌入模型和 LLM 模型
5. 前端页面加载完成
```

## 4. 嵌入模型 (Embedding Models)

本项目支持加载本地嵌入模型。

*   **模型存放位置**: `models/embedding/` 文件夹
*   **支持的模型**: BGE 系列, BGE-M3, M3E 系列, Qwen3-Embedding

**代码调用**:
```python
from backend.RAG.SystemManager import SystemManager

sm = SystemManager.get_instance()
embedder = sm.get_embedding_model()
vectors = embedder.encode(["你好", "世界"])
```

## 5. LLM 模型 (LLM Models)

本项目支持本地 LLM 和 DeepSeek API。

*   **本地模型位置**: `models/LLM/` 文件夹
*   **API 模式**: DeepSeek API

**代码调用**:
```python
from backend.RAG.SystemManager import SystemManager

sm = SystemManager.get_instance()
response = sm.generate_with_llm(prompt)
```

## 6. 向量搜索与索引 (Vector Search & Indexing)

本项目使用 FAISS 进行向量存储和检索。

### 6.1 向量存储

*   **存储位置**: `data/` 文件夹
    *   `faiss_index.bin`: FAISS 索引文件
    *   `metadata.json`: 元数据文件
    *   `faiss_index.info`: 索引信息文件

### 6.2 支持的索引类型

| 索引类型 | 说明 | 特点 |
|---------|------|------|
| IndexFlatL2 | 精确 L2 距离 | 精确但慢 |
| IndexFlatIP | 内积相似度 | 精确但慢 |
| IndexIVFFlat | IVF 聚类加速 | 需训练数据 |
| IndexHNSWFlat | HNSW 图索引 | 高召回高速 |
| IndexLSH | 局部敏感哈希 | 二值向量压缩 |

### 6.3 索引流程

```
文件扫描 → 内容解析 → 文本分块 → 向量化 → 存储
                                      ↓
                              SSE 实时推送进度
```

### 6.4 索引 API

| API | 方法 | 说明 |
|-----|------|------|
| `/api/index_folder` | POST | 建立索引（SSE 流式返回进度） |
| `/api/clear_index` | POST | 清除所有索引 |
| `/api/indexed_folders` | GET | 获取已索引的文件夹列表 |

### 6.5 搜索 API

| API | 方法 | 说明 |
|-----|------|------|
| `/api/vector_search` | POST | 向量语义搜索 |
| `/api/search` | GET | Everything 关键词搜索 |

## 7. 测试脚本

详见 [测试脚本说明](test/TESTSCRIPTS.md)

### 快速运行

```powershell
# RAG 评估
cd backend/test/ragas_test
..\..\venv\Scripts\python ragas_retrieval_eval.py
```
