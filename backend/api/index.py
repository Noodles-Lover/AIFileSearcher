import os
import json
import asyncio
from typing import AsyncGenerator
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from backend.RAG.SystemManager import system
from backend.RAG.FileCache import FileCache
from backend.process.FileProcessor import FileProcessor
from backend.utils.path_utils import get_project_root, get_data_path

router = APIRouter()

@router.post("/api/clear_cache")
def clear_cache():
    """
    清理无用文件缓存（真正不存在的文件）
    """
    try:
        cache_path = get_data_path("file_cache.json")
        file_cache = FileCache(cache_path)
        
        cleaned_count = file_cache.clean_nonexistent_files()
        
        print(f"清理了 {cleaned_count} 个无用文件缓存记录")
        
        return {"success": True, "message": f"清理了 {cleaned_count} 个无用文件缓存记录"}
        
    except Exception as e:
        print(f"清理缓存时出错: {e}")
        return {"error": f"清理缓存失败: {str(e)}"}

@router.post("/api/clear_index")
def clear_index():
    """
    清空向量索引
    """
    try:
        # 直接删除文件，不需要初始化系统
        index_path = get_data_path("faiss_index.bin")
        metadata_path = get_data_path("metadata.json")
        cache_path = get_data_path("file_cache.json")
        
        files_deleted = []
        
        if os.path.exists(index_path):
            os.remove(index_path)
            files_deleted.append("faiss_index.bin")
            
        if os.path.exists(metadata_path):
            os.remove(metadata_path)
            files_deleted.append("metadata.json")
        
        # 删除缓存文件
        if os.path.exists(cache_path):
            os.remove(cache_path)
            files_deleted.append("file_cache.json")
        
        # 清空系统管理器中的向量存储实例（如果已初始化）
        if system.is_initialized and system.vector_store:
            system.vector_store.index = None
            system.vector_store.metadata = []
        
        # 重置系统初始化状态，强制重新初始化
        system.is_initialized = False
        system.embedding_model = None
        system.vector_store = None
        
        print(f"索引和缓存已清空，删除文件: {', '.join(files_deleted)}")
        
        return {"success": True, "message": f"索引和缓存已清空，删除了 {len(files_deleted)} 个文件"}
        
    except Exception as e:
        print(f"清空索引时出错: {e}")
        return {"error": f"清空索引失败: {str(e)}"}

