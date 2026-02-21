from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os
import subprocess
import base64
from api.everything import EverythingClient
from api.icons import icon_manager
from process.processor import ContentProcessor

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
processor = ContentProcessor()

@app.get("/")
def read_root():
    return {"status": "ok", "message": "AI File Searcher Backend is running"}


@app.get("/api/icon")
async def get_icon(path: str):
    """
    獲取系統圖標
    """
    try:
        base64_data = icon_manager.get_icon_base64(path)
        if not base64_data:
            raise HTTPException(status_code=404, detail="Icon not found")
        
        # 解碼 base64 並返回圖片流
        img_data = base64.b64decode(base64_data)
        return Response(content=img_data, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/preview")
def preview_file(path: str):
    """
    預覽文件內容 (僅開發用)
    """
    try:
        # 只讀取前 10 個 chunk
        result = processor.process_file(path)
        
        if result.get("error"):
            # 返回 200，前端判斷 error 字段
            return {"error": result.get("error")}

        chunks = result.get("chunks", [])
        strategy = result.get("strategy", "Unknown")
        
        preview_content = f"Chunking Strategy: {strategy}\n"
        preview_content += f"Total Chunks: {len(chunks)}\n\n"
        
        # Format first 10 chunks
        formatted_chunks = []
        for i, chunk in enumerate(chunks[:10]):
            formatted_chunks.append(f"=== Chunk {i+1} ===\n{chunk}")
            
        preview_content += "\n\n==============\n\n".join(formatted_chunks)
        
        if len(chunks) > 10:
            preview_content += "\n\n... (更多內容已省略)"

        return {
            "content": preview_content,
            "meta": result.get("metadata", {}),
            "type": result.get("type", "")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/search")
def search_files(q: str = "", count: int = 100, parent_path: str = None):
    """
    搜索文件
    """
    query = q
    if parent_path:
        # 如果提供了父目錄，限制在該目錄下搜索
        query = f'parent:"{parent_path}" {q}'.strip()
    
    results = client.search(query, count=count)
    
    if results == "CONNECTION_ERROR":
         raise HTTPException(
             status_code=503, 
             detail="無法連接到 Everything 伺服器。請確保 Everything 正在運行並已啟用 HTTP 伺服器（工具 -> 選項 -> HTTP 伺服器）。"
         )
        
    return {"results": results}

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

@app.get("/api/open-file")
def open_file(path: str):
    """
    使用系统默认程序打开文件或文件夹
    """
    try:
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 使用 os.startfile 在 Windows 上打开
        os.startfile(path)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/open-folder")
def open_folder(path: str):
    """
    在资源管理器中定位并选中文件
    """
    try:
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail="路径不存在")
        
        # 使用 explorer /select, 可以在资源管理器中打开并选中该文件/文件夹
        subprocess.run(['explorer', '/select,', os.path.normpath(path)])
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/list")
def list_files(path: str):
    """
    列出指定目錄下的文件
    """
    results = client.get_files_in_folder(path)
    
    if results == "CONNECTION_ERROR":
        raise HTTPException(
            status_code=503, 
            detail="無法連接到 Everything 伺服器。請確保 Everything 正在運行並已啟用 HTTP 伺服器。"
        )
        
    return {"results": results}

if __name__ == "__main__":
    import uvicorn
    # 允许外部访问，端口 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
