# AI 文件搜索器 (AI File Searcher)

这是一个基于人工智能的桌面文件搜索应用，结合了 React 前端、Python (FastAPI + PyQt6) 后端和向量搜索技术。

## 🌟 主要功能

- **语义搜索**：使用向量嵌入模型进行智能内容搜索
- **多格式支持**：支持 PDF、DOCX、PPTX、TXT、MD、图片、二进制文件等
- **实时进度反馈**：建立索引时提供实时进度显示（SSE流式输出）
- **本地模型支持**：支持加载本地嵌入模型（BGE-M3）和 LLM 模型
- **智能缓存管理**：避免重复处理未修改文件，提高索引效率
- **模型热切换**：支持在设置页面切换嵌入模型和 LLM 模型
- **可配置分块策略**：支持多种分块策略（段落、滑动窗口、句子、语义分块等）
- **多种索引类型**：支持 FAISS 多种索引（Flat、IVF、HNSW、LSH等）
- **检索评估框架**：基于 RAGAS 的检索质量评估工具

## 📁 项目结构

```
AIFileSearcher/
├── frontend/                         # React + TypeScript 前端
│   ├── src/
│   │   ├── components/               # 通用组件
│   │   ├── pages/                    # 页面组件
│   │   │   ├── Home.tsx             # 主页面（搜索和索引）
│   │   │   └── Settings.tsx         # 设置页面
│   │   ├── App.tsx                   # 应用入口
│   │   └── main.tsx                  # React 渲染入口
│   ├── package.json
│   └── vite.config.ts                # Vite 配置
│
├── backend/                          # Python 后端
│   ├── api/                         # HTTP 接口层
│   │   ├── index.py                 # 索引接口（SSE流式输出）
│   │   ├── search.py                # 搜索接口
│   │   ├── files.py                 # 文件操作接口
│   │   ├── llm.py                   # LLM 模型管理接口
│   │   └── server.py                # FastAPI 服务器
│   │
│   ├── gui/                          # 桌面 GUI (PyQt6)
│   │   └── main.py                  # 主窗口启动
│   │
│   ├── RAG/                          # RAG 核心模块
│   │   ├── EmbeddingModel.py        # 嵌入模型封装
│   │   ├── VectorStore.py            # FAISS 向量存储
│   │   ├── FileCache.py              # 文件缓存管理
│   │   ├── SystemManager.py          # 系统管理器（单例模式）
│   │   ├── LocalLLM.py               # 本地 LLM 封装
│   │   ├── DeepSeekLLM.py            # DeepSeek API 封装
│   │   └── DEVELOPMENT.md            # RAG 模块开发文档
│   │
│   ├── process/                      # 文件处理模块
│   │   ├── FileProcessor.py          # 文件处理器调度器
│   │   ├── BaseFileProcessor.py       # 处理基类
│   │   ├── text_chunk/               # 文本分块处理器
│   │   │   ├── TextChunkProcessor.py # 文本处理器基类
│   │   │   ├── ChunkingStrategy.py   # 分块策略（策略模式）
│   │   │   │   ├── ParagraphChunking      # 段落分块
│   │   │   │   ├── SlidingWindowChunking  # 滑动窗口分块
│   │   │   │   ├── SentenceChunking        # 句子分块
│   │   │   │   └── FixedSizeChunking      # 固定大小分块
│   │   │   ├── MDSemanticChunking.py      # MD 语义分块
│   │   │   ├── SlideChunking.py            # PPT 幻灯片分块
│   │   │   ├── PDFParser.py               # PDF 解析器
│   │   │   ├── DocParser.py                # DOC/DOCX 解析器
│   │   │   ├── PPTParser.py               # PPT 解析器
│   │   │   ├── MDParser.py                # MD 解析器
│   │   │   ├── TXTParser.py               # TXT 解析器
│   │   │   ├── ImageParser.py             # 图片解析器
│   │   │   └── TablePreprocessor.py       # 表格预处理
│   │   ├── semi_structured/              # 半结构化文件处理
│   │   │   └── SemiStructuredProcessor.py
│   │   ├── binary/                       # 二进制文件处理
│   │   │   └── BinaryProcessor.py
│   │   └── ProcessDocs.md                # 文件处理开发文档
│   │
│   ├── utils/                            # 工具模块
│   │   ├── path_utils.py                 # 路径工具
│   │   ├── search_utils.py               # 搜索工具
│   │   └── IndexedFoldersManager.py      # 索引文件夹管理
│   │
│   ├── test/                             # 测试脚本
│   │   ├── ragas_test/                   # RAG 评估框架
│   │   │   ├── eval_config.py            # 评估配置
│   │   │   ├── eval_reporter.py          # 结果报告
│   │   │   ├── ragas_retrieval_eval.py  # 检索评估脚本
│   │   │   ├── ragas_evaluation.py       # 评估工具
│   │   │   ├── summarize_results.py      # 结果汇总
│   │   │   ├── test_cases.json          # 测试用例
│   │   │   ├── EVAL_GUIDE.md            # 评估指南
│   │   │   └── result/                   # 评估结果
│   │   └── TESTSCRIPTS.md               # 测试脚本说明
│   │
│   ├── DEVELOPMENT.md                    # 后端开发指南
│   └── requirements.txt                   # Python 依赖
│
├── models/                               # 本地模型存储
│   ├── embedding/                        # 嵌入模型
│   │   ├── bge-base-zh-v1.5/
│   │   ├── bge-large-zh-v1.5/
│   │   └── bge-small-zh-v1.5/
│   └── LLM/                              # LLM 模型
│
├── data/                                 # 向量数据库和缓存
│   ├── faiss_index.bin                  # FAISS 向量索引
│   ├── metadata.json                     # 向量元数据
│   └── file_cache.json                  # 文件修改时间缓存
│
├── testFiles/                            # 测试文件
│   ├── mixed/                            # 混合格式测试集（30个文件）
│   ├── txt/                              # TXT 文件测试集
│   ├── md/                               # MD 文件测试集
│   ├── pdf/                              # PDF 文件测试集
│   ├── doc/                              # DOC 文件测试集
│   └── ppt/                              # PPT 文件测试集
│
├── references/                           # 参考代码
└── README.md
```