@router.post("/api/index_folder")
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
            project_root = get_project_root()
            
            # 初始化系统
            embedder = system.get_embedding_model()
            store = system.get_vector_store()
            processor = FileProcessor()
            
            # 初始化文件缓存
            cache_path = get_data_path("file_cache.json")
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
            
            print(f"🚀 开始处理 {total_files} 个文件...")
            processed_count = 0
            skipped_count = 0
            
            # 处理每个文件
            for i, file_path in enumerate(files_to_process):
                try:
                    file_name = os.path.basename(file_path)
                    current = i + 1
                    percent = int((current / total_files) * 100)
                    
                    # 检查文件是否需要处理
                    should_process, reason = file_cache.should_process_file(file_path)
                    if should_process:
                        # 处理文件并生成向量
                        try:
                            # 处理文件内容
                            result = processor.process_file(file_path)
                            
                            if "error" in result:
                                # 处理失败
                                error_msg = result['error']
                                print(f"文件处理失败 {file_path}: {error_msg}")
                                skipped_count += 1
                                yield f"data: {json.dumps({'status': 'skip', 'current': current, 'total': total_files, 'file': file_name, 'percent': percent, 'msg': f'跳过: {error_msg}'})}\n\n"
                            else:
                                # 获取分块内容
                                chunks = result.get("chunks", [])
                                
                                if chunks and len(chunks) > 0:
                                    # 生成向量嵌入
                                    embeddings = embedder.encode(chunks)
                                    
                                    # 准备元数据
                                    metas = []
                                    for j, chunk in enumerate(chunks):
                                        metadata = {
                                            'file_path': file_path,
                                            'file_name': file_name,
                                            'chunk_index': j,
                                            'chunk_text': chunk,
                                            'total_chunks': len(chunks)
                                        }
                                        metas.append(metadata)
                                    
                                    # 批量添加到向量数据库
                                    added_count = store.add(embeddings, metas, file_name)
                                    
                                    # 更新文件缓存
                                    vector_indices = list(range(len(store.metadata) - added_count, len(store.metadata)))
                                    file_cache.update_file_cache(file_path, vector_indices)
                                    processed_count += 1
                                    
                                    # 控制台输出
                                    print(f"✓ 已处理: {file_name} ({len(chunks)} 个分块, {current}/{total_files})")
                                    
                                    # 发送进度事件
                                    yield f"data: {json.dumps({'status': 'progress', 'current': current, 'total': total_files, 'file': file_name, 'percent': percent, 'msg': f'已处理: {file_name} ({len(chunks)} 个分块)'})}\n\n"
                                    await asyncio.sleep(0.01)  # 小延迟让进度更可见
                                else:
                                    # 文件没有内容
                                    skipped_count += 1
                                    print(f"⚪ 跳过: {file_name} - 文件无内容 ({current}/{total_files})")
                                    yield f"data: {json.dumps({'status': 'skip', 'current': current, 'total': total_files, 'file': file_name, 'percent': percent, 'msg': f'跳过: 文件无内容'})}\n\n"
                            
                        except Exception as process_error:
                            print(f"处理文件失败 {file_path}: {process_error}")
                            skipped_count += 1
                            yield f"data: {json.dumps({'status': 'error', 'current': current, 'total': total_files, 'file': file_name, 'percent': percent, 'msg': f'处理失败: {str(process_error)}'})}\n\n"
                    else:
                        # 跳过文件
                        skipped_count += 1
                        print(f"⚪ 跳过: {file_name} - {reason} ({current}/{total_files})")
                        
                        # 发送跳过事件
                        yield f"data: {json.dumps({'status': 'skip', 'current': current, 'total': total_files, 'file': file_name, 'percent': percent, 'msg': f'跳过: {reason}'})}\n\n"
                    
                except Exception as e:
                    # 处理错误
                    current = i + 1
                    percent = int((current / total_files) * 100)
                    file_name = os.path.basename(file_path)
                    
                    print(f"❌ 错误: {file_name} - {str(e)} ({current}/{total_files})")
                    yield f"data: {json.dumps({'status': 'error', 'current': current, 'total': total_files, 'file': file_name, 'percent': percent, 'msg': f'錯誤: {str(e)}'})}\n\n"
            
            # 保存向量数据库
            try:
                store.save()
                yield f"data: {json.dumps({'status': 'saving', 'current': total_files, 'total': total_files, 'percent': 100, 'msg': '正在保存向量数据库...'})}\n\n"
                await asyncio.sleep(0)
            except Exception as save_error:
                yield f"data: {json.dumps({'status': 'error', 'current': total_files, 'total': total_files, 'percent': 100, 'msg': f'保存失败: {str(save_error)}'})}\n\n"
                await asyncio.sleep(0)
            
            # 保存文件缓存
            try:
                file_cache.save_cache()
                yield f"data: {json.dumps({'status': 'saving', 'current': total_files, 'total': total_files, 'percent': 100, 'msg': '正在保存文件缓存...'})}\n\n"
                await asyncio.sleep(0)
            except Exception as cache_error:
                yield f"data: {json.dumps({'status': 'error', 'current': total_files, 'total': total_files, 'percent': 100, 'msg': f'缓存保存失败: {str(cache_error)}'})}\n\n"
                await asyncio.sleep(0)
            
            # 发送完成事件
            completion_msg = f'索引完成！處理了 {processed_count} 個文件，跳過了 {skipped_count} 個文件'
            print(f"🎉 {completion_msg}")
            yield f"data: {json.dumps({'status': 'complete', 'current': total_files, 'total': total_files, 'percent': 100, 'msg': completion_msg})}\n\n"
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
