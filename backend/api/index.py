import os
import json
import asyncio
from typing import AsyncGenerator
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from backend.RAG.SystemManager import SystemManager
from backend.process.FileProcessor import FileProcessor
from backend.utils.path_utils import get_project_root, get_data_path
from backend.utils.IndexedFoldersManager import folders_manager
from backend.utils.settings_manager import settings_manager

router = APIRouter()

@router.post("/api/clear_cache")
def clear_cache():
    """
    清理已从磁盘消失的文件的向量与缓存记录
    """
    try:
        sm = SystemManager.get_instance()
        file_cache = sm.get_file_cache()
        missing_files = [
            file_path for file_path in file_cache.get_all_files()
            if not os.path.exists(file_path)
        ]

        removed_vectors = 0
        if missing_files:
            writer = sm.get_index_writer()
            removed_vectors = writer.remove_files(missing_files)
            writer.save()

        print(f"清理了 {len(missing_files)} 个失效文件，{removed_vectors} 个向量")

        return {"success": True, "message": f"清理了 {len(missing_files)} 个失效文件，{removed_vectors} 个向量"}

    except Exception as e:
        print(f"清理缓存时出错: {e}")
        return {"error": f"清理缓存失败: {str(e)}"}

@router.post("/api/clear_index")
def clear_index():
    """
    清空向量索引
    """
    try:
        index_path = get_data_path("faiss_index.bin")
        state_path = get_data_path("index_state.json")

        files_deleted = []

        if os.path.exists(index_path):
            os.remove(index_path)
            files_deleted.append("faiss_index.bin")

        if os.path.exists(state_path):
            os.remove(state_path)
            files_deleted.append("index_state.json")

        folders_manager.clear()

        SystemManager.reset_instance()

        print(f"索引和缓存已清空，删除文件: {', '.join(files_deleted)}")

        return {"success": True, "message": f"索引和缓存已清空，删除了 {len(files_deleted)} 个文件"}

    except Exception as e:
        print(f"清空索引时出错: {e}")
        return {"error": f"清空索引失败: {str(e)}"}

@router.get("/api/indexed_folders")
def get_indexed_folders():
    """
    获取所有已索引的根文件夹路径
    """
    try:
        folders = folders_manager.get_indexed_folders()
        return {"folders": sorted(folders)}
    except Exception as e:
        print(f"获取已索引文件夹时出错: {e}")
        return {"error": f"获取已索引文件夹失败: {str(e)}"}

