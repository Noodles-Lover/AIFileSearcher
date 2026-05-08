import { useEffect, useState } from 'react';
import dayjs from 'dayjs';
import { message } from 'antd';
import type { FileItem } from '../../components/FileIcon';
import { API_ENDPOINTS, apiGet, apiPost } from '../api';
import { convertSizeToBytes, getRelativePath, processSemanticSearchResults } from '../fileUtils';
import { loadSettings } from '../settingsManager';

interface LLMFilters {
  extensions?: string[];
  time_range?: {
    min?: string;
    max?: string;
  } | null;
  size_range?: {
    min?: number;
    max?: number;
  } | null;
}

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

const HOME_STATE_STORAGE_KEY = 'ai-file-searcher-home-state';

interface HomeStateCache {
  searchQuery: string;
  files: FileItem[];
  currentPath: string | null;
  filterExtensions: string;
  filterMinSize: number | null;
  filterMaxSize: number | null;
  filterMinSizeUnit: string;
  filterMaxSizeUnit: string;
  filterDateRange: [string | null, string | null];
}

function loadCachedHomeState(): HomeStateCache | null {
  try {
    const rawState = window.sessionStorage.getItem(HOME_STATE_STORAGE_KEY);
    if (!rawState) {
      return null;
    }

    return JSON.parse(rawState) as HomeStateCache;
  } catch (error) {
    console.error('Failed to restore home state:', error);
    return null;
  }
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
  const cachedState = loadCachedHomeState();

  const [searchQuery, setSearchQuery] = useState(cachedState?.searchQuery || '');
  const [files, setFiles] = useState<FileItem[]>(Array.isArray(cachedState?.files) ? cachedState!.files : []);
  const [loading, setLoading] = useState(false);
  const [currentPath, setCurrentPath] = useState<string | null>(cachedState?.currentPath || null);
  const [showPathInput, setShowPathInput] = useState(false);
  const [inputPath, setInputPath] = useState('');
  const [showFilterModal, setShowFilterModal] = useState(false);
  const [filterExtensions, setFilterExtensions] = useState(cachedState?.filterExtensions || '');
  const [filterMinSize, setFilterMinSize] = useState<number | null>(cachedState?.filterMinSize ?? null);
  const [filterMaxSize, setFilterMaxSize] = useState<number | null>(cachedState?.filterMaxSize ?? null);
  const [filterMinSizeUnit, setFilterMinSizeUnit] = useState(cachedState?.filterMinSizeUnit || 'B');
  const [filterMaxSizeUnit, setFilterMaxSizeUnit] = useState(cachedState?.filterMaxSizeUnit || 'B');
  const [filterDateRange, setFilterDateRange] = useState<[any, any]>([
    cachedState?.filterDateRange?.[0] ? dayjs(cachedState.filterDateRange[0]) : null,
    cachedState?.filterDateRange?.[1] ? dayjs(cachedState.filterDateRange[1]) : null,
  ]);

  // LLM识别的过滤条件
  const [llmFilters, setLlmFilters] = useState<LLMFilters | null>(null);
  const [appliedFilters, setAppliedFilters] = useState<Record<string, any> | null>(null);
  const [llmAutoFilterEnabled, setLlmAutoFilterEnabled] = useState(true);  // 与全局设置同步

  // 加载全局设置中的LLM自动过滤开关状态
  useEffect(() => {
    const loadSetting = async () => {
      try {
        const settings = await loadSettings();
        setLlmAutoFilterEnabled(settings.llm_auto_filter_enabled !== false);
      } catch (error) {
        console.error('Failed to load LLM auto filter setting:', error);
      }
    };
    loadSetting();
  }, []);

  useEffect(() => {
    try {
      const cachedState: HomeStateCache = {
        searchQuery,
        files,
        currentPath,
        filterExtensions,
        filterMinSize,
        filterMaxSize,
        filterMinSizeUnit,
        filterMaxSizeUnit,
        filterDateRange: [
          filterDateRange[0]?.toISOString?.() || null,
          filterDateRange[1]?.toISOString?.() || null,
        ],
      };

      window.sessionStorage.setItem(HOME_STATE_STORAGE_KEY, JSON.stringify(cachedState));
    } catch (error) {
      console.error('Failed to cache home state:', error);
    }
  }, [
    searchQuery,
    files,
    currentPath,
    filterExtensions,
    filterMinSize,
    filterMaxSize,
    filterMinSizeUnit,
    filterMaxSizeUnit,
    filterDateRange,
  ]);

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

        const params = new URLSearchParams({
          parent_path: path,
        });
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

      // 解析LLM识别的过滤条件
      if (data.llm_filters && llmAutoFilterEnabled) {
        setLlmFilters(data.llm_filters);

        // 将LLM识别的条件直接填充到过滤弹窗的输入栏内（覆盖所有字段）
        const llmFilters = data.llm_filters;

        // 文件扩展名 - 始终覆盖
        if (llmFilters.extensions && llmFilters.extensions.length > 0) {
          setFilterExtensions(llmFilters.extensions.join(' '));
        } else {
          setFilterExtensions('');
        }

        // 时间范围 - 始终覆盖
        const dates: [any, any] = [null, null];
        if (llmFilters.time_range) {
          if (llmFilters.time_range.min) {
            dates[0] = dayjs(llmFilters.time_range.min);
          }
          if (llmFilters.time_range.max) {
            dates[1] = dayjs(llmFilters.time_range.max);
          }
        }
        setFilterDateRange(dates);

        // 文件大小 - 始终覆盖
        // min_size
        if (llmFilters.size_range && llmFilters.size_range.min !== undefined && llmFilters.size_range.min !== null) {
          const sizeInMB = llmFilters.size_range.min / 1048576;
          if (sizeInMB >= 1024) {
            setFilterMinSize(sizeInMB / 1024);
            setFilterMinSizeUnit('GB');
          } else if (sizeInMB >= 1) {
            setFilterMinSize(sizeInMB);
            setFilterMinSizeUnit('MB');
          } else if (llmFilters.size_range.min >= 1024) {
            setFilterMinSize(llmFilters.size_range.min / 1024);
            setFilterMinSizeUnit('KB');
          } else {
            setFilterMinSize(llmFilters.size_range.min);
            setFilterMinSizeUnit('B');
          }
        } else {
          setFilterMinSize(null);
          setFilterMinSizeUnit('B');
        }

        // max_size
        if (llmFilters.size_range && llmFilters.size_range.max !== undefined && llmFilters.size_range.max !== null) {
          const sizeInMB = llmFilters.size_range.max / 1048576;
          if (sizeInMB >= 1024) {
            setFilterMaxSize(sizeInMB / 1024);
            setFilterMaxSizeUnit('GB');
          } else if (sizeInMB >= 1) {
            setFilterMaxSize(sizeInMB);
            setFilterMaxSizeUnit('MB');
          } else if (llmFilters.size_range.max >= 1024) {
            setFilterMaxSize(llmFilters.size_range.max / 1024);
            setFilterMaxSizeUnit('KB');
          } else {
            setFilterMaxSize(llmFilters.size_range.max);
            setFilterMaxSizeUnit('B');
          }
        } else {
          setFilterMaxSize(null);
          setFilterMaxSizeUnit('B');
        }

        setAppliedFilters(data.applied_filters);
        message.info('LLM已自动填充过滤条件，您可以直接修改');
      } else {
        setLlmFilters(null);
        setAppliedFilters(null);
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
    llmFilters,
    appliedFilters,
    llmAutoFilterEnabled,
    setLlmAutoFilterEnabled,
    handleSearch,
    handlePickFolder,
    handleSetFolder,
    handleOpenFile,
    handleOpenFolder,
    resetFilters,
  };
}
