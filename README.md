# AI 文件搜索器 (AI File Searcher)

这是一个基于人工智能的桌面文件搜索应用，结合了 React 前端、Python (FastAPI + PyQt6) 后端和向量搜索技术。

## 🌟 主要功能

- **文件名搜索**：基于 Everything 引擎的快速文件名搜索
- **语义搜索**：使用向量嵌入模型进行智能内容搜索
- **多格式支持**：支持 PDF、DOCX、PPTX、TXT、MD、图片、二进制文件等
- **实时进度反馈**：建立索引时提供实时进度显示（SSE流式输出）
- **本地模型支持**：支持加载本地嵌入模型（ BGE-M3）和 LLM 模型（Qwen, Phi）
- **智能缓存管理**：避免重复处理未修改文件，提高索引效率
- **模型热切换**：支持在设置页面切换嵌入模型和 LLM 模型
- **空间管理**：提供索引和缓存的清理功能

## 📁 项目结构

```
AIFileSearcher/
├── frontend/                 # React 前端项目
│   ├── src/
│   │   ├── pages/           # 页面组件
│   │   │   ├── Home.tsx     # 主页面（搜索和索引）
│   │   │   └── Settings.tsx # 设置页面
│   │   └── components/      # 通用组件
│   └── package.json
├── backend/                  # Python 后端
│   ├── api/                 # HTTP 接口层
│   │   ├── index.py         # 索引接口（SSE流式输出）
│   │   ├── search.py        # 搜索接口
│   │   ├── files.py         # 文件操作接口
│   │   ├── llm.py           # LLM 模型管理接口
│   │   └── server.py        # FastAPI 服务器
│   ├── gui/                 # 桌面 GUI (PyQt6)
│   │   └── main.py          # 主窗口启动
│   ├── RAG/                 # RAG 核心模块
│   │   ├── SystemManager.py # 系统管理器（单例模式）
│   │   ├── EmbeddingModel.py # 嵌入模型封装
│   │   ├── LocalLLM.py       # 本地 LLM 封装
│   │   ├── VectorStore.py   # FAISS 向量存储
│   │   └── FileCache.py     # 文件缓存管理
│   ├── process/             # 文件处理模块
│   │   ├── FileProcessor.py # 文件处理器调度器
│   │   ├── BaseFileProcessor.py # 处理基类
│   │   ├── text_chunk/      # 文本分块处理器
│   │   ├── semi_structured/ # 半结构化描述处理器
│   │   └── binary/          # 二进制文件处理器
│   └── test/                # 测试脚本
├── models/                   # 本地模型存储
│   ├── embedding/            # 嵌入模型（如 bge-m3）
│   └── LLM/                 # LLM 模型（如 Qwen2.5-3B-Instruct）
├── data/                     # 向量数据库和缓存
│   ├── faiss_index.bin      # FAISS 向量索引
│   ├── metadata.json        # 向量元数据
│   └── file_cache.json      # 文件修改时间缓存
├── references/               # 参考代码
├── testFiles/               # 测试文件
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

## 🎯 使用指南

### 建立索引
1. 点击"建立索引"按钮
2. 选择要索引的文件夹
3. 观察实时进度反馈
4. 等待索引完成

### 文件名搜索
1. 切换到"文件名"模式
2. 输入搜索关键词
3. 点击"搜索"按钮

### 语义搜索
1. 切换到"语义"模式
2. 输入语义关键词（如"人工智能"）
3. 点击"搜索"按钮

### 切换模型
1. 进入设置页面
2. 选择嵌入模型或 LLM 模型
3. 模型将自动加载并生效

### 空间管理
1. 进入设置页面
2. 查看当前索引和缓存大小
3. 点击"清理索引"或"清理缓存"

## 🔧 核心特性

### 文件处理模式
- **文本分块 (TEXT_CHUNK)**：直接分块存储，不调用 LLM
- **半结构化描述 (SEMI_STRUCTURED)**：使用 LLM 生成内容描述
- **二进制描述 (BINARY)**：根据文件名和目录结构生成功能描述

### 实时进度反馈
- 使用 **SSE (Server-Sent Events)** 实现真正的流式输出
- 每个文件处理完成后立即更新进度
- 支持错误、跳过、完成等多种状态反馈

### 智能缓存管理
- 基于**文件修改时间**的智能缓存
- 避免重复处理未修改文件
- 支持增量索引和缓存清理

### 模型管理
- **嵌入模型**：支持 BGE-M3 等多语言模型
- **LLM 模型**：支持 Qwen、Phi 等本地 LLM
- **热切换**：在设置页面实时切换模型

## 📚 文档

- **[RAG 模块文档](backend/RAG/DEVELOPMENT.md)** - RAG 核心模块详细说明
- **[文件处理文档](backend/process/ProcessDocs.md)** - 文件处理模块详细说明
- **[测试脚本说明](backend/test/TESTSCRIPTS.md)** - 测试脚本使用说明

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

### 性能优化

- **大文件处理**：建议分批索引
- **内存管理**：定期清理缓存
- **磁盘空间**：确保 `data/` 目录有足够空间

## 🔄 开发指南

### 添加新文件格式支持
1. 在 `process/text_chunk/` 创建 `XXXParser.py` 继承 `TextChunkProcessor`
2. 在 `TextChunkProcessor.PARSER_MAPPING` 注册扩展名
3. 添加相应的测试用例

### 自定义嵌入模型
1. 将模型放入 `models/embedding/` 目录
2. 在设置页面选择新模型
3. 测试模型兼容性