@router.post("/api/remove_indexed_folder")
def remove_indexed_folder(request: dict):
    """
    删除指定文件夹的所有索引数据
    """
    try:
        folder_path = request.get("path", "").strip()
        if not folder_path:
            return {"error": "路径不能为空"}

        # 规范化路径
        folder_path = os.path.normpath(folder_path)

        sm = SystemManager.get_instance()
        file_cache = sm.get_file_cache()
        files_to_remove = file_cache.get_files_under(folder_path)

        if not files_to_remove:
            return {"success": True, "message": f"未找到 {folder_path} 下的索引数据"}

        writer = sm.get_index_writer()
        removed_vectors = writer.remove_files(files_to_remove)
        writer.save()

        # 从已索引文件夹记录中移除
        folders_manager.remove_folder(folder_path)

        return {
            "success": True,
            "message": f"已删除 {folder_path} 的索引数据（{len(files_to_remove)} 个文件，{removed_vectors} 个向量）"
        }

    except Exception as e:
        print(f"删除文件夹索引时出错: {e}")
        return {"error": f"删除文件夹索引失败: {str(e)}"}

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
            sm = SystemManager.get_instance()
            embedder = await asyncio.to_thread(sm.get_embedding_model)
            store = await asyncio.to_thread(sm.get_vector_store)
            processor = FileProcessor()
            
            # 初始化文件缓存
            file_cache = sm.get_file_cache()
            writer = sm.get_index_writer()
            include_subfolders = bool(settings_manager.load().get("include_subfolders", False))
            
            # 发送初始化事件
            yield f"data: {json.dumps({'status': 'init', 'current': 0, 'total': 0, 'percent': 0, 'msg': '正在初始化系統...'})}\n\n"
            await asyncio.sleep(0)
            
            # 扫描文件夹（大目录遍历放线程池，不阻塞事件循环）
            def _scan_files():
                found = []
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if processor.is_supported_file(file_path):
                            found.append(file_path)
                    if not include_subfolders:
                        break
                return found

            files_to_process = await asyncio.to_thread(_scan_files)

            # 清理已从磁盘消失的文件的旧向量与缓存记录
            missing_files = [
                file_path for file_path in file_cache.get_files_under(folder_path)
                if not os.path.exists(file_path)
            ]
            if missing_files:
                await asyncio.to_thread(writer.remove_files, missing_files)

            total_files = len(files_to_process)
            
            if total_files == 0:
                yield f"data: {json.dumps({'status': 'error', 'current': 0, 'total': 0, 'percent': 0, 'msg': '未找到支持的文件'})}\n\n"
                await asyncio.sleep(0)
                return
            
            # 发送扫描事件
            yield f"data: {json.dumps({'status': 'scanning', 'current': 0, 'total': total_files, 'percent': 0, 'msg': '正在掃描文件...'})}\n\n"
            await asyncio.sleep(0)
            
            # 发送开始事件
            yield f"data: {json.dumps({'status': 'start', 'current': 0, 'total': total_files, 'percent': 0, 'msg': f'找到 {total_files} 个支持的文件'})}\n\n"
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
                            result = await asyncio.to_thread(processor.process_file, file_path)
                            
                            if "error" in result:
                                # 处理失败
                                error_msg = result['error']
                                print(f"文件处理失败 {file_path}: {error_msg}")
                                skipped_count += 1
                                yield f"data: {json.dumps({'status': 'skip', 'current': current, 'total': total_files, 'file': file_name, 'percent': percent, 'msg': f'跳过: {error_msg}'})}\n\n"
                            else:
                                # 获取分块内容
                                chunks = result.get("chunks", [])
                                embedding_mode = result.get("embedding_mode", "text")
                                
                                if chunks and len(chunks) > 0:
                                    # 生成向量嵌入
                                    if embedding_mode == "image":
                                        embedding_inputs = result.get("embedding_inputs", [])
                                        embeddings = await asyncio.to_thread(embedder.encode_images, embedding_inputs)
                                    else:
                                        embeddings = await asyncio.to_thread(embedder.encode, chunks)
                                    
                                    # 准备元数据
                                    metas = []
                                    for j, chunk in enumerate(chunks):
                                        metadata = {
                                            'file_path': file_path,
                                            'chunk_index': j,
                                            'chunk_text': chunk,
                                            'content_type': embedding_mode
                                        }
                                        metas.append(metadata)
                                    
                                    # 替换该文件的全部向量（先删旧，再写新）
                                    await asyncio.to_thread(writer.write_file, file_path, embeddings, metas)
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
            
            # 保存向量数据库与文件缓存（原子写，同代落盘）
            try:
                await asyncio.to_thread(writer.save)
                yield f"data: {json.dumps({'status': 'saving', 'current': total_files, 'total': total_files, 'percent': 100, 'msg': '正在保存向量数据库...'})}\n\n"
                await asyncio.sleep(0)
            except Exception as save_error:
                yield f"data: {json.dumps({'status': 'error', 'current': total_files, 'total': total_files, 'percent': 100, 'msg': f'保存失败: {str(save_error)}'})}\n\n"
                await asyncio.sleep(0)

            # 记录已索引的文件夹
            if processed_count > 0:
                folders_manager.add_folder(folder_path)
            
            # 发送完成事件
            completion_msg = f'索引完成！處理了 {processed_count} 個文件，跳過了 {skipped_count} 個文件'
            print(f"🎉 {completion_msg}")
            
            # 添加总分块数统计
            try:
                store = sm.get_vector_store()
                if store and hasattr(store, 'index') and store.index:
                    total_chunks = store.index.ntotal
                    print(f"📊 數據庫統計: 總分塊數 {total_chunks}")
            except Exception as stats_error:
                print(f"⚠️ 無法獲取分塊統計: {stats_error}")
            
            
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
