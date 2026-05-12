# AIFileSearcher 开发指南

> 本文档面向开发人员，包含项目架构、模块说明和开发指南。
> 用户文档请参考 [README.md](README.md)。

---

## 项目架构

```
AIFileSearcher/
├── frontend/                         # React + TypeScript 前端
│   ├── src/
│   │   ├── components/               # 通用组件
│   │   ├── pages/                   # 页面组件（Home、Settings）
│   │   ├── utils/                   # 前端工具函数
│   │   ├── styles/                  # 样式文件
│   │   └── assets/                 # 静态资源
│   ├── package.json
│   └── vite.config.ts
│
├── backend/                          # Python 后端
│   ├── api/                         # HTTP 接口层
│   │   ├── server.py                # FastAPI 服务器
│   │   ├── search.py                # 搜索接口
│   │   ├── index.py                 # 索引接口（SSE 流式输出）
│   │   ├── files.py                 # 文件操作接口
│   │   └── llm.py                  # LLM 模型管理接口
│   │
│   ├── gui/                         # 桌面 GUI (PyQt6)
│   │   └── main.py                  # 主窗口启动
│   │
│   ├── RAG/                         # RAG 核心模块
│   │   ├── SystemManager.py          # 系统管理器（单例模式）
│   │   ├── EmbeddingModel.py        # 嵌入模型封装（支持 GPU 自动检测）
│   │   ├── VectorStore.py           # FAISS 向量存储
│   │   ├── LocalLLM.py              # 本地 LLM 封装（支持 GPU 加速）
│   │   ├── DeepSeekLLM.py           # DeepSeek API 封装
│   │   └── FileCache.py             # 文件缓存管理
│   │
│   ├── process/                      # 文件处理模块
│   │   ├── FileProcessor.py          # 文件处理器调度器
│   │   ├── BaseFileProcessor.py      # 处理基类
│   │   ├── text_chunk/               # 文本分块处理器
│   │   ├── semi_structured/          # 半结构化文件处理
│   │   └── binary/                   # 二进制文件处理
│   │
│   ├── utils/                        # 工具模块
│   │   ├── search_utils.py           # 搜索工具（LLM 查询重写）
│   │   ├── path_utils.py             # 路径工具
│   │   ├── everything_client.py      # Everything 搜索客户端
│   │   ├── settings_manager.py        # 设置管理器
│   │   ├── model_utils.py            # 模型工具
│   │   └── icons.py                  # 图标工具
│   │
│   └── test/                         # 测试脚本
│       └── ragas_test/               # RAGAS 评估框架（实验性）
│
├── models/                           # 本地模型存储
│   ├── embedding/                    # 嵌入模型（bge 系列）
│   └── LLM/                         # LLM 模型
│
├── local_data/                       # 向量数据库和缓存
│   ├── faiss_index.bin               # FAISS 向量索引
│   ├── metadata.json                 # 向量元数据
│   └── file_cache.json               # 文件修改时间缓存
│
├── testFiles/                        # 测试文件集
├── references/                       # 参考文档
├── README.md                         # 用户文档
└── DEVELOP.md                       # 本文件
```

---

## 核心模块说明

### RAG 模块 (`backend/RAG/`)

| 文件 | 说明 |
|------|------|
| `SystemManager.py` | 系统管理器（单例模式），统一管理各组件 |
| `EmbeddingModel.py` | 嵌入模型封装，支持 GPU 自动检测 |
| `VectorStore.py` | FAISS 向量存储 |
| `LocalLLM.py` | 本地 LLM 封装，支持 GPU 加速 |
| `DeepSeekLLM.py` | DeepSeek API 封装 |
| `FileCache.py` | 文件缓存管理 |

**GPU 加速**：
- 嵌入模型：通过 `torch.cuda.is_available()` 自动检测 GPU
- 本地 LLM：使用 `torch.float16` + `device_map="auto"`

详细文档：`backend/RAG/DEVELOPMENT.md`

### 文件处理模块 (`backend/process/`)

采用**策略模式**实现多种分块算法：

| 策略 | 说明 | 适用文件 |
|------|------|----------|
| `ParagraphChunking` | 按段落/换行分块 | .txt, .md |
| `SlidingWindowChunking` | 滑动窗口（带重叠） | .docx, .doc |
| `SentenceChunking` | 按句子分块 | .pdf |
| `FixedSizeChunking` | 固定字符数分块 | 通用 |
| `MDSemanticChunking` | 按 Markdown 标题层级分块 | .md |
| `SlideChunking` | 按 PPT 幻灯片分块 | .pptx, .ppt |

详细文档：`backend/process/ProcessDocs.md`

### 工具模块 (`backend/utils/`)

| 文件 | 说明 |
|------|------|
| `search_utils.py` | 搜索工具，包含 LLM 查询重写 |
| `path_utils.py` | 路径工具 |
| `everything_client.py` | Everything 搜索客户端 |
| `settings_manager.py` | 设置管理器 |
| `model_utils.py` | 模型工具 |
| `icons.py` | 图标工具 |

---

## 开发指南

### 添加新文件格式支持

1. 在 `backend/process/text_chunk/` 创建解析器（继承 `TextChunkProcessor`）
2. 在 `FileProcessor.EXTENSION_PROCESSOR` 注册扩展名
3. 在 `ChunkingStrategy.DEFAULT_STRATEGIES` 添加默认分块策略

### 自定义嵌入模型

1. 将模型放入 `models/embedding/` 目录（**推荐 `safetensors` 格式**）
2. 在设置页面选择新模型
3. 测试模型兼容性

> ⚠️ **注意**：PyTorch 2.6+ 要求模型使用 `safetensors` 格式，否则会报错。
> 如果只有 `.bin` 格式，需降级 PyTorch 或重新下载 `safetensors` 格式模型。

### GPU 加速配置

**问题：嵌入模型没有使用 GPU**

原因：`torch.cuda.is_available()` 返回 `False`，通常是因为安装了 CPU 版本的 PyTorch。

解决方案：安装 CUDA 版本的 PyTorch

```powershell
# 卸载 CPU 版本
pip uninstall torch torchvision torchaudio -y

# 安装 CUDA 12.1 版本
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

安装后重启后端，应该能看到：`Embedding model using device: cuda`

---

## 测试

### 运行单元测试

```bash
cd backend
venv\Scripts\activate
python -m pytest test/
```

### 系统评估

项目包含自动化的检索质量评估工具（位于 `backend/test/ragas_test/`），可用于评估不同嵌入模型、分块策略、索引类型的检索效果。

```bash
cd backend/test/ragas_test
python ragas_evaluation.py
```

详细文档：`backend/test/ragas_test/EVAL_GUIDE.md`

---

## 技术栈

### 前端
- React 18 + TypeScript
- Vite (构建工具)
- Ant Design (UI 组件库)
- React Router (路由管理)

### 后端
- Python 3.10+
- FastAPI (Web 框架)
- PyQt6 (桌面 GUI)
- SentenceTransformers (向量嵌入)
- FAISS (向量搜索)
- Transformers (LLM 推理)

### 文件处理
- PyMuPDF (PDF 解析)
- python-docx (DOCX 解析)
- python-pptx (PPTX 解析)
- openpyxl (Excel 解析)
