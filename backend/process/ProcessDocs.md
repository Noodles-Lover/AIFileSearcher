# 文件处理模块开发文档

该文件夹 (`backend/process/`) 包含了文件内容解析、分块、描述生成及存储的相关逻辑。

## 文件结构与作用

### 1. 核心基类

*   **BaseFileProcessor.py**
    *   **作用**: 文件处理器基类，定义统一接口。
    *   **关键方法**:
        *   `get_text()`: 获取解析后的文本（抽象方法，子类实现）
        *   `vectorize_and_store()`: 向量化并存储到向量数据库
        *   `_get_file_info()`: 获取文件基本信息

*   **FileProcessor.py**
    *   **作用**: 文件处理器调度器，根据处理模式和文件扩展名选择合适的处理器。
    *   **处理模式** (ProcessingMode):
        *   `TEXT_CHUNK`: 文本分块模式 - 直接分块存储，不调用 LLM
        *   `SEMI_STRUCTURED`: 半结构化描述模式 - 使用 LLM 生成内容描述
        *   `BINARY`: 二进制描述模式 - 根据文件名和目录结构生成功能描述

### 2. 三种处理器实现

*   **text_chunk/TextChunkProcessor.py**
    *   **作用**: 文本分块处理器，使用分块策略将文件内容分块，不调用 LLM。
    *   **继承**: `BaseFileProcessor`
    *   **解析器映射**: 根据文件扩展名自动选择对应的解析器

*   **semi_structured/SemiStructuredProcessor.py**
    *   **作用**: 半结构化描述处理器，解析文件内容并使用 LLM 生成描述。
    *   **继承**: `BaseFileProcessor`

*   **binary/BinaryProcessor.py**
    *   **作用**: 二进制描述处理器，基于文件名和文件目录结构，使用 LLM 生成文件功能描述。
    *   **继承**: `BaseFileProcessor`

### 3. 分块策略（策略模式）

*   **text_chunk/ChunkingStrategy.py**
    *   **作用**: 分块策略接口及具体实现（Strategy Pattern）。
    *   **主要类**:
        *   `ChunkingStrategy` (抽象基类)
        *   `FixedSizeChunking`: 固定字符数分块
        *   `ParagraphChunking`: 按段落分块
        *   `SentenceChunking`: 按句子分块
        *   `SlidingWindowChunking`: 滑动窗口重叠分块
    *   **DEFAULT_STRATEGIES**: 不同文件类型的默认分块策略映射

### 4. 具体解析器（继承 TextChunkProcessor）

每个文件对应一种文件格式的解析器，直接继承 `TextChunkProcessor`。

| 解析器 | 文件类型 | 说明 |
|--------|---------|------|
| TXTParser.py | .txt | 纯文本文件解析 |
| MDParser.py | .md | Markdown 文件解析 |
| PDFParser.py | .pdf | PDF 文件解析（含表格预处理） |
| DocParser.py | .doc, .docx | Word 文件解析 |
| PPTParser.py | .pptx, .ppt | PowerPoint 文件解析 |
| ImageParser.py | .png, .jpg, .jpeg | 图片文件 OCR 解析 |
| MDSemanticChunking.py | .md | Markdown 语义分块（按标题层级） |
| SlideChunking.py | .pptx, .ppt | PPT 幻灯片分块 |

## 模块互动流程

1.  **外部调用**: API 层 (如 `api/index.py`) 初始化 `FileProcessor` 并调用 `process_file(path, processing_mode)`。
2.  **自动选择处理器**: `FileProcessor` 根据 `processing_mode` 和文件扩展名自动选择对应的处理器。
3.  **文本分块模式**:
    *   根据文件扩展名从 `TextChunkProcessor.PARSER_MAPPING` 选择对应的 Parser
    *   Parser 调用 `get_text()` 返回分块后的文本列表
4.  **描述模式**:
    *   创建 `SemiStructuredProcessor` 或 `BinaryProcessor`
    *   调用 LLM 生成描述
5.  **返回**: 返回包含处理结果的字典。

## 默认分块策略

```python
DEFAULT_STRATEGIES = {
    '.md': ParagraphChunking(),       # 段落分块
    '.txt': ParagraphChunking(),      # 段落分块
    '.docx': SlidingWindowChunking(), # 滑动窗口分块
    '.doc': SlidingWindowChunking(),   # 滑动窗口分块
    '.pdf': SentenceChunking(),        # 句子分块
    '.pptx': SlideChunking(),         # 幻灯片分块
    '.ppt': SlideChunking(),          # 幻灯片分块
}
```

## 开发指南

### 添加新文件格式支持

1. 新建 `XXXParser.py` 继承 `TextChunkProcessor`。
2. 实现 `_extract_content()` 方法提取文件文本。
3. 在 `FileProcessor.EXTENSION_PROCESSOR` 中注册扩展名映射。

### 添加新分块策略

1. 在 `ChunkingStrategy.py` 中新建类继承 `ChunkingStrategy`。
2. 实现 `chunk(text)` 方法。
3. 在 `ChunkingStrategy.DEFAULT_STRATEGIES` 中添加映射。

### 添加新处理模式

1. 在 `ProcessingMode` 中添加新枚举值。
2. 新建处理器类继承 `BaseFileProcessor`。
3. 在 `FileProcessor.process_file()` 中添加对应的处理逻辑。
4. 在处理器类的 `PARSER_MAPPING` 中定义支持的扩展名。
