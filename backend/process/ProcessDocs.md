# 文件處理模塊開發文檔

該文件夾 (`backend/process/`) 包含了文件內容解析、分塊、描述生成及存儲的相關邏輯。

## 文件結構與作用

### 1. 核心基類

*   **[BaseFileProcessor.py](file:///d:/_Programming/CompleteProjects/AIFileSearcher/backend/process/BaseFileProcessor.py)**
    *   **作用**: 文件處理器基類，定義統一接口。
    *   **關鍵方法**:
        *   `get_text()`: 獲取解析後的文本（抽象方法，子類實現）
        *   `vectorize_and_store()`: 向量化並存儲到向量數據庫
        *   `_get_file_info()`: 獲取文件基本信息

*   **[FileProcessor.py](file:///d:/_Programming/CompleteProjects/AIFileSearcher/backend/process/FileProcessor.py)**
    *   **作用**: 文件處理器調度器，根據處理模式選擇合適的處理器。
    *   **處理模式**:
        *   `ProcessingMode.TEXT_CHUNK`: 文本分塊模式
        *   `ProcessingMode.CONTENT_DESCRIPTION`: 內容描述模式（LLM）
        *   `ProcessingMode.FUNCTION_DESCRIPTION`: 功能描述模式（LLM）

### 2. 三種處理器實現

*   **[text_chunk/TextChunkProcessor.py](file:///d:/_Programming/CompleteProjects/AIFileSearcher/backend/process/text_chunk/TextChunkProcessor.py)**
    *   **作用**: 文本分塊處理器，使用分塊策略將文件內容分塊，不調用LLM。
    *   **繼承**: `BaseFileProcessor`
    *   **自動策略選擇**: 根據文件擴展名從 `ChunkingStrategy.DEFAULT_STRATEGIES` 選擇合適的分塊策略。

*   **[content_description/ContentDescriptionProcessor.py](file:///d:/_Programming/CompleteProjects/AIFileSearcher/backend/process/content_description/ContentDescriptionProcessor.py)**
    *   **作用**: 內容描述處理器，解析文件內容並使用LLM生成描述。
    *   **繼承**: `BaseFileProcessor`

*   **[function_description/FunctionDescriptionProcessor.py](file:///d:/_Programming/CompleteProjects/AIFileSearcher/backend/process/function_description/FunctionDescriptionProcessor.py)**
    *   **作用**: 功能描述處理器，基於文件名和文件目錄結構，使用LLM生成文件功能描述。
    *   **繼承**: `BaseFileProcessor`

### 3. 分塊策略

*   **[text_chunk/ChunkingStrategy.py](file:///d:/_Programming/CompleteProjects/AIFileSearcher/backend/process/text_chunk/ChunkingStrategy.py)**
    *   **作用**: 分塊策略接口及具體實現（Strategy Pattern）。
    *   **主要類**:
        *   `ChunkingStrategy` (抽象基類)
        *   `FixedSizeChunking`: 固定字符數分塊
        *   `ParagraphChunking`: 按段落分塊
        *   `SentenceChunking`: 按句子分塊
    *   **DEFAULT_STRATEGIES**: 不同文件類型的默認分塊策略映射

### 4. 具體解析器 (繼承 TextChunkProcessor)

每個文件對應一種文件格式的解析器，直接繼承 `TextChunkProcessor`。

*   **[text_chunk/TXTParser.py](file:///d:/_Programming/CompleteProjects/AIFileSearcher/backend/process/text_chunk/TXTParser.py)**: 處理 `.txt` 文件
*   **[text_chunk/MDParser.py](file:///d:/_Programming/CompleteProjects/AIFileSearcher/backend/process/text_chunk/MDParser.py)**: 處理 `.md` 文件
*   **[text_chunk/PDFParser.py](file:///d:/_Programming/CompleteProjects/AIFileSearcher/backend/process/text_chunk/PDFParser.py)**: 處理 `.pdf` 文件
*   **[text_chunk/DocxParser.py](file:///d:/_Programming/CompleteProjects/AIFileSearcher/backend/process/text_chunk/DocxParser.py)**: 處理 `.docx` 文件
*   **[text_chunk/DocParser.py](file:///d:/_Programming/CompleteProjects/AIFileSearcher/backend/process/text_chunk/DocParser.py)**: 處理 `.doc` 文件
*   **[text_chunk/PPTParser.py](file:///d:/_Programming/CompleteProjects/AIFileSearcher/backend/process/text_chunk/PPTParser.py)**: 處理 `.pptx` 文件
*   **[text_chunk/ImageParser.py](file:///d:/_Programming/CompleteProjects/AIFileSearcher/backend/process/text_chunk/ImageParser.py)**: 處理圖片文件

## 模塊互動流程

1.  **外部調用**: API 層 (如 `api/files.py`) 初始化 `FileProcessor` 並調用 `process_file(path, processing_mode)`。
2.  **分發 (Dispatch)**: `FileProcessor` 根據 `processing_mode` 選擇對應的處理器。
3.  **文本分塊模式**:
    *   根據文件擴展名選擇對應的 Parser（如 `MDParser`）
    *   Parser 繼承 `TextChunkProcessor`，自動選擇合適的分塊策略
    *   調用 `get_text()` 返回分塊後的文本列表
4.  **描述模式**:
    *   創建 `ContentDescriptionProcessor` 或 `FunctionDescriptionProcessor`
    *   調用 LLM 生成描述
5.  **返回**: 返回包含處理結果的字典。

## 開發指南

### 添加新文件格式支持

1.  新建 `XXXParser.py` 繼承 `TextChunkProcessor`。
2.  實現 `_extract_content()` 方法提取文件文本。
3.  在 `FileProcessor.py` 的 `TEXT_PARSERS` 中註冊。

### 添加新分塊策略

1.  在 `ChunkingStrategy.py` 中新建類繼承 `ChunkingStrategy`。
2.  實現 `chunk(text)` 方法。
3.  在 `ChunkingStrategy.DEFAULT_STRATEGIES` 中添加映射。

### 添加新處理模式

1.  在 `ProcessingMode` 中添加新枚舉值。
2.  新建處理器類繼承 `BaseFileProcessor`。
3.  在 `FileProcessor.process_file()` 中添加對應的處理邏輯。
