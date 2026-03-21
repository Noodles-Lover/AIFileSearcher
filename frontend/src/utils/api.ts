/**
 * API 工具模块
 * 统一管理 API 相关的配置和常量
 */

export const API_BASE_URL = 'http://localhost:8000';

export const API_ENDPOINTS = {
  // 搜索相关
  SEARCH: `${API_BASE_URL}/api/search`,
  VECTOR_SEARCH: `${API_BASE_URL}/api/vector_search`,
  LIST_FILES: `${API_BASE_URL}/api/list`,
  
  // 索引相关
  INDEX_FOLDER: `${API_BASE_URL}/api/index_folder`,
  CLEAR_INDEX: `${API_BASE_URL}/api/clear_index`,
  CLEAR_CACHE: `${API_BASE_URL}/api/clear_cache`,
  
  // 文件操作相关
  PICK_FOLDER: `${API_BASE_URL}/api/pick-folder`,
  SET_FOLDER: `${API_BASE_URL}/api/set-folder`,
  PREVIEW: `${API_BASE_URL}/api/preview`,
  OPEN_FILE: `${API_BASE_URL}/api/open-file`,
  OPEN_FOLDER: `${API_BASE_URL}/api/open-folder`,
  GET_ICON: `${API_BASE_URL}/api/icon`,
} as const;

export const DEFAULT_HEADERS = {
  'Content-Type': 'application/json',
};

/**
 * 通用的 API 请求函数
 */
export async function apiRequest<T>(
  url: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(url, {
    headers: DEFAULT_HEADERS,
    ...options,
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

/**
 * GET 请求
 */
export async function apiGet<T>(url: string): Promise<T> {
  return apiRequest<T>(url, { method: 'GET' });
}

/**
 * POST 请求
 */
export async function apiPost<T>(
  url: string,
  data?: Record<string, unknown>
): Promise<T> {
  return apiRequest<T>(url, {
    method: 'POST',
    body: data ? JSON.stringify(data) : undefined,
  });
}
