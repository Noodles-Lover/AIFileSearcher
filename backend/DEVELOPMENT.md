# 後端開發指南 (Backend Development Guide)

本項目後端使用 Python (FastAPI + PyQt6) 開發，並依賴虛擬環境 (Virtual Environment) 來管理依賴包。

## 1. 虛擬環境 (Virtual Environment)

本項目已在 `backend/venv` 目錄下創建了虛擬環境。

**重要提示**: 所有的 Python 命令和包安裝 **必須** 使用該虛擬環境，而不是系統全局的 Python。

### 如何使用

*   **Windows (PowerShell)**:
    *   激活虛擬環境 (可選，但在命令行中方便): `backend\venv\Scripts\activate`
    *   直接使用虛擬環境的 Python: `backend\venv\Scripts\python.exe`
    *   直接使用虛擬環境的 Pip: `backend\venv\Scripts\pip.exe`

### 常用命令示例

*   **啟動應用**:
    ```powershell
    backend\venv\Scripts\python gui/main.py
    ```

*   **安裝依賴**:
    ```powershell
    backend\venv\Scripts\pip install package_name
    ```

*   **導出依賴**:
    ```powershell
    backend\venv\Scripts\pip freeze > requirements.txt
    ```

## 2. 項目結構與功能概述

### `api/` (API 接口層)
負責定義 HTTP 接口，處理前端請求。
*   **`server.py`**: 應用的入口文件。啟動時自動加載模型，配置 CORS，並掛載其他路由模組。
*   **`files.py`**: 文件操作相關接口，包括預覽、打開文件/文件夾、獲取圖標等。
*   **`search.py`**: 搜索功能相關接口，包括 Everything 搜索、列表文件和向量搜索。
*   **`index.py`**: 索引功能相關接口，建立文件夾索引，使用 SSE 提供實時進度反饋。
*   **`llm.py`**: LLM 模型管理接口，包括模型列表、加載、卸載和文本生成。

### `gui/` (桌面 GUI 層)
負責創建桌面窗口，嵌入 Web 界面。
*   **`main.py`**: 桌面應用的入口。啟動後端 FastAPI 線程，創建 PyQt6 `QWebEngineView` 窗口並加載前端頁面。

### `RAG/` (RAG 系統層)
負責 RAG 系統的核心組件管理和對外接口。
*   **`SystemManager.py`**: 系統管理器，單例模式，統一管理嵌入模型、LLM 和向量存儲。提供模型加載、切換和生成接口。
*   **`EmbeddingModel.py`**: 嵌入模型封裝，支持加載本地或 HuggingFace 模型。
*   **`LocalLLM.py`**: 本地 LLM 封裝，支持文本生成。
*   **`VectorStore.py`**: FAISS 向量存儲封裝，負責向量存儲和檢索。
*   **`FileCache.py`**: 文件緩存管理器，跟踪文件修改時間，避免重複處理。

### `process/` (內容處理層)
負責文件的讀取、解析、清洗和分塊。
*   **`FileProcessor.py`**: 核心處理類。根據文件擴展名和處理模式調度對應的處理器。
*   **`BaseFileProcessor.py`**: 文件處理器基類，定義統一接口。
*   **`text_chunk/`**: 文本分塊處理器和解析器目錄。
    *   **`TextChunkProcessor.py`**: 文本分塊處理器
    *   **`ChunkingStrategy.py`**: 分塊策略（固定大小、段落、句子）
    *   **`TXTParser.py`**, **`MDParser.py`**, **`PDFParser.py`** 等：具體文件解析器
*   **`semi_structured/`**: 半結構化描述處理器目錄
*   **`binary/`**: 二進制文件描述處理器目錄

### `utils/` (工具層)
通用工具函數。
*   **`path_utils.py`**: 路徑工具，獲取項目根目錄、模型路徑等
*   **`settings_manager.py`**: 設置管理器，保存和加載用戶設置
*   **`model_utils.py`**: 模型工具，列舉可用模型
*   **`icons.py`**: 系統圖標提取工具

## 3. 系統啟動流程

1.  啟動 `gui/main.py` 或 `api/server.py`
2.  FastAPI 服務啟動，觸發 `on_startup` 事件
3.  `SystemManager.get_instance()` 獲取單例
4.  自動調用 `_auto_load()` 加載嵌入模型和 LLM 模型
5.  前端頁面加載完成

## 4. 嵌入模型 (Embedding Models)

本項目支持加載本地嵌入模型 (如 BGE-M3)。

*   **模型存放位置**: 項目根目錄的 `models/embedding/` 文件夾
*   **代碼調用**:
    ```python
    from backend.RAG.SystemManager import SystemManager

    sm = SystemManager.get_instance()
    sm.reload_embedding_model("bge-m3")  # 切換模型
    embedder = sm.get_embedding_model()
    vectors = embedder.encode(["你好", "世界"])
    ```

## 5. LLM 模型 (LLM Models)

本項目支持加載本地 LLM 模型 (如 Qwen, Phi)。

*   **模型存放位置**: 項目根目錄的 `models/LLM/` 文件夾
*   **代碼調用**:
    ```python
    from backend.RAG.SystemManager import SystemManager

    sm = SystemManager.get_instance()
    sm.reload_llm("Qwen2.5-3B-Instruct")  # 切換模型
    response = sm.generate_with_llm(prompt)
    ```

## 6. 向量搜索與索引 (Vector Search & Indexing)

本項目使用 FAISS 進行向量存儲和檢索。

### 6.1 向量存儲

*   **存儲位置**: `data/` 文件夾
    *   `faiss_index.bin`: FAISS 索引文件
    *   `metadata.json`: 元數據文件
*   **支持的索引類型**: IndexFlatL2, IndexFlatIP, IndexIVFFlat, IndexHNSWFlat

### 6.2 索引流程

1.  文件掃描 → 內容解析 → 文本分塊 → 向量化 → 存儲
2.  實時進度通過 SSE 推送到前端

### 6.3 索引 API

*   `POST /api/index_folder`: 建立索引（SSE 流式返回進度）
*   `POST /api/clear_index`: 清除所有索引
*   `GET /api/indexed_folders`: 獲取已索引的文件夾列表

### 6.4 搜索 API

*   `POST /api/vector_search`: 向量語義搜索
*   `GET /api/search`: Everything 關鍵詞搜索

## 7. 測試腳本

*   **`test/test_llm.py`**: LLM 模型測試脚本，直接調用 LocalLLM 測試提示詞
*   **`test/test_embedding.py`**: 嵌入模型測試
*   **`test/test_faiss.py`**: FAISS 向量存儲測試

運行測試：
```powershell
backend\venv\Scripts\python backend/test/test_llm.py
```
