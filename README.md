# React + PyQt6 Desktop App Framework

这是一个使用 React 作为前端、Python (PyQt6) 作为 GUI 容器的项目框架。

## 项目结构

- `frontend/`: React 前端项目 (使用 Vite + TypeScript)
- `backend/`: Python 后端
    - `gui/`: 负责创建桌面窗口并加载网页 (使用 PyQt6)
    - `api/`: 负责处理前端请求的业务逻辑 (预留文件夹)

## 快速开始

### 1. 启动前端开发服务器

进入 `frontend` 目录并启动 Vite 开发服务器：

```bash
cd frontend
npm run dev
```

### 2. 启动 Python 桌面窗口

进入 `backend` 目录，激活虚拟环境并运行：

```bash
cd backend
# 激活虚拟环境 (Windows)
.\venv\Scripts\activate
# 运行 GUI
python gui/main.py
```

## 常见问题解答 (FAQ)

### 1. 为什么 `node_modules` 文件夹这么大？
这是现代前端开发的正常现象。`node_modules` 包含了 Vite、React 以及编译 TypeScript 所需的所有工具。虽然文件很多，但它们只存在于开发环境。当你最终“构建”项目时，所有代码会被压缩成极小的几个文件。

### 2. 为什么需要/不需要虚拟环境 (venv)？
虚拟环境是为了防止不同项目之间的 Python 依赖冲突。如果你只有一个项目或者习惯全局管理依赖，可以不使用它。我已经根据建议移除了虚拟环境，现在你可以直接使用系统的 Python 环境。

### 3. 依赖项说明
目前仅安装了运行框架所必需的：
- 前端：`vite`, `react`, `typescript` 等基础开发包。
- 后端：`PyQt6`, `PyQt6-WebEngine`。
