import { useState } from 'react';
import { message } from 'antd';
import { API_ENDPOINTS } from '../api';

export interface IndexProgressState {
  status: string;
  current: number;
  total: number;
  file: string;
  percent: number;
  msg: string;
}

const INITIAL_INDEX_PROGRESS: IndexProgressState = {
  status: '',
  current: 0,
  total: 0,
  file: '',
  percent: 0,
  msg: '',
};

export function useIndexingFeature() {
  const [indexing, setIndexing] = useState(false);
  const [indexProgress, setIndexProgress] = useState<IndexProgressState>(INITIAL_INDEX_PROGRESS);

  const handleIndexFolder = async (path: string) => {
    if (!path) {
      message.warning('请先选择一个文件夹');
      return;
    }

    setIndexing(true);
    setIndexProgress({ ...INITIAL_INDEX_PROGRESS, msg: '正在初始化索引...' });

    try {
      const response = await fetch(API_ENDPOINTS.INDEX_FOLDER, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path }),
      });

      if (!response.ok) {
        throw new Error(`索引请求失败: ${response.status} ${response.statusText}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('无法读取索引进度流');
      }

      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n').filter((line) => line.trim() !== '');

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;

          try {
            const eventData = JSON.parse(line.slice(6));

            if (eventData.status === 'complete') {
              setIndexProgress((prev) => ({ ...prev, ...eventData }));
              message.success('索引完成');
              setTimeout(() => setIndexing(false), 1000);
              continue;
            }

            if (eventData.status === 'fatal') {
              message.error(`索引失败: ${eventData.msg}`);
              setIndexing(false);
              continue;
            }

            setIndexProgress((prev) => ({
              ...prev,
              status: eventData.status || prev.status,
              current: eventData.current ?? prev.current,
              total: eventData.total ?? prev.total,
              percent: eventData.percent ?? prev.percent,
              file: eventData.file ?? prev.file,
              msg: eventData.msg || prev.msg,
            }));
          } catch (error) {
            console.error('解析索引进度失败:', error, line);
          }
        }
      }
    } catch (error) {
      console.error('索引失败:', error);
      message.error(`索引失败: ${error instanceof Error ? error.message : '未知错误'}`);
      setIndexing(false);
    }
  };

  return {
    indexing,
    indexProgress,
    handleIndexFolder,
  };
}
