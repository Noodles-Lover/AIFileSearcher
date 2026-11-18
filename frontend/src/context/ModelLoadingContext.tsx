import { createContext, useCallback, useContext, useMemo, useState } from 'react';
import type { ReactNode } from 'react';

export type ModelKind = '本地 LLM 模型' | '嵌入模型' | 'DeepSeek API 模型';

interface LoadingState {
  model: ModelKind;
  detail: string;
}

interface ModelLoadingContextValue {
  loading: LoadingState | null;
  startLoading: (model: ModelKind, detail: string) => void;
  updateDetail: (detail: string) => void;
  stopLoading: () => void;
}

const ModelLoadingContext = createContext<ModelLoadingContextValue | null>(null);

export function ModelLoadingProvider({ children }: { children: ReactNode }) {
  const [loading, setLoading] = useState<LoadingState | null>(null);

  const startLoading = useCallback((model: ModelKind, detail: string) => {
    setLoading({ model, detail });
  }, []);

  const updateDetail = useCallback((detail: string) => {
    setLoading((prev) => (prev ? { ...prev, detail } : prev));
  }, []);

  const stopLoading = useCallback(() => {
    setLoading(null);
  }, []);

  const value = useMemo(
    () => ({ loading, startLoading, updateDetail, stopLoading }),
    [loading, startLoading, updateDetail, stopLoading],
  );

  return <ModelLoadingContext.Provider value={value}>{children}</ModelLoadingContext.Provider>;
}

export function useModelLoading(): ModelLoadingContextValue {
  const ctx = useContext(ModelLoadingContext);
  if (!ctx) throw new Error('useModelLoading must be used within ModelLoadingProvider');
  return ctx;
}
