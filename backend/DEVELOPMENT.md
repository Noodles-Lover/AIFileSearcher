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
*   **`server.py`**: 應用的入口文件。負責初始化 FastAPI 應用 (`app`)，配置 CORS，並掛載其他路由模塊 (`include_router`)。
*   **`files.py`**: 文件操作相關接口。包括文件預覽 (`/api/preview`)、打開文件/文件夾 (`/api/open-*`)、獲取圖標 (`/api/icon`) 等。
*   **`search.py`**: 搜索功能相關接口。包括調用 Everything 進行搜索 (`/api/search`)、列出文件 (`/api/list`) 和向量搜索 (`/api/vector_search`)。
*   **`index.py`**: 索引功能相關接口。包括建立文件夾索引 (`/api/index_folder`)，使用 SSE (Server-Sent Events) 提供實時進度反饋。
*   **`everything.py`**: Everything 客戶端封裝，提供與 Everything HTTP 服務器的通信接口。

### `gui/` (桌面 GUI 層)
負責創建桌面窗口，嵌入 Web 界面。
*   **`main.py`**: 桌面應用的入口。啟動後端 FastAPI 線程，創建 PyQt6 `QWebEngineView` 窗口並加載前端頁面。

### `core/` (核心組件層)
負責系統核心組件的管理和初始化。
*   **`SystemManager.py`**: 系統管理器，使用單例模式管理嵌入模型和向量存儲的實例。提供統一的初始化和訪問接口。

### `process/` (內容處理層)
負責文件的讀取、解析、清洗和分塊。
*   **`FileProcessor.py`**: 核心處理類。根據文件擴展名調度對應的 Parser 和分塊策略。
*   **`BaseParser.py`**: 所有解析器的抽象基類，定義了模板方法。
*   **`ChunkingStrategy.py`**: 定義分塊策略（如固定大小、按段落、按句子）。
*   **具體解析器**: `TXTParser.py`, `PDFParser.py`, `DocxParser.py`, `PPTParser.py`, `MDParser.py` 等。

### `embedding/` (向量嵌入層)
負責將文本轉換為向量並進行向量搜索。
*   **`EmbeddingModel.py`**: 通用嵌入模型加載器。支持從項目根目錄的 `models/` 文件夾加載本地模型（如 BGE-M3），也支持從 HuggingFace 在線加載。使用 SentenceTransformers 框架。
*   **`VectorStore.py`**: FAISS 向量存儲封裝。負責向量的存儲、檢索和管理。使用 L2 距離進行相似度計算，支持索引的保存和加載。

### `utils/` (工具層)
通用工具函數。
*   **`icons.py`**: 系統圖標提取工具，利用 PyQt6 獲取文件的原生圖標並轉換為 Base64。

## 3. 嵌入模型 (Embedding Models)

本項目支持加載本地嵌入模型 (如 BGE, Qwen3-Embedding)。

*   **模型存放位置**: 請將模型文件夾放置在項目根目錄的 `models/` 文件夾下。
*   **文件結構示例**:
    ```
    AIFileSearcher/
    ├── models/
    │   ├── bge-small-zh-v1.5/
    │   │   ├── config.json
    │   │   ├── model.safetensors
    │   │   └── ...
    │   └── ...
    ```
*   **代碼調用**:
    ```python
    from embedding.EmbeddingModel import EmbeddingModel
    
    # 自動加載 models/bge-small-zh-v1.5
    embedder = EmbeddingModel("bge-small-zh-v1.5")
    vectors = embedder.encode(["你好", "世界"])
    ```

## 4. 模型下載 (Model Download)

為了方便開發者，我們提供了一個自動下載模型的腳本 `backend/download_model.py`。該腳本會從 HuggingFace 下載完整的模型文件並自動保存到 `models/` 目錄。

### 使用方法

1.  **確保依賴已安裝**:
    ```powershell
    backend\venv\Scripts\pip install huggingface-hub
    ```

2.  **運行下載腳本**:
    ```powershell
    backend\venv\Scripts\python backend/download_model.py
    ```

3.  **選擇模型**:
    腳本運行後，會提示選擇要下載的模型（默認推薦 `BAAI/bge-small-zh-v1.5`），或者你可以輸入自定義的 HuggingFace 模型 ID。

    ```text
    請選擇要下載的模型:
    1. BAAI/bge-small-zh-v1.5
    2. BAAI/bge-large-zh-v1.5
    3. BAAI/bge-m3
    4. Alibaba-NLP/gte-Qwen2-1.5B-instruct
    0. 自定義輸入模型 ID
    ```

4.  **下載完成**:
    模型下載完成後，會自動保存在項目根目錄的 `models/` 文件夾下，之後即可在代碼中直接使用。

## 5. 向量搜索與索引 (Vector Search & Indexing)

本項目使用 FAISS 進行向量存儲和檢索，支持高效的語義搜索。

### 5.1 向量存儲 (Vector Storage)

*   **存儲位置**: 項目根目錄的 `local_data/` 文件夾下
    *   `faiss_index.bin`: FAISS 索引文件
    *   `metadata.json`: 元數據文件（包含文件路徑、內容片段等）
*   **維度自動檢測**: 系統會自動檢測模型的向量維度，無需手動配置
*   **錯誤恢復**: 當索引文件損壞時，系統會自動重建索引

### 5.2 索引流程 (Indexing Workflow)

1.  **文件掃描**: 遍歷指定文件夾，找出支持的文件類型
2.  **內容解析**: 使用對應的 Parser 提取文件內容
3.  **文本分塊**: 根據文件類型選擇合適的分塊策略
4.  **向量化**: 使用嵌入模型將文本塊轉換為向量
5.  **存儲**: 將向量和元數據存儲到 FAISS 索引中

### 5.3 實時進度反饋 (Real-time Progress Feedback)

使用 SSE (Server-Sent Events) 技術實現索引過程的實時進度反饋：

*   **後端實現**: `api/index.py` 中的 `index_folder` 接口
*   **前端實現**: `frontend/src/pages/Home.tsx` 中的 SSE 事件處理
*   **進度事件類型**:
    *   `init`: 初始化系統
    *   `scanning`: 掃描文件
    *   `start`: 開始索引，顯示總文件數
    *   `progress`: 索引進度更新
    *   `complete`: 索引完成
    *   `error`: 錯誤處理

### 5.4 向量搜索 (Vector Search)

*   **搜索接口**: `api/search.py` 中的 `vector_search` 接口
*   **相似度計算**: 使用 L2 距離計算相似度（越小越相似）
*   **結果格式**: 返回包含文件路徑、內容預覽、相似度分數的結果列表
*   **錯誤處理**: 當搜索失敗時自動重建索引

### 5.5 測試 (Testing)

項目提供了測試腳本來驗證向量搜索功能：

*   **`test/test_faiss.py`**: FAISS 向量存儲集成測試
*   **`test/test_embedding.py`**: 嵌入模型測試

運行測試：
```powershell
backend\venv\Scripts\python backend/test/test_faiss.py
```
