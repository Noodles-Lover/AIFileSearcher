import { useState } from 'react';
import { message } from 'antd';
import type { FileItem } from '../../components/FileIcon';
import { API_ENDPOINTS, apiGet, apiPost } from '../api';
import { convertSizeToBytes, getRelativePath, processSemanticSearchResults } from '../fileUtils';

interface FolderResponse {
  path?: string;
  cancelled?: boolean;
  error?: string;
}

interface SetFolderResponse {
  path?: string;
  success?: boolean;
  message?: string;
  error?: string;
}

interface ListFileResult {
  name: string;
  path: string;
  type: 'file' | 'folder';
  size: string;
  size_bytes: number;
  modified: string;
  created?: string;
  extension?: string;
}

function mapListResults(results: ListFileResult[], path: string): FileItem[] {
  return results.map((item, index) => ({
    key: `${item.path}-${index}`,
    name: item.name,
    path: item.path,
    type: item.type,
    size: item.size,
    size_bytes: item.size_bytes,
    modified: item.modified,
    created: item.created || '-',
    extension: item.extension || '',
    relativePath: getRelativePath(item.path, path),
  }));
}

export function useSearchFeature() {
  const [searchQuery, setSearchQuery] = useState('');
  const [files, setFiles] = useState<FileItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [currentPath, setCurrentPath] = useState<string | null>(null);
  const [showPathInput, setShowPathInput] = useState(false);
  const [inputPath, setInputPath] = useState('');
  const [showFilterModal, setShowFilterModal] = useState(false);
  const [filterExtensions, setFilterExtensions] = useState('');
  const [filterMinSize, setFilterMinSize] = useState<number | null>(null);
  const [filterMaxSize, setFilterMaxSize] = useState<number | null>(null);
  const [filterMinSizeUnit, setFilterMinSizeUnit] = useState('B');
  const [filterMaxSizeUnit, setFilterMaxSizeUnit] = useState('B');
  const [filterDateRange, setFilterDateRange] = useState<[any, any]>([null, null]);

  const clearResults = () => {
    setFiles([]);
    setSearchQuery('');
  };

  const resetFilters = () => {
    setFilterExtensions('');
    setFilterMinSize(null);
    setFilterMaxSize(null);
    setFilterMinSizeUnit('B');
    setFilterMaxSizeUnit('B');
    setFilterDateRange([null, null]);
  };

  const performSearch = async (query: string, path: string | null) => {
    setLoading(true);
    setFiles([]);

    try {
      if (!query) {
        if (!path) {
          message.warning('请先选择文件夹再开始搜索');
          return;
        }

        const params = new URLSearchParams({ parent_path: path });
        const response = await fetch(`${API_ENDPOINTS.LIST_FILES}?${params.toString()}`);
        const data = await response.json();

        if (!response.ok) {
          throw new Error(data.detail || data.message || '获取文件列表失败');
        }

        const mappedFiles = mapListResults(data.results || [], path);
        setFiles(mappedFiles);
        if (mappedFiles.length === 0) {
          message.info('当前文件夹为空');
        }
        return;
      }

      const params = new URLSearchParams({ q: query, k: '30', decay_rate: '-1' });

      if (filterExtensions.trim()) {
        params.append('file_extensions', filterExtensions.split(/\s+/).filter(Boolean).join(','));
      }

      const minSizeBytes = convertSizeToBytes(filterMinSize, filterMinSizeUnit);
      const maxSizeBytes = convertSizeToBytes(filterMaxSize, filterMaxSizeUnit);
      if (minSizeBytes) params.append('min_size', minSizeBytes.toString());
      if (maxSizeBytes) params.append('max_size', maxSizeBytes.toString());
      if (filterDateRange[0]) params.append('min_modified', Math.floor(filterDateRange[0].valueOf() / 1000).toString());
      if (filterDateRange[1]) params.append('max_modified', Math.floor(filterDateRange[1].valueOf() / 1000).toString());

      const response = await fetch(`${API_ENDPOINTS.VECTOR_SEARCH}?${params.toString()}`);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || data.message || '语义搜索失败');
      }

      if (data.msg) {
        message.warning(data.msg);
      }

      const mappedFiles = processSemanticSearchResults(data.results, path);
      setFiles(mappedFiles);
      if (mappedFiles.length === 0) {
        message.info('未找到匹配结果');
      }
    } catch (error: unknown) {
      console.error('Search failed:', error);
      message.error((error as Error).message || '搜索失败，请检查后端服务状态');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    if (!searchQuery.trim() && !currentPath) {
      message.warning('请先选择文件夹再开始搜索');
      return;
    }

    performSearch(searchQuery.trim(), currentPath);
  };

  const handlePickFolder = async () => {
    try {
      const data = await apiGet<FolderResponse>(API_ENDPOINTS.PICK_FOLDER);

      if (data.path && !data.cancelled) {
        setCurrentPath(data.path);
        clearResults();
        message.success(`已选择文件夹: ${data.path}`);
        await performSearch('', data.path);
        return;
      }

      if (data.cancelled) {
        message.info('已取消选择文件夹');
        return;
      }

      if (data.error) {
        message.error(data.error);
        return;
      }

      message.error('选择文件夹失败');
    } catch (error) {
      console.error('选择文件夹失败:', error);
      message.error('选择文件夹失败');
    }
  };

  const handleSetFolder = async (path: string) => {
    if (!path.trim()) {
      message.error('请输入文件夹路径');
      return;
    }

    try {
      const data = await apiPost<SetFolderResponse>(API_ENDPOINTS.SET_FOLDER, { path });
      if (!data.success) {
        message.error(data.error || '设置文件夹失败');
        return;
      }

      const nextPath = data.path || path;
      setCurrentPath(nextPath);
      setShowPathInput(false);
      setInputPath('');
      clearResults();
      message.success(data.message || '文件夹设置成功');
      await performSearch('', nextPath);
    } catch (error) {
      console.error('设置文件夹失败:', error);
      message.error('设置文件夹失败');
    }
  };

  const handleOpenFile = async (path: string) => {
    try {
      const response = await fetch(`${API_ENDPOINTS.OPEN_FILE}?path=${encodeURIComponent(path)}`);
      if (!response.ok) {
        throw new Error('打开文件失败');
      }
    } catch {
      message.error('打开文件失败');
    }
  };

  const handleOpenFolder = async (path: string) => {
    try {
      const response = await fetch(`${API_ENDPOINTS.OPEN_FOLDER}?path=${encodeURIComponent(path)}`);
      if (!response.ok) {
        throw new Error('打开文件夹失败');
      }
    } catch {
      message.error('打开文件夹失败');
    }
  };

  return {
    searchQuery,
    setSearchQuery,
    files,
    loading,
    currentPath,
    showPathInput,
    setShowPathInput,
    inputPath,
    setInputPath,
    showFilterModal,
    setShowFilterModal,
    filterExtensions,
    setFilterExtensions,
    filterMinSize,
    setFilterMinSize,
    filterMaxSize,
    setFilterMaxSize,
    filterMinSizeUnit,
    setFilterMinSizeUnit,
    filterMaxSizeUnit,
    setFilterMaxSizeUnit,
    filterDateRange,
    setFilterDateRange,
    handleSearch,
    handlePickFolder,
    handleSetFolder,
    handleOpenFile,
    handleOpenFolder,
    resetFilters,
  };
}
