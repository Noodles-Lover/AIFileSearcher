# AI 文件搜索器 (AI File Searcher)

<div align="center">

基于人工智能的桌面文件搜索应用，支持语义搜索、多格式文件索引和智能检索。

[功能特性](#-功能特性) • [快速开始](#-快速开始) • [技术栈](#-技术栈) • [文档](#-文档)

</div>

---

## 🌟 功能特性

### 核心功能
- **🧠 语义搜索**：基于向量嵌入模型，理解查询意图，返回最相关的文件
- **📁 多格式支持**：PDF、DOCX、PPTX、TXT、MD、Excel、图片等
- **🖥️ 桌面应用**：基于 PyQt6 的原生桌面体验，无需浏览器
- **⚡ GPU 加速**：自动检测 NVIDIA GPU，加速向量化和推理

### 智能特性
- **🔄 智能缓存**：基于文件修改时间，避免重复处理未修改文件
- **🔀 模型热切换**：在设置页面随时切换嵌入模型和 LLM 模型
- **📊 实时进度**：建立索引时提供实时进度显示（SSE 流式输出）
- **🎯 LLM 查询重写**：智能解析自然语言查询，自动提取文件类型、时间范围等约束

---

## 🚀 快速开始

### 1. 环境准备

- **Node.js 16+** (前端)
- **Python 3.10+** (后端)
- **Everything** (可选，用于文件名搜索)

### 2. 安装依赖

```bash
# 前端
cd frontend && npm install

# 后端
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. 启动应用

```bash
# 启动后端（桌面应用入口）
cd backend
.\venv\Scripts\Activate.ps1
python gui/main.py
```

前端会在桌面应用中自动加载，无需单独启动。

---

## 💻 技术栈

### 前端
- React 18 + TypeScript
- Vite (构建工具)
- Ant Design (UI 组件库)

### 后端
- Python 3.10+ / FastAPI
- PyQt6 (桌面 GUI)
- SentenceTransformers (向量嵌入)
- FAISS (向量搜索)
- Transformers (LLM 推理)

### 文件处理
- PyMuPDF (PDF 解析)
- python-docx (Word 解析)
- python-pptx (PPT 解析)
- openpyxl (Excel 解析)

---

## 🔧 核心特性

### 智能语义搜索

系统使用向量嵌入模型将文件内容转换为向量，通过计算相似度实现语义搜索：

- **自然语言查询**：支持"最近修改的 PDF 关于神经网络"这类复杂查询
- **LLM 查询重写**：自动解析查询中的文件类型、时间范围、大小约束
- **多源搜索**：结合向量搜索和 Everything 文件名搜索

### 分块策略

系统支持多种分块算法，按文件类型自动选择：
- **段落分块**：按段落/换行分块（TXT, MD)
- **滑动窗口**：重叠分块保持上下文（DOC, DOCX)
- **句子分块**：按句子分块（PDF)
- **语义分块**：按 Markdown 标题层级分块
- **幻灯片分块**：按 PPT 幻灯片分块

### FAISS 索引

支持多种 FAISS 索引类型（可在设置中选择）：
| 索引类型 | 特点 |
|---------|------|
| IndexFlatL2 / IndexFlatIP | 精确搜索 |
| IndexIVFFlat | 聚类加速 |
| IndexHNSWFlat | 图索引（高召回） |
| IndexLSH | 局部敏感哈希 |

### 实时进度与缓存

- **SSE 流式输出**：建立索引时实时显示进度
- **智能缓存**：基于文件修改时间，避免重复处理未修改文件

---

## 📚 文档

- **[开发指南](DEVELOP.md)** - 项目架构与开发说明
- **[后端开发指南](backend/DEVELOPMENT.md)** - Python 后端开发说明
- **[RAG 模块文档](backend/RAG/DEVELOPMENT.md)** - RAG 核心模块详细说明
- **[文件处理文档](backend/process/ProcessDocs.md)** - 文件处理模块详细说明

---

## 🐛 故障排除

### 常见问题

**1. 模型加载失败**
- 确认模型文件在 `models/` 目录
- 检查模型完整性（推荐使用 `safetensors` 格式）
- 确认内存充足（建议 8GB+）

**2. 索引进度不更新**
- 检查后端日志
- 确认 SSE 连接正常
- 重启后端服务

**3. 搜索结果不准确**
- 尝试重新建立索引
- 检查文件是否被正确解析
- 调整搜索关键词

**4. GPU 未启用**
- 确认安装了 CUDA 版本的 PyTorch（非 CPU 版本）
- 运行 `python -c "import torch; print(torch.cuda.is_available())"` 检查
- 如果显示 `False`，需要重新安装 CUDA 版本的 PyTorch

---

## 🤝 参考与致谢

本项目参考或借鉴了以下开源项目：

| 项目 | 描述 | 许可证 |
|------|------|--------|
| [semantra](https://github.com/freedmand/semantra) | 多功能语义搜索工具，支持本地文本和PDF文件的语义搜索 | MIT |
| [SearchAnything](https://github.com/kaijiezhu11/SearchAnything) | 基于 AI 模型的本地语义搜索引擎，支持文本和图像搜索 | MIT |
| [everything-ai-chat](https://github.com/MaskerPRC/everything-ai-chat) | 现代化 Everything 搜索客户端，结合 AI 智能与极速本地搜索 | - |

感谢这些优秀的开源项目提供的灵感与参考！
