# AI 文件搜索器 (AI File Searcher)

这是一个基于人工智能的桌面文件搜索应用，结合了 React 前端、Python (FastAPI + PyQt6) 后端和向量搜索技术。

## 主要功能

- **文件名搜索**：基于 Everything 引擎的快速文件名搜索
- **语义搜索**：使用向量嵌入模型进行智能内容搜索
- **多格式支持**：支持 PDF、DOCX、PPTX、TXT、MD 等多种文件格式的索引和搜索
- **实时进度反馈**：建立索引时提供实时进度显示
- **本地模型支持**：支持加载本地嵌入模型（如 BGE-M3），无需联网

## 项目结构

- `frontend/`: React 前端项目 (使用 Vite + TypeScript)
- `backend/`: Python 后端
    - `api/`: HTTP 接口层，处理前端请求
    - `gui/`: 桌面窗口创建和 Web 界面加载 (使用 PyQt6)
    - `core/`: 系统核心组件管理（单例模式）
    - `embedding/`: 向量嵌入模型和 FAISS 向量存储
    - `process/`: 文件内容解析、清洗和分块
    - `utils/`: 工具函数（如图标提取）
    - `test/`: 测试脚本和测试数据
- `models/`: 本地嵌入模型存储目录
- `data/`: 向量数据库存储目录
- `references/`: 参考代码目录
- `testFiles/`: 测试文件目录

## 快速开始

### 1. 环境准备

确保已安装以下依赖：
- Node.js (用于前端)
- Python 3.10+ (用于后端)
- Everything (用于文件名搜索，可选)

### 2. 启动前端开发服务器

进入 `frontend` 目录并启动 Vite 开发服务器：

```bash
cd frontend
npm install
npm run dev
```

### 3. 启动后端服务

进入 `backend` 目录，激活虚拟环境并运行：

```bash
cd backend
# 激活虚拟环境 (Windows)
venv\Scripts\activate
# 运行 GUI
python gui/main.py
```

## 技术栈

### 前端
- React 18
- TypeScript
- Vite
- Ant Design
- React Router

### 后端
- Python 3.10+
- FastAPI
- PyQt6 (桌面 GUI)
- SentenceTransformers (向量嵌入)
- FAISS (向量搜索)
- PyMuPDF (PDF 解析)
- python-docx (DOCX 解析)
- python-pptx (PPTX 解析)

### 核心功能实现
- **模板方法模式**：文件解析器基类设计
- **策略模式**：分块策略实现
- **单例模式**：系统组件管理
- **SSE (Server-Sent Events)**：实时进度反馈

## 使用说明

### 建立索引
1. 点击"建立索引"按钮
2. 选择要索引的文件夹
3. 等待索引完成（会显示实时进度）

### 文件名搜索
1. 切换到"文件名"模式
2. 输入搜索关键词
3. 点击"搜索"按钮

### 语义搜索
1. 切换到"语义"模式
2. 输入语义关键词（如"人工智能"）
3. 点击"搜索"按钮

## 开发文档

- [后端开发指南](backend/DEVELOPMENT.md)
- [内容处理模块文档](backend/process/ProcessDocs.md)

## 注意事项

- 首次使用需要建立索引
- 语义搜索需要先建立向量索引
- 本地模型需要放在 `models/` 目录下
- 向量数据库存储在 `data/` 目录下
