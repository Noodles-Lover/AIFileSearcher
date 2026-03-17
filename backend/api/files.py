from fastapi import APIRouter, HTTPException, Response
import os
import subprocess
import base64
from utils.icons import icon_manager
from process.FileProcessor import FileProcessor

router = APIRouter()

# 初始化處理器
processor = FileProcessor()

@router.get("/api/icon")
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

@router.get("/api/preview")
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

@router.get("/api/pick-folder")
def pick_folder():
    """
    弹出系统文件夹选择框（通过 PowerShell）
    修复中文路径编码问题
    """
    try:
        # 使用 PowerShell 调用 Windows Forms FolderBrowserDialog
        # 添加编码处理确保中文路径正确
        ps_script = """
        Add-Type -AssemblyName System.Windows.Forms
        $f = New-Object System.Windows.Forms.FolderBrowserDialog
        $f.Description = "请选择一个文件夹进行索引"
        $f.ShowNewFolderButton = $true
        if ($f.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
            # 确保输出UTF-8编码
            [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
            Write-Output $f.SelectedPath
        }
        """
        
        # 运行 PowerShell 命令，指定UTF-8编码
        result = subprocess.run(
            ["powershell", "-Command", "-ExecutionPolicy", "Bypass", ps_script], 
            capture_output=True, 
            text=True, 
            creationflags=subprocess.CREATE_NO_WINDOW,
            encoding='utf-8',  # 明确指定UTF-8编码
            errors='replace'  # 处理编码错误
        )
        
        path = result.stdout.strip()
        if path:
            # 验证路径有效性
            if os.path.exists(path):
                return {"path": path, "cancelled": False}
            else:
                return {"path": None, "cancelled": True, "error": "选择的路径不存在"}
        else:
            return {"path": None, "cancelled": True}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件夹选择失败: {str(e)}")

@router.post("/api/set-folder")
def set_folder(request: dict):
    """
    直接设置文件夹路径
    接收前端直接输入的路径
    """
    try:
        path = request.get("path", "").strip()
        
        if not path:
            return {"error": "路径不能为空"}
        
        # 处理路径中的特殊字符和编码
        try:
            # 尝试解码可能的编码问题
            if isinstance(path, bytes):
                path = path.decode('utf-8', errors='replace')
            else:
                # 确保是字符串
                path = str(path)
        except Exception:
            return {"error": "路径编码错误"}
        
        # 规范化路径
        path = os.path.normpath(path)
        
        # 验证路径存在性
        if not os.path.exists(path):
            return {"error": f"路径不存在: {path}"}
        
        # 验证是否为文件夹
        if not os.path.isdir(path):
            return {"error": f"路径不是文件夹: {path}"}
        
        # 验证访问权限
        if not os.access(path, os.R_OK):
            return {"error": f"无法访问文件夹: {path}"}
        
        return {
            "path": path, 
            "success": True,
            "message": f"成功设置文件夹: {os.path.basename(path)}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"设置文件夹失败: {str(e)}")

@router.get("/api/open-file")
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

@router.get("/api/open-folder")
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
