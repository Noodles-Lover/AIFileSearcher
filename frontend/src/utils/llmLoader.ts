import { API_BASE_URL, API_ENDPOINTS, DEFAULT_HEADERS } from './api';

export interface LlmLoadEvent {
  status: 'loading' | 'complete' | 'error';
  stage?: string;
  msg?: string;
}

/** 等待后端服务就绪（startup 期间嵌入模型加载、端口未监听时请求会失败） */
export async function waitForBackend(maxSeconds = 600): Promise<void> {
  const deadline = Date.now() + maxSeconds * 1000;
  while (Date.now() < deadline) {
    try {
      const resp = await fetch(`${API_BASE_URL}/`, { method: 'GET' });
      if (resp.ok) return;
    } catch {
      // 后端未监听，继续轮询
    }
    await new Promise((r) => setTimeout(r, 500));
  }
  throw new Error('后端服务未就绪');
}

/** 调用 /api/llm/load（SSE），逐事件回调；error 事件以异常抛出 */
export async function loadLLMStream(
  body: { provider?: string; model_name?: string; force?: boolean },
  onEvent?: (ev: LlmLoadEvent) => void,
): Promise<void> {
  const resp = await fetch(API_ENDPOINTS.LLM_LOAD, {
    method: 'POST',
    headers: DEFAULT_HEADERS,
    body: JSON.stringify(body),
  });
  if (!resp.ok || !resp.body) {
    throw new Error(`LLM 加载请求失败: ${resp.status}`);
  }

  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let finalError: string | null = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';
    for (const line of lines) {
      if (!line.startsWith('data: ')) continue;
      try {
        const ev = JSON.parse(line.slice(6)) as LlmLoadEvent;
        onEvent?.(ev);
        if (ev.status === 'error') finalError = ev.msg || '模型加载失败';
      } catch {
        // 忽略无法解析的行
      }
    }
  }
  if (finalError) throw new Error(finalError);
}

// 应用启动后的自动加载：StrictMode 双挂载/重复调用共享同一次加载
let autoLoadPromise: Promise<void> | null = null;

export function autoLoadLLM(onEvent?: (ev: LlmLoadEvent) => void): Promise<void> {
  if (!autoLoadPromise) {
    autoLoadPromise = (async () => {
      await waitForBackend();
      // body 为空时由后端按 settings 决定 provider 与模型
      await loadLLMStream({}, onEvent);
    })();
    autoLoadPromise.catch(() => {
      // 允许失败后重试
      autoLoadPromise = null;
    });
  }
  return autoLoadPromise;
}
