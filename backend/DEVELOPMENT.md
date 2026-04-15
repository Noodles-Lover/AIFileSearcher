# 后端开发指南 (Backend Development Guide)

本项目后端使用 Python (FastAPI + PyQt6) 开发，并依赖虚拟环境 (Virtual Environment) 来管理依赖包。

## 1. 虚拟环境 (Virtual Environment)

本项目已在 `backend/venv` 目录下创建了虚拟环境。

**重要提示**: 所有的 Python 命令和包安装 **必须** 使用该虚拟环境，而不是系统全局的 Python。

### 如何使用

*   **Windows (PowerShell)**:
    *   激活虚拟环境 (可选，但在命令行中方便): `backend\venv\Scripts\activate`
    *   直接使用虚拟环境的 Python: `backend\venv\Scripts\python.exe`
    *   直接使用虚拟环境的 Pip: `backend\venv\Scripts\pip.exe`

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
*   **`server.py`**: 应用的入口文件。启动时自动加载模型，配置 CORS，并挂载其他路由模块。
*   **`files.py`**: 文件操作相关接口，包括预览、打开文件/文件夹、获取图标等。
*   **`search.py`**: 搜索功能相关接口，包括 Everything 搜索、列表文件和向量搜索。
*   **`index.py`**: 索引功能相关接口，建立文件夹索引，使用 SSE 提供实时进度反馈。
*   **`llm.py`**: LLM 模型管理接口，包括模型列表、加载、卸载和文本生成。

### `gui/` (桌面 GUI 层)
负责创建桌面窗口，嵌入 Web 界面。
*   **`main.py`**: 桌面应用的入口。启动后端 FastAPI 线程，创建 PyQt6 `QWebEngineView` 窗口并加载前端页面。

### `RAG/` (RAG 系统层)
负责 RAG 系统的核心组件管理和对外接口。
*   **`SystemManager.py`**: 系统管理器，单例模式，统一管理嵌入模型、LLM 和向量存储。提供模型加载、切换和生成接口。
*   **`EmbeddingModel.py`**: 嵌入模型封装，支持加载本地或 HuggingFace 模型。
*   **`LocalLLM.py`**: 本地 LLM 封装，支持文本生成。
*   **`VectorStore.py`**: FAISS 向量存储封装，负责向量存储和检索。
*   **`FileCache.py`**: 文件缓存管理器，跟踪文件修改时间，避免重复处理。

### `process/` (内容处理层)
负责文件的读取、解析、清洗和分块。
*   **`FileProcessor.py`**: 核心处理类。根据文件扩展名和处理模式调度对应的处理器。
*   **`BaseFileProcessor.py`**: 文件处理器基类，定义统一接口。
*   **`text_chunk/`**: 文本分块处理器和解析器目录。
    *   **`TextChunkProcessor.py`**: 文本分块处理器
    *   **`ChunkingStrategy.py`**: 分块策略（固定大小、段落、句子）
    *   **`TXTParser.py`**, **`MDParser.py`**, **`PDFParser.py`** 等：具体文件解析器
*   **`semi_structured/`**: 半结构化描述处理器目录
*   **`binary/`**: 二进制文件描述处理器目录

### `utils/` (工具层)
通用工具函数。
*   **`path_utils.py`**: 路径工具，获取项目根目录、模型路径等
*   **`settings_manager.py`**: 设置管理器，保存和加载用户设置
*   **`model_utils.py`**: 模型工具，列举可用模型
*   **`icons.py`**: 系统图标提取工具

## 3. 系统启动流程

1.  启动 `gui/main.py` 或 `api/server.py`
2.  FastAPI 服务启动，触发 `on_startup` 事件
3.  `SystemManager.get_instance()` 获取单例
4.  自动调用 `_auto_load()` 加载嵌入模型和 LLM 模型
5.  前端页面加载完成

## 4. 嵌入模型 (Embedding Models)

本项目支持加载本地嵌入模型 (如 BGE-M3)。

*   **模型存放位置**: 项目根目录的 `models/embedding/` 文件夹
*   **代码调用**:
    ```python
    from backend.RAG.SystemManager import SystemManager

    sm = SystemManager.get_instance()
    sm.reload_embedding_model("bge-m3")  # 切换模型
    embedder = sm.get_embedding_model()
    vectors = embedder.encode(["你好", "世界"])
    ```

## 5. LLM 模型 (LLM Models)

本项目支持加载本地 LLM 模型 (如 Qwen, Phi)。

*   **模型存放位置**: 项目根目录的 `models/LLM/` 文件夹
*   **代码调用**:
    ```python
    from backend.RAG.SystemManager import SystemManager

    sm = SystemManager.get_instance()
    sm.reload_llm("Qwen2.5-3B-Instruct")  # 切换模型
    response = sm.generate_with_llm(prompt)
    ```

## 6. 向量搜索与索引 (Vector Search & Indexing)

本项目使用 FAISS 进行向量存储和检索。

### 6.1 向量存储

*   **存储位置**: `data/` 文件夹
    *   `faiss_index.bin`: FAISS 索引文件
    *   `metadata.json`: 元数据文件
*   **支持的索引类型**: IndexFlatL2, IndexFlatIP, IndexIVFFlat, IndexHNSWFlat

### 6.2 索引流程

1.  文件扫描 → 内容解析 → 文本分块 → 向量化 → 存储
2.  实时进度通过 SSE 推送到前端

### 6.3 索引 API

*   `POST /api/index_folder`: 建立索引（SSE 流式返回进度）
*   `POST /api/clear_index`: 清除所有索引
*   `GET /api/indexed_folders`: 获取已索引的文件夹列表

### 6.4 搜索 API

*   `POST /api/vector_search`: 向量语义搜索
*   `GET /api/search`: Everything 关键词搜索

## 7. 测试脚本

*   **`test/test_llm.py`**: LLM 模型测试脚本，直接调用 LocalLLM 测试提示词
*   **`test/test_embedding.py`**: 嵌入模型测试
*   **`test/test_faiss.py`**: FAISS 向量存储测试

运行测试：
```powershell
backend\venv\Scripts\python backend/test/test_llm.py
```
