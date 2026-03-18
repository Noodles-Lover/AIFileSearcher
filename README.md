# AI 文件搜索器 (AI File Searcher)

这是一个基于人工智能的桌面文件搜索应用，结合了 React 前端、Python (FastAPI + PyQt6) 后端和向量搜索技术。

## 🌟 主要功能

- **文件名搜索**：基于 Everything 引擎的快速文件名搜索
- **语义搜索**：使用向量嵌入模型进行智能内容搜索
- **多格式支持**：支持 PDF、DOCX、PPTX、TXT、MD 等多种文件格式的索引和搜索
- **实时进度反馈**：建立索引时提供实时进度显示（SSE流式输出）
- **本地模型支持**：支持加载本地嵌入模型（如 BGE-M3），无需联网
- **智能缓存管理**：避免重复处理未修改文件，提高索引效率
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
│   │   └── server.py        # FastAPI 服务器
│   ├── gui/                 # 桌面 GUI (PyQt6)
│   │   └── main.py          # 主窗口启动
│   ├── RAG/                 # RAG 核心模块
│   │   ├── SystemManager.py # 系统管理器
│   │   ├── FileCache.py     # 文件缓存管理
│   │   ├── VectorStore.py   # 向量存储管理
│   │   ├── FileProcessor.py # 文件处理器
│   │   └── core.py          # RAG 核心组件
│   ├── process/             # 文件处理模块
│   └── test/                # 测试脚本
├── models/                   # 本地嵌入模型存储
├── data/                     # 向量数据库和缓存
│   ├── faiss_index.bin      # FAISS 向量索引
│   ├── metadata.json        # 向量元数据
│   └── file_cache.json      # 文件修改时间缓存
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
```bash
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
pip install -r requirements.txt
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

### 空间管理
1. 进入设置页面
2. 查看当前索引和缓存大小
3. 点击"清理索引"或"清理缓存"

## 🔧 核心特性

### 实时进度反馈
- 使用 **SSE (Server-Sent Events)** 实现真正的流式输出
- 每个文件处理完成后立即更新进度
- 支持错误、跳过、完成等多种状态反馈

### 智能缓存管理
- 基于**文件修改时间**的智能缓存
- 避免重复处理未修改文件
- 支持增量索引和缓存清理

### 向量搜索优化
- 使用 **FAISS** 进行高效向量检索
- 支持 **BGE-M3** 多语言嵌入模型
- 1024 维向量，支持中英文搜索

## 📚 文档

- **[RAG 模块文档](backend/RAG/README.md)** - 核心搜索模块详细说明
- **[API 文档](backend/api/)** - 接口文档
- **[测试脚本](backend/test/)** - 功能测试

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
1. 在 `FileProcessor.py` 中添加解析器
2. 更新文件类型检测逻辑
3. 添加相应的测试用例

### 自定义嵌入模型
1. 将模型放入 `models/` 目录
2. 更新 `SystemManager.py` 配置
3. 测试模型兼容性


