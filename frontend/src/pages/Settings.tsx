import React, { useEffect, useState } from 'react';
import type { CSSProperties } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Button,
  Empty,
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
} from '@ant-design/icons';

import SettingSection from '../components/SettingSection';
import { API_ENDPOINTS, apiGet, apiPost } from '../utils/api';
import { listAvailableModels, loadSettings, saveSettings } from '../utils/settingsManager';

interface ApiResponse {
  success?: boolean;
  message?: string;
  error?: string;
}

interface IndexedFoldersResponse {
  folders?: string[];
  error?: string;
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
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const [selectedModel, setSelectedModel] = useState('bge-m3');
  const [folders, setFolders] = useState<string[]>([]);
  const [foldersLoading, setFoldersLoading] = useState(false);
  const [deletingFolder, setDeletingFolder] = useState<string | null>(null);

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
      const [settings, models] = await Promise.all([loadSettings(true), listAvailableModels()]);
      setIncludeSubfolders(settings.include_subfolders);
      setSelectedModel(settings.embedding_model);
      setAvailableModels(models);
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

  const handleModelChange = async (modelName: string) => {
    setSelectedModel(modelName);
    setSettingsSaving(true);
    try {
      const settings = await saveSettings({ embedding_model: modelName });
      setSelectedModel(settings.embedding_model);
      message.success('模型设置已保存，重启并重建索引后生效');
    } catch (error) {
      console.error('Failed to save model setting:', error);
      message.error('保存模型设置失败');
      const settings = await loadSettings(true);
      setSelectedModel(settings.embedding_model);
    } finally {
      setSettingsSaving(false);
    }
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

  const modelOptions = Array.from(new Set([selectedModel, ...availableModels])).map((model) => ({
    label: model,
    value: model,
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
                    自动读取 `models` 文件夹。切换模型后建议重建索引，避免出现兼容性问题。
                  </Text>
                </div>
                <Select
                  value={selectedModel}
                  options={modelOptions}
                  onChange={handleModelChange}
                  style={styles.modelSelect}
                  placeholder="请选择模型"
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
