export const API_BASE_URL = 'http://localhost:8000';

export const API_ENDPOINTS = {
  SEARCH: `${API_BASE_URL}/api/search`,
  VECTOR_SEARCH: `${API_BASE_URL}/api/vector_search`,
  LIST_FILES: `${API_BASE_URL}/api/list`,
  INDEX_FOLDER: `${API_BASE_URL}/api/index_folder`,
  INDEXED_FOLDERS: `${API_BASE_URL}/api/indexed_folders`,
  REMOVE_INDEXED_FOLDER: `${API_BASE_URL}/api/remove_indexed_folder`,
  CLEAR_INDEX: `${API_BASE_URL}/api/clear_index`,
  CLEAR_CACHE: `${API_BASE_URL}/api/clear_cache`,
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

export async function apiRequest<T>(url: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(url, {
    headers: DEFAULT_HEADERS,
    ...options,
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

export async function apiGet<T>(url: string): Promise<T> {
  return apiRequest<T>(url, { method: 'GET' });
}

export async function apiPost<T>(url: string, data?: Record<string, unknown>): Promise<T> {
  return apiRequest<T>(url, {
    method: 'POST',
    body: data ? JSON.stringify(data) : undefined,
  });
}
