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

### 方式一：使用批处理脚本（推荐）

项目提供了三个批处理脚本，简化安装和启动流程：

1. **`init.bat`** - 初始化项目（检查环境、安装前端依赖、创建 Python 虚拟环境、安装后端依赖）
2. **`init_models.bat`** - 下载 AI 模型（嵌入模型或 LLM 模型）
3. **`start_app.bat`** - 启动应用（前端开发服务器 + 后端应用）

**操作步骤**：
```bash
# 1. 初始化项目（首次运行）
init.bat

# 2. 下载模型（首次运行）
init_models.bat

# 3. 启动应用
start_app.bat
```

**脚本详细说明**：

#### `init.bat` - 项目初始化
- **功能**：检查 Node.js/Python 环境 → 安装前端依赖 → 创建 Python 虚拟环境 → 安装后端依赖
- **镜像源**：自动使用清华大学镜像源加速下载
- **耗时**：首次运行可能需要 5-30 分钟（取决于网络和电脑性能）

#### `init_models.bat` - 模型下载
- **功能**：下载 AI 模型（嵌入模型或 LLM 模型）
- **模型选择**：
  - 嵌入模型：推荐 `bge-small-zh-v1.5`（体积小，适合新手）
  - LLM 模型：推荐 `qwen2:1.5b`（需 2GB+ 磁盘空间）

#### `start_app.bat` - 启动应用
- **功能**：启动前端开发服务器（新窗口）→ 等待 5 秒 → 启动后端应用
- **说明**：前端在新命令窗口运行，后端在主窗口运行
- **退出**：关闭后端窗口或按 Ctrl+C 停止应用

**注意事项**：
- 如果 `init.bat` 失败，请查看错误信息，通常是网络问题或环境缺失
- 如果 `init_models.bat` 下载失败，可以手动从 HuggingFace 下载模型放到 `models/` 目录
- 如果 `start_app.bat` 启动失败，请检查前端是否已启动（`http://localhost:5173`）

---


### 方式二：手动安装

#### 1. 环境准备

- **Node.js 16+** (前端)
- **Python 3.10+** (后端)

#### 2. 安装依赖

**前端** (终端 1):
```bash
cd frontend
npm install
npm run dev  # 启动 Vite 开发服务器 (http://localhost:5173)
```

> **重要**: 保持此终端运行，不要关闭。桌面应用需要连接此开发服务器。

**后端** (终端 2):
```bash
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows PowerShell
pip install -r requirements.txt
```

#### 3. 下载模型

后端需要嵌入模型才能工作。首次运行前需下载模型：

```bash
# 在后端终端中（保持虚拟环境激活）
python download_model.py
```

- 选择 `1` (嵌入模型)
- 推荐选择 `1` (BAAI/bge-small-zh-v1.5) - 适合新手，体积小
- 等待下载完成（可能需要几分钟，取决于网络速度）

> **注意**: 如果下载失败，请检查网络连接。如需使用代理，请配置 `HF_ENDPOINT` 环境变量。

#### 4. 启动应用

```bash
# 在后端终端中（保持虚拟环境激活）
python gui/main.py
```

这将启动：
- 后端 API 服务器（http://127.0.0.1:8000）
- PyQt6 桌面应用窗口

#### 5. 验证安装

1. 桌面应用窗口应自动打开
2. 在设置页面确认嵌入模型已加载（显示模型名称）
3. 尝试建立索引：选择一个文件夹，点击"建立索引"

---

## 💻 GPU 加速配置（可选）

默认安装的 PyTorch 是 CUDA 12.1 版本。如果您有 NVIDIA GPU 且已安装 CUDA Toolkit 12.1+，将自动启用 GPU 加速。

### 检查 GPU 状态

```bash
# 在后端虚拟环境中运行
python -c "import torch; print('CUDA available:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'None')"
```

如果显示 `CUDA available: False`，可能原因：
- 未安装 NVIDIA 驱动
- 未安装 CUDA Toolkit 12.1+
- 或您使用的是 CPU 版本 Windows

### 安装 CUDA Toolkit（如需要）

访问 [NVIDIA CUDA Toolkit 下载页面](https://developer.nvidia.com/cuda-toolkit-archive) 下载并安装 CUDA 12.1。

安装完成后，重启电脑，再次运行检查命令。

### 切换到 CPU 版本（如需要）

如果您的电脑没有 NVIDIA GPU，可以切换到 CPU 版本：

```bash
# 在后端目录中运行
.\venv\Scripts\activate
pip uninstall torch torchvision torchaudio -y
pip install torch torchvision torchaudio
```

> **注意**: CPU 版本运行速度较慢，但兼容所有电脑。

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


## 🐛 故障排除

### 安装与启动问题

**1. `init.bat` 运行失败**
- **问题**：pip 安装依赖失败（SSL 错误、代理错误等）
- **解决**：
  - 尝试不使用代理（选择 `N`）
  - 或检查代理地址是否正确（如 `http://127.0.0.1:7890`）
  - 或手动安装：进入 `backend` 目录，运行 `venv\Scripts\python.exe -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`

**2. `init_models.bat` 或 `python download_model.py` 下载模型失败**
- **问题**：无法从 HuggingFace 下载模型
- **解决**：
  - 检查网络连接
  - 使用代理（运行 `init_models.bat` 时选择 `Y` 并输入代理地址）
  - 或手动下载：从 [HuggingFace](https://huggingface.co) 下载模型，放到 `models/embedding/` 或 `models/LLM/` 目录

**3. `start_app.bat` 启动失败或前端空白**
- **问题**：后端启动失败或前端无法加载
- **解决**：
  - 检查前端是否启动（`http://localhost:5173`）
  - 查看后端错误信息
  - 或手动启动：进入 `backend` 目录，运行 `venv\Scripts\python.exe gui/main.py`

### 运行时问题

**4. 模型加载失败**
- 确认模型文件在 `models/embedding/` 或 `models/LLM/` 目录
- 检查模型完整性（推荐使用 `safetensors` 格式）
- 确认内存充足（建议 8GB+）
- 查看后端日志中的具体错误信息

**5. GPU 未启用**
- 参考 [GPU 加速配置](#-gpu-加速配置可选) 部分
- 确认安装了 CUDA 版本的 PyTorch
- 运行 `python -c "import torch; print(torch.cuda.is_available())"` 检查


---

## 💻 技术栈

### 前端
- React 19 + TypeScript
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

## 📚 文档

- **[开发指南](DEVELOP.md)** - 项目架构与开发说明
- **[后端开发指南](backend/DEVELOPMENT.md)** - Python 后端开发说明
- **[RAG 模块文档](backend/RAG/DEVELOPMENT.md)** - RAG 核心模块详细说明
- **[文件处理文档](backend/process/ProcessDocs.md)** - 文件处理模块详细说明

---

## 🤝 参考与致谢

本项目参考或借鉴了以下开源项目：

| 项目 | 描述 | 许可证 |
|------|------|--------|
| [semantra](https://github.com/freedmand/semantra) | 多功能语义搜索工具，支持本地文本和PDF文件的语义搜索 | MIT |
| [SearchAnything](https://github.com/kaijiezhu11/SearchAnything) | 基于 AI 模型的本地语义搜索引擎，支持文本和图像搜索 | MIT |
| [everything-ai-chat](https://github.com/MaskerPRC/everything-ai-chat) | 现代化 Everything 搜索客户端，结合 AI 智能与极速本地搜索 | - |

感谢这些优秀的开源项目提供的灵感与参考！
