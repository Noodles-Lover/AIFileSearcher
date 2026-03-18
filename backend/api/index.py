import os
import json
import asyncio
from typing import AsyncGenerator
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from backend.RAG.SystemManager import system
from backend.RAG.FileCache import FileCache
from backend.process.FileProcessor import FileProcessor

router = APIRouter()

@router.post("/index_folder")
async def index_folder(request: dict):
    """索引指定文件夹"""
    
    async def event_generator():
        try:
            folder_path = request.get("path")
            if not folder_path or not os.path.exists(folder_path):
                yield f"data: {json.dumps({'status': 'error', 'msg': '无效的文件夹路径'})}\n\n"
                await asyncio.sleep(0)
                return
            
            # 获取项目根目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            
            # 初始化系统
            embedder = system.get_embedding_model()
            store = system.get_vector_store()
            processor = FileProcessor()
            
            # 初始化文件缓存
            cache_path = os.path.join(project_root, "data", "file_cache.json")
            file_cache = FileCache(cache_path)
            
            # 发送初始化事件
            yield f"data: {json.dumps({'status': 'init', 'current': 0, 'total': 0, 'percent': 0, 'msg': '正在初始化系統...'})}\n\n"
            await asyncio.sleep(0)
            
            # 扫描文件夹
            files_to_process = []
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if processor.is_supported_file(file_path):
                        files_to_process.append(file_path)
            
            total_files = len(files_to_process)
            
            if total_files == 0:
                yield f"data: {json.dumps({'status': 'error', 'current': 0, 'total': 0, 'percent': 0, 'msg': '未找到支持的文件'})}\n\n"
                await asyncio.sleep(0)
                return
            
            # 发送扫描事件
            yield f"data: {json.dumps({'status': 'scanning', 'current': 0, 'total': total_files, 'percent': 0, 'msg': '正在掃描文件...'})}\n\n"
            await asyncio.sleep(0)
            
            # 发送开始事件
            yield f"data: {json.dumps({'status': 'start', 'current': 0, 'total': total_files, 'percent': 0, 'msg': f'找到 {total_files} 個支持的文件'})}\n\n"
            await asyncio.sleep(0)
            
            processed_count = 0
            skipped_count = 0
            
            # 处理每个文件
            for i, file_path in enumerate(files_to_process):
                try:
                    file_name = os.path.basename(file_path)
                    current = i + 1
                    percent = int((current / total_files) * 100)
                    
                    # 检查文件是否需要处理
                    if file_cache.should_process_file(file_path):
                        # 处理文件
                        processor.process_file(file_path)
                        processed_count += 1
                        
                        # 发送进度事件
                        yield f"data: {json.dumps({'status': 'progress', 'current': current, 'total': total_files, 'file': file_name, 'percent': percent, 'msg': f'正在處理: {file_name}'})}\n\n"
                        await asyncio.sleep(0)
                    else:
                        # 跳过文件
                        skipped_count += 1
                        
                        # 发送跳过事件
                        yield f"data: {json.dumps({'status': 'skip', 'current': current, 'total': total_files, 'file': file_name, 'percent': percent, 'msg': f'跳過: 文件未修改'})}\n\n"
                        await asyncio.sleep(0)
                    
                except Exception as e:
                    # 处理错误
                    current = i + 1
                    percent = int((current / total_files) * 100)
                    file_name = os.path.basename(file_path)
                    
                    yield f"data: {json.dumps({'status': 'error', 'current': current, 'total': total_files, 'file': file_name, 'percent': percent, 'msg': f'錯誤: {str(e)}'})}\n\n"
                    await asyncio.sleep(0)
            
            # 发送完成事件
            yield f"data: {json.dumps({'status': 'complete', 'current': total_files, 'total': total_files, 'percent': 100, 'msg': f'索引完成！處理了 {processed_count} 個文件，跳過了 {skipped_count} 個文件'})}\n\n"
            await asyncio.sleep(0)
            
        except Exception as e:
            # 发送致命错误
            yield f"data: {json.dumps({'status': 'fatal', 'current': 0, 'total': 0, 'percent': 0, 'msg': f'致命錯誤: {str(e)}'})}\n\n"
            await asyncio.sleep(0)
    
    return StreamingResponse(
        event_generator(), 
        media_type="text/event-stream",
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "X-Accel-Buffering": "no"
        }
    )
