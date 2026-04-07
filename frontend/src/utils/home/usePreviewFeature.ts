import { useState } from 'react';
import { message } from 'antd';
import { API_ENDPOINTS, apiGet } from '../api';
import type { FileItem } from '../../components/FileIcon';

interface PreviewResponse {
  error?: string;
  content?: string;
}

export function usePreviewFeature(searchQuery: string) {
  const [previewVisible, setPreviewVisible] = useState(false);
  const [previewContent, setPreviewContent] = useState('');
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewTitle, setPreviewTitle] = useState('');
  const [chunkVisible, setChunkVisible] = useState(false);
  const [chunkContent, setChunkContent] = useState('');
  const [chunkTitle, setChunkTitle] = useState('');
  const [chunkData, setChunkData] = useState<any[]>([]);

  const handlePreview = async (record: FileItem) => {
    setPreviewTitle(record.name);
    setPreviewVisible(true);
    setPreviewLoading(true);
    setPreviewContent('');

    try {
      const data = await apiGet<PreviewResponse>(`${API_ENDPOINTS.PREVIEW}?path=${encodeURIComponent(record.path)}`);
      setPreviewContent(data.error ? `Error: ${data.error}` : (data.content || '无预览内容'));
    } catch {
      setPreviewContent('预览加载失败');
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleViewChunk = async (record: FileItem) => {
    if (!searchQuery.trim()) {
      message.warning('请先执行语义搜索后再查看分块');
      return;
    }

    setChunkTitle(`${record.name} - 命中分块`);
    setChunkContent('正在加载分块内容...');
    setChunkData([]);
    setChunkVisible(true);

    try {
      if (record.all_chunks && record.all_chunks.length > 0) {
        setChunkData(record.all_chunks);
        return;
      }

      const response = await fetch(
        `${API_ENDPOINTS.VECTOR_SEARCH.replace('/vector_search', '/file_chunks')}?q=${encodeURIComponent(searchQuery)}&file_path=${encodeURIComponent(record.path)}`
      );
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || '获取分块失败');
      }

      const chunks = data.chunks || [];
      if (chunks.length === 0) {
        setChunkContent('未找到该文件的分块内容');
        return;
      }

      setChunkData(chunks);
    } catch (error) {
      console.error('获取分块失败:', error);
      setChunkContent('获取分块内容失败');
      message.error('获取分块失败');
    }
  };

  return {
    previewVisible,
    setPreviewVisible,
    previewContent,
    previewLoading,
    previewTitle,
    chunkVisible,
    setChunkVisible,
    chunkContent,
    chunkTitle,
    chunkData,
    handlePreview,
    handleViewChunk,
  };
}
