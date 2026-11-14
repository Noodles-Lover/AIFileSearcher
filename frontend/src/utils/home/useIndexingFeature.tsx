import { useState } from 'react';
import { Modal, message } from 'antd';
import { ExclamationCircleOutlined } from '@ant-design/icons';
import { API_ENDPOINTS, apiPost } from '../api';

export interface IndexProgressState {
  status: string;
  current: number;
  total: number;
  file: string;
  percent: number;
  msg: string;
  last_done: string;
}

const INITIAL_INDEX_PROGRESS: IndexProgressState = {
  status: '',
  current: 0,
  total: 0,
  file: '',
  percent: 0,
  msg: '',
  last_done: '',
};

export function useIndexingFeature() {
  const [indexing, setIndexing] = useState(false);
  const [cancelling, setCancelling] = useState(false);
  const [indexProgress, setIndexProgress] = useState<IndexProgressState>(INITIAL_INDEX_PROGRESS);

  const handleIndexFolder = async (path: string) => {
    if (!path) {
      message.warning('请先选择一个文件夹');
      return;
    }

    setIndexing(true);
    setCancelling(false);
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
              setCancelling(false);
              setTimeout(() => setIndexing(false), 1000);
              continue;
            }

            if (eventData.status === 'cancelled') {
              setIndexProgress((prev) => ({ ...prev, ...eventData }));
              message.warning(eventData.msg || '索引已取消，已保存部分结果');
              setCancelling(false);
              setTimeout(() => setIndexing(false), 1000);
              continue;
            }

            if (eventData.status === 'fatal') {
              message.error(`索引失败: ${eventData.msg}`);
              setIndexing(false);
              setCancelling(false);
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
              last_done: eventData.last_done ?? prev.last_done,
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
      setCancelling(false);
    }
  };

  const handleCancelIndex = () => {
    if (!indexing || cancelling) return;
    Modal.confirm({
      title: '确认取消索引？',
      icon: <ExclamationCircleOutlined />,
      content: '当前文件处理完成后停止，已处理部分将保存为部分索引，下次索引自动续传。',
      okText: '确认取消',
      cancelText: '继续索引',
      okType: 'danger',
      onOk: async () => {
        setCancelling(true);
        try {
          const data = await apiPost<{ success?: boolean; message?: string }>(API_ENDPOINTS.INDEX_CANCEL);
          if (!data.success) {
            message.error(data.message || '取消失败');
            setCancelling(false);
          }
          // 成功后由 cancelled 事件驱动弹窗关闭
        } catch {
          message.error('取消失败');
          setCancelling(false);
        }
      },
    });
  };

  return {
    indexing,
    indexProgress,
    handleIndexFolder,
    handleCancelIndex,
    cancelling,
  };
}
