import React, { useEffect, useState } from 'react';
import type { CSSProperties } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Button,
  Empty,
  Input,
  Layout,
  message,
  Modal,
  Select,
  Space,
  Spin,
  Switch,
  Typography,
} from 'antd';
import {
  ArrowLeftOutlined,
  DeleteOutlined,
  ExclamationCircleOutlined,
  FolderOutlined,
  KeyOutlined,
} from '@ant-design/icons';

import SettingSection from '../components/SettingSection';
import { API_ENDPOINTS, apiGet, apiPost } from '../utils/api';
import { listEmbeddingModels, listLLMModels, loadSettings, saveSettings } from '../utils/settingsManager';

interface ApiResponse {
  success?: boolean;
  message?: string;
  error?: string;
}

interface IndexedFoldersResponse {
  folders?: string[];
  error?: string;
}

interface ModelsResponse {
  providers?: string[];
  models: string[];
  current_provider?: string;
  current_model: string;
  has_api_key?: boolean;
}

const { Header, Content } = Layout;
const { Text, Title } = Typography;

const styles: Record<string, CSSProperties> = {
  layout: { minHeight: '100vh', background: '#f5f5f7' },
  header: { display: 'flex', alignItems: 'center', padding: '0 24px', background: '#fff', borderBottom: '1px solid #f0f0f0' },
  backButton: { marginRight: '16px' },
  title: { margin: 0 },
  content: { width: '100%', maxWidth: '800px', margin: '0 auto', padding: '40px' },
  fullWidth: { width: '100%' },
  row: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '16px' },
  rowTop: { display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '16px' },
  secondaryText: { fontSize: '12px' },
  folderList: { maxHeight: '200px', overflowY: 'auto', padding: '4px 0', border: '1px solid #f0f0f0', borderRadius: '8px' },
  folderItem: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 12px', backgroundColor: '#e6f7ff', borderRadius: '6px', transition: 'background-color 0.2s' },
  folderIcon: { color: '#1890ff' },
  folderText: { fontSize: '13px' },
  modelSelect: { width: 260 },
};

