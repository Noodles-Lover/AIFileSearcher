import type { FileItem } from '../components/FileIcon';

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
  
  // 规范化路径，统一处理路径分隔符
  const normalizedCurrentPath = currentPath.replace(/[\\/]/g, '/').replace(/\/$/, '');
  const normalizedFilePath = filePath.replace(/[\\/]/g, '/');
  
  // 计算相对路径
  if (normalizedFilePath.startsWith(normalizedCurrentPath)) {
    const relPath = normalizedFilePath.substring(normalizedCurrentPath.length).replace(/^\//, '');
    // 如果有相对路径，不管是否有子目录，都返回 .../
    // 对于直接在当前目录下的文件，返回 .../
    // 对于子目录中的文件，提取目录部分
    if (relPath) {
      // 提取目录部分，去掉文件名
      const lastSlashIndex = relPath.lastIndexOf('/');
      if (lastSlashIndex > 0) {
        const dirPath = relPath.substring(0, lastSlashIndex);
        return `.../${dirPath}/`;
      } else {
        // 直接在当前目录下
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
    .filter(item => item.type === 'file') // 过滤掉文件夹
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