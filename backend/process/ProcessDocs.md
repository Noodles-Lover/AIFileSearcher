# 內容處理模塊開發文檔

該文件夾 (`backend/process/`) 包含了文件內容解析、清洗、分塊以及存儲的相關邏輯。

## 文件結構與作用

### 1. 核心接口與基類

*   **[BaseParser.py](file:///d:/_Programming/CompleteProjects/AIFileSearcher/backend/process/BaseParser.py)**
    *   **作用**: 定義了所有解析器的基類。
    *   **設計模式**:
        *   **模板方法模式 (Template Method)**: `process()` 方法定義了解析流程的骨架（檢查格式 -> 提取內容 -> 清洗內容 -> 分塊）。具體步驟由子類實現。
        *   **策略模式 (Strategy Pattern)**: 使用 `ChunkingStrategy` 來執行分塊邏輯，允許動態更換分塊算法。
    *   **關鍵方法**: `process()`, `_extract_content()`, `_extract_metadata()`.

*   **[ChunkingStrategy.py](file:///d:/_Programming/CompleteProjects/AIFileSearcher/backend/process/ChunkingStrategy.py)**
    *   **作用**: 定義分塊策略接口及具體實現。
    *   **主要類**:
        *   `ChunkingStrategy` (抽象基類)
        *   `FixedSizeChunking`: 固定字符數分塊 (適用於 PDF, DOCX 等結構複雜文件)。
        *   `ParagraphChunking`: 按段落分塊 (適用於 Markdown)。
        *   `SentenceChunking`: 按句子分塊 (需進一步完善 NLP 支持)。

*   **[FileProcessor.py](file:///d:/_Programming/CompleteProjects/AIFileSearcher/backend/process/FileProcessor.py)**
    *   **作用**: 統一入口（Facade / Dispatcher）。負責根據文件類型選擇合適的 Parser 和 ChunkingStrategy。
    *   **功能**:
        *   註冊支持的 Parser (`PARSERS` 字典)。
        *   配置不同文件類型的默認分塊策略 (`type_strategies`)。
        *   提供 `process_file(path)` 接口供外部調用。

### 2. 具體解析器 (Concrete Parsers)

每個文件對應一種文件格式的解析邏輯，繼承自 `BaseParser`。

*   **[TXTParser.py](file:///d:/_Programming/CompleteProjects/AIFileSearcher/backend/process/TXTParser.py)**: 處理 `.txt` 文件。簡單讀取，忽略編碼錯誤。
*   **[MDParser.py](file:///d:/_Programming/CompleteProjects/AIFileSearcher/backend/process/MDParser.py)**: 處理 `.md` 文件。類似 TXT，但未來可擴展 Frontmatter 解析。
*   **[PDFParser.py](file:///d:/_Programming/CompleteProjects/AIFileSearcher/backend/process/PDFParser.py)**: 處理 `.pdf` 文件。依賴 `PyMuPDF (fitz)` 提取文本和元數據。
*   **[DocxParser.py](file:///d:/_Programming/CompleteProjects/AIFileSearcher/backend/process/DocxParser.py)**: 處理 `.docx` 文件。依賴 `python-docx`。
*   **[PPTParser.py](file:///d:/_Programming/CompleteProjects/AIFileSearcher/backend/process/PPTParser.py)**: 處理 `.pptx` 文件。依賴 `python-pptx`。

## 模塊互動流程

1.  **外部調用**: API 層 (如 `api/files.py`) 初始化 `FileProcessor` 並調用 `process_file(path)`。
2.  **分發 (Dispatch)**: `FileProcessor` 根據文件後綴名 (e.g., `.pdf`) 找到對應的 `PDFParser` 類，並獲取該類型的推薦分塊策略 (e.g., `FixedSizeChunking`)。
3.  **實例化**: 創建 `PDFParser` 實例，注入分塊策略。
4.  **執行 (Execution)**: 調用 `parser.process()`。
    *   `PDFParser` 讀取文件內容。
    *   `BaseParser` 調用注入的 `FixedSizeChunking` 將內容切分為 Chunks。
5.  **返回**: 返回包含 metadata, content, chunks 的字典。

## 開發指南

*   **添加新格式支持**:
    1.  新建 `XXXParser.py` 繼承 `BaseParser`。
    2.  實現 `_extract_content` 和 `_check_format`。
    3.  在 `FileProcessor.py` 的 `PARSERS` 中註冊。
    
*   **添加新分塊策略**:
    1.  在 `ChunkingStrategy.py` 中新建類繼承 `ChunkingStrategy`。
    2.  實現 `chunk(text)` 方法。