const Settings: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [cacheLoading, setCacheLoading] = useState(false);
  const [settingsLoading, setSettingsLoading] = useState(true);
  const [settingsSaving, setSettingsSaving] = useState(false);
  const [includeSubfolders, setIncludeSubfolders] = useState(false);
  const [availableEmbeddingModels, setAvailableEmbeddingModels] = useState<string[]>([]);
  const [selectedEmbeddingModel, setSelectedEmbeddingModel] = useState('bge-m3');
  const [availableLLMModels, setAvailableLLMModels] = useState<string[]>([]);
  const [selectedLLMProvider, setSelectedLLMProvider] = useState<'local' | 'deepseek'>('local');
  const [selectedLLMModel, setSelectedLLMModel] = useState('');
  const [deepseekApiKey, setDeepseekApiKey] = useState('');
  const [queryRewriteEnabled, setQueryRewriteEnabled] = useState(false);
  const [selectedIndexType, setSelectedIndexType] = useState('IndexFlatL2');
  const [folders, setFolders] = useState<string[]>([]);
  const [foldersLoading, setFoldersLoading] = useState(false);
  const [deletingFolder, setDeletingFolder] = useState<string | null>(null);

  const AVAILABLE_INDEX_TYPES = ['IndexFlatL2', 'IndexFlatIP', 'IndexIVFFlat', 'IndexHNSWFlat'];

  const fetchFolders = async () => {
    setFoldersLoading(true);
    try {
      const data = await apiGet<IndexedFoldersResponse>(API_ENDPOINTS.INDEXED_FOLDERS);
      setFolders(data.folders || []);
    } catch (error) {
      console.error('Failed to load indexed folders:', error);
    } finally {
      setFoldersLoading(false);
    }
  };

  const fetchSettings = async () => {
    setSettingsLoading(true);
    try {
      const settings = await loadSettings(true);
      setIncludeSubfolders(settings.include_subfolders);
      setSelectedEmbeddingModel(settings.embedding_model || 'bge-m3');
      setSelectedLLMProvider(settings.llm_provider || 'local');
      setSelectedLLMModel(settings.llm_model || '');
      setDeepseekApiKey(settings.deepseek_api_key || '');
      setQueryRewriteEnabled(settings.query_rewrite_enabled || false);
      setSelectedIndexType(settings.index_type || 'IndexFlatL2');

      const [embeddingData, llmData] = await Promise.all([
        apiGet<ModelsResponse>(API_ENDPOINTS.EMBEDDING_MODELS),
        apiGet<ModelsResponse>(API_ENDPOINTS.LLM_MODELS),
      ]);
      setAvailableEmbeddingModels(embeddingData.models || []);
      setAvailableLLMModels(llmData.models || []);
    } catch (error) {
      console.error('Failed to load settings:', error);
      message.error('加载设置失败');
    } finally {
      setSettingsLoading(false);
    }
  };

  useEffect(() => {
    fetchFolders();
    fetchSettings();
  }, []);

  const handleIncludeSubfoldersChange = async (checked: boolean) => {
    setIncludeSubfolders(checked);
    setSettingsSaving(true);
    try {
      const settings = await saveSettings({ include_subfolders: checked });
      setIncludeSubfolders(settings.include_subfolders);
      message.success('设置已保存');
    } catch (error) {
      console.error('Failed to save settings:', error);
      message.error('保存设置失败');
      const settings = await loadSettings(true);
      setIncludeSubfolders(settings.include_subfolders);
    } finally {
      setSettingsSaving(false);
    }
  };

  const handleEmbeddingModelChange = async (modelName: string) => {
    setSelectedEmbeddingModel(modelName);
    setSettingsSaving(true);
    try {
      message.loading({ content: '正在加载嵌入模型...', key: 'embedding' });
      await apiPost(API_ENDPOINTS.EMBEDDING_LOAD, { model_name: modelName });
      await saveSettings({ embedding_model: modelName });
      setSelectedEmbeddingModel(modelName);
      message.success({ content: `嵌入模型 [${modelName}] 加载成功`, key: 'embedding' });
    } catch (error) {
      console.error('Failed to load embedding model:', error);
      message.error({ content: '加载嵌入模型失败', key: 'embedding' });
      const settings = await loadSettings(true);
      setSelectedEmbeddingModel(settings.embedding_model);
    } finally {
      setSettingsSaving(false);
    }
  };

  const handleLLMProviderChange = async (provider: 'local' | 'deepseek') => {
    setSelectedLLMProvider(provider);
    setSettingsSaving(true);
    try {
      if (provider === 'deepseek') {
        // DeepSeek 模式只需要保存 provider
        await saveSettings({ llm_provider: provider });
        message.success('已切换到 DeepSeek API 模式');
      } else {
        // 本地模式
        await saveSettings({ llm_provider: provider });
        message.success('已切换到本地模型模式');
      }
    } catch (error) {
      console.error('Failed to change LLM provider:', error);
      message.error('切换失败');
    } finally {
      setSettingsSaving(false);
    }
  };

  const handleLLMModelChange = async (modelName: string) => {
    setSelectedLLMModel(modelName);
    setSettingsSaving(true);
    try {
      message.loading({ content: '正在加载LLM模型...', key: 'llm' });
      await apiPost(API_ENDPOINTS.LLM_LOAD, { provider: selectedLLMProvider, model_name: modelName });
      await saveSettings({ llm_model: modelName });
      setSelectedLLMModel(modelName);
      message.success({ content: `LLM模型 [${modelName}] 加载成功`, key: 'llm' });
    } catch (error) {
      console.error('Failed to load LLM model:', error);
      message.error({ content: '加载LLM模型失败', key: 'llm' });
      const settings = await loadSettings(true);
      setSelectedLLMModel(settings.llm_model);
    } finally {
      setSettingsSaving(false);
    }
  };

  const handleDeepseekApiKeyChange = async (apiKey: string) => {
    setDeepseekApiKey(apiKey);
  };

  const handleDeepseekApiKeySave = async () => {
    if (!deepseekApiKey.trim()) {
      message.warning('请输入 API Key');
      return;
    }
    setSettingsSaving(true);
    try {
      message.loading({ content: '正在配置 DeepSeek API...', key: 'deepseek' });
      await apiPost(API_ENDPOINTS.LLM_CONFIG, {
        provider: 'deepseek',
        api_key: deepseekApiKey.trim(),
        model_name: 'deepseek-chat',
      });
      await saveSettings({ deepseek_api_key: deepseekApiKey.trim() });
      message.success({ content: 'DeepSeek API 配置成功', key: 'deepseek' });
    } catch (error) {
      console.error('Failed to config DeepSeek API:', error);
      message.error({ content: 'DeepSeek API 配置失败', key: 'deepseek' });
    } finally {
      setSettingsSaving(false);
    }
  };

  const handleQueryRewriteChange = async (checked: boolean) => {
    setQueryRewriteEnabled(checked);
    setSettingsSaving(true);
    try {
      const settings = await saveSettings({ query_rewrite_enabled: checked });
      setQueryRewriteEnabled(settings.query_rewrite_enabled);
      message.success('查询重写设置已保存');
    } catch (error) {
      console.error('Failed to save query rewrite setting:', error);
      message.error('保存查询重写设置失败');
      const settings = await loadSettings(true);
      setQueryRewriteEnabled(settings.query_rewrite_enabled);
    } finally {
      setSettingsSaving(false);
    }
  };

  const handleIndexTypeChange = async (indexType: string) => {
    if (indexType === selectedIndexType) return;

    Modal.confirm({
      title: '确认更改索引类型？',
      icon: <ExclamationCircleOutlined />,
      content: `更改索引类型将清除所有现有索引数据，确定要继续吗？`,
      okText: '确认更改',
      cancelText: '取消',
      okType: 'danger',
      onOk: async () => {
        setSettingsSaving(true);
        setLoading(true);
        try {
          await saveSettings({ index_type: indexType });
          await apiPost<{ success: boolean; message?: string }>(API_ENDPOINTS.CLEAR_INDEX, {});
          setSelectedIndexType(indexType);
          fetchFolders();
          message.success('索引类型已更改，所有索引数据已清除');
        } catch (error) {
          console.error('Failed to change index type:', error);
          message.error('更改索引类型失败');
        } finally {
          setSettingsSaving(false);
          setLoading(false);
        }
      },
    });
  };

  const handleRemoveFolder = (folderPath: string) => {
    Modal.confirm({
      title: '确认移除索引文件夹？',
      icon: <ExclamationCircleOutlined />,
      content: `将移除 ${folderPath} 的索引数据。`,
      okText: '确认移除',
      cancelText: '取消',
      okType: 'danger',
      onOk: async () => {
        setDeletingFolder(folderPath);
        try {
          const data = await apiPost<ApiResponse>(API_ENDPOINTS.REMOVE_INDEXED_FOLDER, { path: folderPath });
          if (data.success) {
            message.success(data.message || '移除成功');
            fetchFolders();
          } else {
            message.error(data.error || '移除失败');
          }
        } catch (error) {
          console.error('Failed to remove indexed folder:', error);
          message.error('移除索引文件夹失败');
        } finally {
          setDeletingFolder(null);
        }
      },
    });
  };

  const handleClearIndex = async () => {
    Modal.confirm({
      title: '确认清空索引？',
      icon: <ExclamationCircleOutlined />,
      content: '这会删除当前所有向量索引与索引文件夹记录。',
      okText: '清空索引',
      cancelText: '取消',
      okType: 'danger',
      onOk: async () => {
        setLoading(true);
        try {
          await apiPost<ApiResponse>(API_ENDPOINTS.CLEAR_INDEX);
          message.success('索引已清空');
          fetchFolders();
        } catch (error) {
          console.error('Failed to clear index:', error);
          message.error('清空索引失败');
        } finally {
          setLoading(false);
        }
      },
    });
  };

  const handleClearCache = async () => {
    setCacheLoading(true);
    try {
      const data = await apiPost<ApiResponse>(API_ENDPOINTS.CLEAR_CACHE);
      if (data.success) {
        message.success(data.message || '缓存已清理');
      } else {
        message.error(data.error || '清理缓存失败');
      }
    } catch (error) {
      console.error('Failed to clear cache:', error);
      message.error('清理缓存失败');
    } finally {
      setCacheLoading(false);
    }
  };

  const embeddingModelOptions = Array.from(new Set([selectedEmbeddingModel, ...availableEmbeddingModels])).map((model) => ({
    label: model,
    value: model,
  }));

  const llmProviderOptions = [
    { label: '本地模型', value: 'local' },
    { label: 'DeepSeek API', value: 'deepseek' },
  ];

  const llmModelOptions = [
    { label: '未选择', value: '' },
    ...Array.from(new Set([selectedLLMModel, ...availableLLMModels])).map((model) => ({
      label: model,
      value: model,
    })),
  ];

  const indexTypeOptions = AVAILABLE_INDEX_TYPES.map((type) => ({
    label: type,
    value: type,
  }));

  return (
    <Layout style={styles.layout}>
      <Header style={styles.header}>
        <Button type="text" icon={<ArrowLeftOutlined />} onClick={() => navigate('/')} style={styles.backButton} />
        <Title level={4} style={styles.title}>设置</Title>
      </Header>

      <Content style={styles.content}>
        <Space direction="vertical" size="large" style={styles.fullWidth}>
          <SettingSection title="搜索设置">
            <Spin spinning={settingsLoading || settingsSaving}>
              <div style={styles.row}>
                <div>
                  <Text strong>包含子文件夹文件</Text>
                  <br />
                  <Text type="secondary" style={styles.secondaryText}>
                    打开文件夹时是否继续遍历下层文件夹
                  </Text>
                </div>
                <Switch checked={includeSubfolders} onChange={handleIncludeSubfoldersChange} />
              </div>

              <div style={{ ...styles.rowTop, marginTop: '16px' }}>
                <div>
                  <Text strong>嵌入模型</Text>
                  <br />
                  <Text type="secondary" style={styles.secondaryText}>
                    自动读取 `models/embedding` 文件夹。切换模型后建议重建索引，避免出现兼容性问题。
                  </Text>
                </div>
                <Select
                  value={selectedEmbeddingModel}
                  options={embeddingModelOptions}
                  onChange={handleEmbeddingModelChange}
                  style={styles.modelSelect}
                  placeholder="请选择嵌入模型"
                />
              </div>

              <div style={{ ...styles.rowTop, marginTop: '16px' }}>
                <div>
                  <Text strong>LLM 提供商</Text>
                  <br />
                  <Text type="secondary" style={styles.secondaryText}>
                    选择使用本地模型还是 DeepSeek API
                  </Text>
                </div>
                <Select
                  value={selectedLLMProvider}
                  options={llmProviderOptions}
                  onChange={handleLLMProviderChange}
                  style={styles.modelSelect}
                  placeholder="请选择 LLM 提供商"
                />
              </div>

              {selectedLLMProvider === 'deepseek' ? (
                <div style={{ ...styles.rowTop, marginTop: '16px' }}>
                  <div style={{ flex: 1 }}>
                    <Text strong>DeepSeek API Key</Text>
                    <br />
                    <Text type="secondary" style={styles.secondaryText}>
                      输入您的 DeepSeek API Key，用于调用云端大模型
                    </Text>
                    <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
                      <Input.Password
                        value={deepseekApiKey}
                        onChange={(e) => handleDeepseekApiKeyChange(e.target.value)}
                        placeholder="sk-..."
                        style={{ flex: 1 }}
                        prefix={<KeyOutlined />}
                      />
                      <Button type="primary" onClick={handleDeepseekApiKeySave} loading={settingsSaving}>
                        保存
                      </Button>
                    </div>
                  </div>
                </div>
              ) : (
                <div style={{ ...styles.rowTop, marginTop: '16px' }}>
                  <div>
                    <Text strong>本地 LLM 模型</Text>
                    <br />
                    <Text type="secondary" style={styles.secondaryText}>
                      自动读取 `models/LLM` 文件夹。用于查询重写功能。
                    </Text>
                  </div>
                  <Select
                    value={selectedLLMModel}
                    options={llmModelOptions}
                    onChange={handleLLMModelChange}
                    style={styles.modelSelect}
                    placeholder="请选择 LLM 模型"
                  />
                </div>
              )}

              <div style={{ ...styles.rowTop, marginTop: '16px' }}>
                <div>
                  <Text strong>索引类型</Text>
                  <br />
                  <Text type="secondary" style={styles.secondaryText}>
                    切换索引类型会清除所有现有索引数据。IndexFlatL2：精确但慢；IndexIVFFlat：快速但需数据量大。
                  </Text>
                </div>
                <Select
                  value={selectedIndexType}
                  options={indexTypeOptions}
                  onChange={handleIndexTypeChange}
                  style={styles.modelSelect}
                  placeholder="请选择索引类型"
                  disabled={settingsSaving}
                />
              </div>

              <div style={{ ...styles.rowTop, marginTop: '16px' }}>
                <div>
                  <Text strong>启用查询重写</Text>
                  <br />
                  <Text type="secondary" style={styles.secondaryText}>
                    使用LLM优化搜索关键词，提升语义搜索准确率。需要先配置好 LLM。
                  </Text>
                </div>
                <Switch
                  checked={queryRewriteEnabled}
                  onChange={handleQueryRewriteChange}
                  disabled={selectedLLMProvider === 'local' && !selectedLLMModel}
                />
              </div>
            </Spin>
          </SettingSection>

          <SettingSection title="已索引文件夹">
            <Spin spinning={foldersLoading}>
              {folders.length === 0 ? (
                <Empty description="当前还没有已建立索引的文件夹" image={Empty.PRESENTED_IMAGE_SIMPLE} />
              ) : (
                <div style={styles.folderList}>
                  {folders.map((folder) => (
                    <div
                      key={folder}
                      style={styles.folderItem}
                      onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = '#bae7ff'; }}
                      onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = '#e6f7ff'; }}
                    >
                      <Space>
                        <FolderOutlined style={styles.folderIcon} />
                        <Text style={styles.folderText}>{folder}</Text>
                      </Space>
                      <Button
                        type="text"
                        danger
                        size="small"
                        icon={<DeleteOutlined />}
                        onClick={() => handleRemoveFolder(folder)}
                        loading={deletingFolder === folder}
                      >
                        移除
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </Spin>
          </SettingSection>

          <SettingSection title="数据管理">
            <Space direction="vertical" size="middle" style={styles.fullWidth}>
              <div style={styles.row}>
                <div>
                  <Text strong>清空本地索引</Text>
                  <br />
                  <Text type="secondary" style={styles.secondaryText}>删除全部向量索引、元数据和已索引文件夹记录</Text>
                </div>
                <Button danger icon={<DeleteOutlined />} onClick={handleClearIndex} loading={loading}>
                  清空索引
                </Button>
              </div>

              <div style={styles.row}>
                <div>
                  <Text strong>清理失效缓存</Text>
                  <br />
                  <Text type="secondary" style={styles.secondaryText}>移除已经不存在的文件缓存记录，保持索引状态整洁</Text>
                </div>
                <Button icon={<DeleteOutlined />} onClick={handleClearCache} loading={cacheLoading}>
                  清理缓存
                </Button>
              </div>
            </Space>
          </SettingSection>
        </Space>
      </Content>
    </Layout>
  );
};

export default Settings;
