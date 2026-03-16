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

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.responses import PlainTextResponse
import json
import os
import asyncio
from backend.RAG.SystemManager import system
from backend.process.FileProcessor import FileProcessor

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
            print("=== 开始SSE流 ===")
            
            # 初始化系统
            print(f"系統初始化狀態: {system.is_initialized}")
            embedder = system.get_embedding_model()
            store = system.get_vector_store()
            processor = FileProcessor()
            
            print(f"模型已加載: {embedder is not None}")
            print(f"向量存儲已初始化: {store is not None}")
            if store and hasattr(store, 'index') and store.index:
                print(f"當前向量數量: {store.index.ntotal}")
            else:
                print("向量存儲索引為空或未初始化")
            
            # 扫描文件
            print(f"扫描文件夹: {folder_path}")
            
            files_to_process = []
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in processor.PARSERS:
                        files_to_process.append(os.path.join(root, file))
            
            total_files = len(files_to_process)
            print(f"找到 {total_files} 个支持的文件")
            
            # 发送开始事件
            yield f"data: {json.dumps({'status': 'init', 'msg': '正在初始化系統...'})}\n\n"
            yield f"data: {json.dumps({'status': 'scanning', 'msg': '正在掃描文件...'})}\n\n"
            yield f"data: {json.dumps({'status': 'start', 'total': total_files, 'msg': f'找到 {total_files} 個支持的文件'})}\n\n"
            
            # 处理每个文件
            for i, file_path in enumerate(files_to_process):
                try:
                    file_name = os.path.basename(file_path)
                    print(f"处理文件 {i+1}/{total_files}: {file_name}")
                    
                    # 发送开始处理事件 - 使用当前进度
                    current_progress = int(i / total_files * 100)
                    start_event = {
                        'status': 'progress', 
                        'current': i+1, 
                        'total': total_files, 
                        'file': file_name, 
                        'percent': current_progress, 
                        'msg': f'正在處理: {file_name}'
                    }
                    
                    yield f"data: {json.dumps(start_event)}\n\n"
                    
                    # 处理文件
                    result = processor.process_file(file_path)
                    
                    if "error" in result:
                        print(f"跳过文件 {file_name}: {result['error']}")
                        continue
                    
                    chunks = result.get("chunks", [])
                    if not chunks:
                        print(f"跳过空文件: {file_name}")
                        continue
                    
                    # 向量化并存储
                    vectors = embedder.encode(chunks)
                    metas = []
                    for chunk_idx, chunk_text in enumerate(chunks):
                        metas.append({
                            "file_path": file_path,
                            "chunk_index": chunk_idx,
                            "content": chunk_text,
                            "type": result["type"]
                        })
                    
                    store.add(vectors, metas, file_name)
                    
                    # 发送文件完成事件 - 使用完成后的进度
                    completed_progress = int((i + 1) / total_files * 100)
                    complete_event = {
                        'status': 'progress', 
                        'current': i+1, 
                        'total': total_files, 
                        'file': file_name, 
                        'percent': completed_progress, 
                        'msg': f'✓ 完成: {file_name}'
                    }
                    
                    yield f"data: {json.dumps(complete_event)}\n\n"
                    
                    # 短暂延迟
                    await asyncio.sleep(0.2)
                    
                except Exception as e:
                    print(f"处理文件 {file_name} 时出错: {e}")
                    error_event = f"data: {json.dumps({'status': 'error', 'file': os.path.basename(file_path), 'msg': str(e)})}\n\n"
                    yield error_event

            # 发送完成事件
            yield f"data: {json.dumps({'status': 'complete', 'msg': f'🎉 索引完成! 共處理 {total_files} 個文件'})}\n\n"
            print("=== SSE流结束 ===")
            
        except Exception as e:
            yield f"data: {json.dumps({'status': 'fatal', 'msg': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(), 
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*"
        }
    )
