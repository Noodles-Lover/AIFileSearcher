import { useEffect, useState } from 'react';
import type { CSSProperties } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import Settings from './pages/Settings';
import { autoLoadLLM } from './utils/llmLoader';
import './App.css';

const llmBarStyle: CSSProperties = {
  position: 'fixed',
  bottom: 0,
  left: 0,
  right: 0,
  zIndex: 999,
  padding: '6px 16px',
  background: '#e6f7ff',
  borderTop: '1px solid #91d5ff',
  fontSize: '13px',
  color: '#1890ff',
};

function App() {
  const [llmMsg, setLlmMsg] = useState<string | null>('正在连接后端服务...');

  useEffect(() => {
    autoLoadLLM((ev) => {
      if (ev.msg) setLlmMsg(ev.msg);
    })
      .then(() => setLlmMsg(null))
      .catch((err) => {
        setLlmMsg(null);
        console.error('LLM 自动加载失败:', err);
      });
  }, []);

  return (
    <Router>
      {llmMsg && <div style={llmBarStyle}>⏳ {llmMsg}</div>}
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Router>
  );
}

export default App;
