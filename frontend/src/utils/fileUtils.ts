import type { FileItem } from '../components/FileIcon';

/**
 * 将文件大小转换为字节数
 * @param size 文件大小
 * @param unit 单位 (B, KB, MB, GB)
 * @returns 字节数
 */
export const convertSizeToBytes = (size: number | null, unit: string): number | null => {
  if (size === null) return null;
  const multipliers: { [key: string]: number } = {
    'B': 1,
    'KB': 1024,
    'MB': 1024 * 1024,
    'GB': 1024 * 1024 * 1024
  };
  return size * (multipliers[unit] || 1);
};

/**
 * 格式化文件大小
 * @param bytes 字节数
 * @returns 格式化后的大小字符串
 */
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

/**
 * 格式化日期
 * @param timestamp 时间戳
 * @returns 格式化后的日期字符串
 */
export const formatDate = (timestamp: number): string => {
  const date = new Date(timestamp * 1000);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
};

/**
 * 计算相对路径
 * @param filePath 文件完整路径
 * @param currentPath 当前文件夹路径
 * @returns 相对路径，格式为 .../relative/path
 */
export const getRelativePath = (filePath: string, currentPath: string | null): string => {
  if (!currentPath) {
    return filePath;
  }
  
  const normalizedCurrentPath = currentPath.replace(/[\\/]/g, '/').replace(/\/$/, '');
  const normalizedFilePath = filePath.replace(/[\\/]/g, '/');
  
  if (normalizedFilePath.startsWith(normalizedCurrentPath)) {
    const relPath = normalizedFilePath.substring(normalizedCurrentPath.length).replace(/^\//, '');
    if (relPath) {
      const lastSlashIndex = relPath.lastIndexOf('/');
      if (lastSlashIndex > 0) {
        const dirPath = relPath.substring(0, lastSlashIndex);
        return `.../${dirPath}/`;
      } else {
        return `.../`;
      }
    }
  }
  
  return filePath;
};

/**
 * 处理文件名搜索模式的文件列表
 * @param results 后端返回的文件列表
 * @param currentPath 当前文件夹路径
 * @returns 处理后的文件列表
 */
export const processFilenameSearchResults = (results: any[], currentPath: string | null): FileItem[] => {
  return results
    .filter(item => item.type === 'file')
    .map((item, index) => ({
      key: index.toString(),
      name: item.name,
      path: item.path,
      relativePath: getRelativePath(item.path, currentPath),
      size: item.size,
      size_bytes: item.size_bytes,
      modified: item.modified,
      created: item.created || '-',
      extension: item.extension || '',
      type: item.type
    }));
};

/**
 * 处理语义搜索模式的文件列表
 * @param results 后端返回的文件列表
 * @param currentPath 当前文件夹路径
 * @returns 处理后的文件列表
 */
export const processSemanticSearchResults = (results: any[], currentPath: string | null): FileItem[] => {
  return (results || []).map((item, index) => {
    const fileName = item.file_path.split('\\').pop() || item.file_path.split('/').pop();
    
    return {
      key: index.toString(),
      name: fileName,
      path: item.file_path,
      relativePath: getRelativePath(item.file_path, currentPath),
      size: item.size || '-',
      size_bytes: item.size_bytes || 0,
      modified: item.modified || '-',
      created: '-',
      extension: '.' + (item.file_path.split('.').pop() || ''),
      type: 'file',
      score: item.score,
      content_preview: item.content,
      chunk_count: item.chunk_count || 1,
      all_chunks: item.all_chunks || []
    };
  });
};