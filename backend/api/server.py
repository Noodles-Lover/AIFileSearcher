from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os

# 确保能导入 everything 模块
# 如果直接运行此脚本，sys.path 需要包含 backend 目录
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from api.everything import EverythingClient

app = FastAPI(title="AI File Searcher API")

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置为具体的域名，开发环境可以用 *
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化 Everything 客户端
client = EverythingClient()

@app.get("/")
def read_root():
    return {"status": "ok", "message": "AI File Searcher Backend is running"}

import subprocess

# ... (imports)

@app.get("/api/search")
def search_files(q: str, count: int = 100, parent_path: str = None):
    """
    搜索文件
    :param q: 搜索关键词
    :param count: 返回结果数量
    :param parent_path: 限制在指定文件夹内搜索
    """
    try:
        # 如果指定了父目录，修改查询语句
        final_query = q
        if parent_path:
            # Everything 语法: <query> parent:<path>
            # 注意路径如果有空格需要引号
            final_query = f'{q} parent:"{parent_path}"'
            
        results = client.search(final_query, count=count)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/pick-folder")
def pick_folder():
    """
    弹出系统文件夹选择框（通过 PowerShell）
    """
    try:
        # 使用 PowerShell 调用 Windows Forms FolderBrowserDialog
        ps_script = """
        Add-Type -AssemblyName System.Windows.Forms
        $f = New-Object System.Windows.Forms.FolderBrowserDialog
        $f.Description = "请选择一个文件夹进行索引"
        $f.ShowNewFolderButton = $true
        if ($f.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
            $f.SelectedPath
        }
        """
        
        # 运行 PowerShell 命令
        result = subprocess.run(
            ["powershell", "-Command", ps_script], 
            capture_output=True, 
            text=True, 
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        path = result.stdout.strip()
        if path:
            return {"path": path, "cancelled": False}
        else:
            return {"path": None, "cancelled": True}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/list")
# ... (rest of the file)
def list_files(path: str, recursive: bool = False):
    """
    列出指定文件夹下的文件
    :param path: 文件夹路径
    :param recursive: 是否递归
    """
    try:
        results = client.get_files_in_folder(path, recursive=recursive)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # 允许外部访问，端口 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
