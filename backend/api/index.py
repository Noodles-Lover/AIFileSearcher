import sys
import os
import json
import time

# 确保项目根目录在路径中
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(backend_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from backend.process.FileProcessor import FileProcessor
from backend.core.SystemManager import system

router = APIRouter()

@router.post("/api/index_folder")
async def index_folder(request: Request):
    """
    索引文件夹接口 (SSE 流式响应)
    接收文件夹路径，遍历处理文件，并实时返回进度
    """
    data = await request.json()
    folder_path = data.get("path")
    
    if not folder_path:
        return {"error": "Path is required"}
        
    if not os.path.exists(folder_path):
        return {"error": f"Path does not exist: {folder_path}"}

    async def event_generator():
        try:
            yield f"data: {json.dumps({'status': 'init', 'msg': '正在初始化系統...'})}\n\n"
            
            # 初始化系统 (如果尚未初始化)
            embedder = system.get_embedding_model()
            store = system.get_vector_store()
            processor = FileProcessor()
            
            yield f"data: {json.dumps({'status': 'scanning', 'msg': '正在掃描文件...'})}\n\n"
            
            # 遍历文件
            files_to_process = []
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in processor.PARSERS:
                        files_to_process.append(os.path.join(root, file))
            
            total_files = len(files_to_process)
            yield f"data: {json.dumps({'status': 'start', 'total': total_files, 'msg': f'找到 {total_files} 個支持的文件'})}\n\n"
            
            for i, file_path in enumerate(files_to_process):
                try:
                    file_name = os.path.basename(file_path)
                    
                    # 1. 解析与分块
                    yield f"data: {json.dumps({'status': 'progress', 'current': i+1, 'total': total_files, 'file': file_name, 'percent': int((i) / total_files * 100), 'msg': f'正在解析文件: {file_name}'})}\n\n"
                    
                    result = processor.process_file(file_path)
                    
                    if "error" in result:
                        yield f"data: {json.dumps({'status': 'skipped', 'file': file_name, 'msg': result['error']})}\n\n"
                        continue
                    
                    chunks = result.get("chunks", [])
                    if not chunks:
                        yield f"data: {json.dumps({'status': 'skipped', 'file': file_name, 'msg': '文件無內容'})}\n\n"
                        continue
                    
                    # 2. 向量化
                    yield f"data: {json.dumps({'status': 'progress', 'current': i+1, 'total': total_files, 'file': file_name, 'percent': int((i) / total_files * 100), 'msg': f'正在向量化: {file_name} ({len(chunks)} 個文本塊)'})}\n\n"
                    
                    vectors = embedder.encode(chunks)
                    
                    # 3. 准备元数据
                    yield f"data: {json.dumps({'status': 'progress', 'current': i+1, 'total': total_files, 'file': file_name, 'percent': int((i) / total_files * 100), 'msg': f'正在準備元數據: {file_name}'})}\n\n"
                    
                    metas = []
                    for chunk_idx, chunk_text in enumerate(chunks):
                        metas.append({
                            "file_path": file_path,
                            "chunk_index": chunk_idx,
                            "content": chunk_text,
                            "type": result["type"]
                        })
                    
                    # 4. 存储
                    yield f"data: {json.dumps({'status': 'progress', 'current': i+1, 'total': total_files, 'file': file_name, 'percent': int((i) / total_files * 100), 'msg': f'正在存儲向量: {file_name}'})}\n\n"
                    
                    store.add(vectors, metas)
                    
                    # 完成该文件
                    progress = int((i + 1) / total_files * 100)
                    yield f"data: {json.dumps({'status': 'progress', 'current': i+1, 'total': total_files, 'file': file_name, 'percent': progress, 'msg': f'✓ 完成: {file_name}'})}\n\n"
                    
                except Exception as e:
                    yield f"data: {json.dumps({'status': 'error', 'file': os.path.basename(file_path), 'msg': str(e)})}\n\n"

            yield f"data: {json.dumps({'status': 'complete', 'msg': f'🎉 索引完成! 共處理 {total_files} 個文件'})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'status': 'fatal', 'msg': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