## 🚀 快速开始

### 1. 环境准备

确保已安装以下依赖：
- **Node.js 16+** (用于前端)
- **Python 3.10+** (用于后端)
- **Everything** (用于文件名搜索，可选)

### 2. 安装依赖

**前端依赖**：
```bash
cd frontend
npm install
```

**后端依赖**：
```powershell
cd backend
venv\Scripts\pip install -r requirements.txt
```

### 3. 启动应用

**方法一：独立启动**
```bash
# 启动前端
cd frontend
npm run dev

# 启动后端 (新窗口)
cd backend
venv\Scripts\activate
python gui/main.py
```

**方法二：桌面应用**
```bash
cd backend
venv\Scripts\activate
python gui/main.py
```

## 💻 技术栈

### 前端
- **React 18** + **TypeScript**
- **Vite** (构建工具)
- **Ant Design** (UI 组件库)
- **React Router** (路由管理)

### 后端
- **Python 3.10+**
- **FastAPI** (Web 框架)
- **PyQt6** (桌面 GUI)
- **SentenceTransformers** (向量嵌入)
- **FAISS** (向量搜索)
- **Transformers** (LLM 推理)
- **SSE** (Server-Sent Events 实时通信)

### 文件处理
- **PyMuPDF** (PDF 解析)
- **python-docx** (DOCX 解析)
- **python-pptx** (PPTX 解析)
- **openpyxl** (Excel 解析)

## 🔧 核心特性

### 分块策略（策略模式）

系统采用**策略模式**实现多种分块算法，可按文件类型自动选择：

```python
# 默认分块策略配置
DEFAULT_STRATEGIES = {
    '.md': ParagraphChunking(),     # 段落分块
    '.txt': ParagraphChunking(),     # 段落分块
    '.docx': SlidingWindowChunking(),  # 滑动窗口
    '.doc': SlidingWindowChunking(),   # 滑动窗口
    '.pdf': SentenceChunking(),        # 句子分块
    '.pptx': SlideChunking(),           # 幻灯片分块
}
```

**支持的分块策略**：
| 策略 | 说明 | 适用场景 |
|------|------|---------|
| ParagraphChunking | 按段落/换行分块 | TXT, MD |
| SlidingWindowChunking | 滑动窗口重叠分块 | DOC, 结构化文档 |
| SentenceChunking | 按句子分块 | PDF |
| FixedSizeChunking | 固定字符数分块 | 通用 |
| MDSemanticChunking | 按 Markdown 标题层级分块 | MD |
| SlideChunking | 按 PPT 幻灯片分块 | PPTX, PPT |

### FAISS 索引类型

支持多种 FAISS 索引类型：

| 索引类型 | 说明 | 特点 |
|---------|------|------|
| IndexFlatL2 | 精确 L2 距离 | 精确但慢 |
| IndexFlatIP | 内积相似度 | 精确但慢 |
| IndexIVFFlat | IVF 聚类加速 | 需训练 |
| IndexHNSWFlat | HNSW 图索引 | 高召回高速 |
| IndexLSH | 局部敏感哈希 | 二值向量 |

### 文件处理模式

- **文本分块 (TEXT_CHUNK)**：直接分块存储，不调用 LLM
- **半结构化描述 (SEMI_STRUCTURED)**：使用 LLM 生成内容描述
- **二进制描述 (BINARY)**：根据文件名和目录结构生成功能描述

### 实时进度反馈

使用 **SSE (Server-Sent Events)** 实现真正的流式输出，每个文件处理完成后立即更新进度。

### 智能缓存管理

基于**文件修改时间**的智能缓存，避免重复处理未修改文件，支持增量索引。

## 📚 文档

- **[后端开发指南](backend/DEVELOPMENT.md)** - Python 后端开发说明
- **[RAG 模块文档](backend/RAG/DEVELOPMENT.md)** - RAG 核心模块详细说明
- **[文件处理文档](backend/process/ProcessDocs.md)** - 文件处理模块详细说明
- **[测试脚本说明](backend/test/TESTSCRIPTS.md)** - 测试脚本使用说明
- **[检索评估指南](backend/test/ragas_test/EVAL_GUIDE.md)** - RAG 检索评估说明

## 🐛 故障排除

### 常见问题

**1. 模型加载失败**
- 确认模型文件在 `models/` 目录
- 检查模型完整性
- 确认内存充足（建议 8GB+）

**2. 索引进度不更新**
- 检查后端日志
- 确认 SSE 连接正常
- 重启后端服务

**3. 搜索结果不准确**
- 尝试重新建立索引
- 检查文件是否被正确解析
- 调整搜索关键词

## 🔄 开发指南

### 添加新文件格式支持

1. 在 `process/text_chunk/` 创建 `XXXParser.py` 继承 `TextChunkProcessor`
2. 在 `FileProcessor.EXTENSION_PROCESSOR` 注册扩展名
3. 在 `ChunkingStrategy.DEFAULT_STRATEGIES` 添加默认分块策略

### 自定义嵌入模型

1. 将模型放入 `models/embedding/` 目录
2. 在设置页面选择新模型
3. 测试模型兼容性
