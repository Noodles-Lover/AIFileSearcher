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
*   **`search.py`**: 搜索功能相關接口。包括調用 Everything 進行搜索 (`/api/search`) 和列出文件 (`/api/list`)。

### `gui/` (桌面 GUI 層)
負責創建桌面窗口，嵌入 Web 界面。
*   **`main.py`**: 桌面應用的入口。啟動後端 FastAPI 線程，創建 PyQt6 `QWebEngineView` 窗口並加載前端頁面。

### `process/` (內容處理層)
負責文件的讀取、解析、清洗和分塊。
*   **`FileProcessor.py`**: 核心處理類。根據文件擴展名調度對應的 Parser 和分塊策略。
*   **`BaseParser.py`**: 所有解析器的抽象基類，定義了模板方法。
*   **`ChunkingStrategy.py`**: 定義分塊策略（如固定大小、按段落、按句子）。
*   **具體解析器**: `TXTParser.py`, `PDFParser.py`, `DocxParser.py`, `PPTParser.py`, `MDParser.py` 等。

### `embedding/` (向量嵌入層)
負責將文本轉換為向量。
*   **`EmbeddingModel.py`**: 通用嵌入模型加載器。支持從項目根目錄的 `models/` 文件夾加載本地模型（如 BGE, Qwen3），也支持從 HuggingFace 在線加載。

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
