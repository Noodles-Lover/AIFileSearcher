import { useEffect } from 'react';
import type { CSSProperties } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { message, Spin } from 'antd';
import Home from './pages/Home';
import Settings from './pages/Settings';
import { ModelLoadingProvider, useModelLoading } from './context/ModelLoadingContext';
import { autoLoadLLM } from './utils/llmLoader';
import { loadSettings } from './utils/settingsManager';
import './App.css';

const overlayStyle: CSSProperties = {
  position: 'fixed',
  inset: 0,
  zIndex: 9999,
  background: 'rgba(0, 0, 0, 0.45)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
};

const cardStyle: CSSProperties = {
  background: '#fff',
  borderRadius: 8,
  padding: '32px 48px',
  boxShadow: '0 4px 24px rgba(0, 0, 0, 0.2)',
  textAlign: 'center',
  minWidth: 360,
};

function AutoLLMInitializer() {
  const { startLoading, updateDetail, stopLoading } = useModelLoading();

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const settings = await loadSettings();
      if (cancelled) return;
      const kind = settings.llm_provider === 'deepseek' ? 'DeepSeek API 模型' : '本地 LLM 模型';
      startLoading(kind, settings.llm_model || '正在连接后端服务...');
      autoLoadLLM((ev) => {
        if (ev.model) updateDetail(ev.model);
      })
        .catch((err) => {
          if (cancelled) return;
          console.error('模型自动加载失败:', err);
          message.error(`模型加载失败：${err instanceof Error ? err.message : err}`);
        })
        .finally(() => {
          if (!cancelled) stopLoading();
        });
    })();
    return () => {
      cancelled = true;
    };
  }, [startLoading, updateDetail, stopLoading]);

  return null;
}

function LoadingOverlay() {
  const { loading } = useModelLoading();

  useEffect(() => {
    document.body.style.overflow = loading ? 'hidden' : '';
    return () => {
      document.body.style.overflow = '';
    };
  }, [loading]);

  if (!loading) return null;

  return (
    <div style={overlayStyle}>
      <div style={cardStyle}>
        <Spin size="large" />
        <div style={{ marginTop: 20, fontSize: 16, fontWeight: 500 }}>正在加载{loading.model}</div>
        <div style={{ marginTop: 8, color: '#666' }}>{loading.detail}</div>
        <div style={{ marginTop: 16, color: '#999', fontSize: 12 }}>加载期间请勿操作</div>
      </div>
    </div>
  );
}

function App() {
  return (
    <ModelLoadingProvider>
      <Router>
        <AutoLLMInitializer />
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
        <LoadingOverlay />
      </Router>
    </ModelLoadingProvider>
  );
}

export default App;
