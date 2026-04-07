import type { FileItem } from '../components/FileIcon';

export const convertSizeToBytes = (size: number | null, unit: string): number | null => {
  if (size === null) return null;

  const multipliers: Record<string, number> = {
    B: 1,
    KB: 1024,
    MB: 1024 * 1024,
    GB: 1024 * 1024 * 1024,
  };

  return size * (multipliers[unit] || 1);
};

export const getRelativePath = (filePath: string, currentPath: string | null): string => {
  if (!currentPath) {
    return filePath;
  }

  const normalizedCurrentPath = currentPath.replace(/[\\/]/g, '/').replace(/\/$/, '');
  const normalizedFilePath = filePath.replace(/[\\/]/g, '/');

  if (!normalizedFilePath.startsWith(normalizedCurrentPath)) {
    return filePath;
  }

  const relativePath = normalizedFilePath.substring(normalizedCurrentPath.length).replace(/^\//, '');
  if (!relativePath) {
    return filePath;
  }

  const lastSlashIndex = relativePath.lastIndexOf('/');
  return lastSlashIndex > 0 ? `.../${relativePath.substring(0, lastSlashIndex)}/` : '.../';
};

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
      extension: `.${item.file_path.split('.').pop() || ''}`,
      type: 'file',
      score: item.score,
      content_preview: item.content,
      chunk_count: item.chunk_count || 1,
      all_chunks: item.all_chunks || []
    };
  });
};
