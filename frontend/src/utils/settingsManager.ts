export interface AppSettings {
  include_subfolders: boolean;
  embedding_model: string;
  llm_provider: 'local' | 'deepseek';
  llm_model: string;
  deepseek_api_key: string;
  query_rewrite_enabled: boolean;
  llm_auto_filter_enabled: boolean;  // LLM自动识别并应用过滤范围
  index_type: string;  // FAISS索引类型
}

const SETTINGS_STORAGE_KEY = 'ai-file-searcher-settings';
const SETTINGS_FILE_PATH = 'local_data/settings.json';

const DEFAULT_SETTINGS: AppSettings = {
  include_subfolders: false,
  embedding_model: '',
  llm_provider: 'local',
  llm_model: '',
  deepseek_api_key: '',
  query_rewrite_enabled: false,
  llm_auto_filter_enabled: true,  // 默认开启LLM自动过滤
  index_type: 'IndexFlatL2',  // 默认FAISS索引类型
};

type FileBridge = {
  readTextFile: (relativePath: string, callback: (content: string) => void) => void;
  writeTextFile: (relativePath: string, content: string, callback: (success: boolean) => void) => void;
  listDirectories: (relativePath: string, callback: (content: string) => void) => void;
};

declare global {
  interface Window {
    qt?: {
      webChannelTransport?: unknown;
    };
    QWebChannel?: new (
      transport: unknown,
      callback: (channel: { objects: { fileBridge: FileBridge } }) => void
    ) => void;
  }
}

let cachedSettings: AppSettings | null = null;
let bridgePromise: Promise<FileBridge | null> | null = null;

function mergeSettings(
  settings?: Partial<AppSettings> | (Partial<AppSettings> & { recursive_folder_listing?: boolean }) | null
): AppSettings {
  const nextSettings: Partial<AppSettings> & { recursive_folder_listing?: boolean } = { ...(settings || {}) };

  if (typeof nextSettings.recursive_folder_listing === 'boolean' && typeof nextSettings.include_subfolders !== 'boolean') {
    nextSettings.include_subfolders = nextSettings.recursive_folder_listing;
  }

  return { ...DEFAULT_SETTINGS, ...nextSettings };
}

function loadLocalSettings(): AppSettings {
  try {
    const rawSettings = window.localStorage.getItem(SETTINGS_STORAGE_KEY);
    if (!rawSettings) {
      return DEFAULT_SETTINGS;
    }

    return mergeSettings(JSON.parse(rawSettings));
  } catch {
    return DEFAULT_SETTINGS;
  }
}

function saveLocalSettings(settings: AppSettings): AppSettings {
  window.localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(settings));
  return settings;
}

function ensureQWebChannelScript(): Promise<void> {
  return new Promise((resolve) => {
    if (window.QWebChannel) {
      resolve();
      return;
    }

    const existingScript = document.querySelector('script[data-qwebchannel="true"]') as HTMLScriptElement | null;
    if (existingScript) {
      existingScript.addEventListener('load', () => resolve(), { once: true });
      existingScript.addEventListener('error', () => resolve(), { once: true });
      return;
    }

    const script = document.createElement('script');
    script.src = 'qrc:///qtwebchannel/qwebchannel.js';
    script.dataset.qwebchannel = 'true';
    script.onload = () => resolve();
    script.onerror = () => resolve();
    document.head.appendChild(script);
  });
}

async function getFileBridge(): Promise<FileBridge | null> {
  if (bridgePromise) {
    return bridgePromise;
  }

  bridgePromise = (async () => {
    if (!window.qt?.webChannelTransport) {
      return null;
    }

    await ensureQWebChannelScript();
    if (!window.QWebChannel) {
      return null;
    }

    return new Promise<FileBridge | null>((resolve) => {
      new window.QWebChannel!(window.qt!.webChannelTransport!, (channel) => {
        resolve(channel.objects.fileBridge || null);
      });
    });
  })();

  return bridgePromise;
}

export async function loadSettings(forceRefresh = false): Promise<AppSettings> {
  if (cachedSettings && !forceRefresh) {
    return cachedSettings;
  }

  const bridge = await getFileBridge();

  if (!bridge) {
    cachedSettings = loadLocalSettings();
    return cachedSettings;
  }

  cachedSettings = await new Promise<AppSettings>((resolve) => {
    bridge.readTextFile(SETTINGS_FILE_PATH, (settingsJson) => {
      try {
        resolve(settingsJson ? mergeSettings(JSON.parse(settingsJson)) : DEFAULT_SETTINGS);
      } catch {
        resolve(DEFAULT_SETTINGS);
      }
    });
  });

  return cachedSettings;
}

export async function saveSettings(nextSettings: Partial<AppSettings>): Promise<AppSettings> {
  const mergedSettings = mergeSettings({ ...(await loadSettings()), ...nextSettings });
  const bridge = await getFileBridge();

  if (!bridge) {
    cachedSettings = saveLocalSettings(mergedSettings);
    return cachedSettings;
  }

  cachedSettings = await new Promise<AppSettings>((resolve, reject) => {
    bridge.writeTextFile(SETTINGS_FILE_PATH, JSON.stringify(mergedSettings, null, 2), (success) => {
      if (!success) {
        reject(new Error('Failed to write settings file'));
        return;
      }

      resolve(mergedSettings);
    });
  });

  return cachedSettings;
}

export async function listAvailableModels(): Promise<string[]> {
  return [DEFAULT_SETTINGS.embedding_model];
}

export async function listEmbeddingModels(): Promise<string[]> {
  const bridge = await getFileBridge();

  if (!bridge) {
    return [DEFAULT_SETTINGS.embedding_model];
  }

  return new Promise<string[]>((resolve) => {
    bridge.listDirectories('models/embedding', (directoryJson) => {
      try {
        const directories = JSON.parse(directoryJson);
        if (!Array.isArray(directories) || directories.length === 0) {
          resolve([DEFAULT_SETTINGS.embedding_model]);
          return;
        }

        resolve(directories);
      } catch {
        resolve([DEFAULT_SETTINGS.embedding_model]);
      }
    });
  });
}

export async function listLLMModels(): Promise<string[]> {
  const bridge = await getFileBridge();

  if (!bridge) {
    return [];
  }

  return new Promise<string[]>((resolve) => {
    bridge.listDirectories('models/LLM', (directoryJson) => {
      try {
        const directories = JSON.parse(directoryJson);
        if (!Array.isArray(directories) || directories.length === 0) {
          resolve([]);
          return;
        }

        resolve(directories);
      } catch {
        resolve([]);
      }
    });
  });
}
