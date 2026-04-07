import React, { useEffect, useState } from 'react';
import type { CSSProperties } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Button,
  Divider,
  Empty,
  InputNumber,
  Layout,
  message,
  Modal,
  Radio,
  Select,
  Space,
  Spin,
  Typography
} from 'antd';
import {
  ArrowLeftOutlined,
  DeleteOutlined,
  ExclamationCircleOutlined,
  FolderOutlined
} from '@ant-design/icons';
import { API_ENDPOINTS, apiGet, apiPost } from '../utils/api';
import SettingSection from '../components/SettingSection';

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
  divider: { margin: '8px 0' },
  row: { display: 'flex', alignItems: 'center', justifyContent: 'space-between' },
  secondaryText: { fontSize: '12px' },
  select: { width: 180 },
  folderList: { maxHeight: '200px', overflowY: 'auto', padding: '4px 0', border: '1px solid #f0f0f0', borderRadius: '8px' },
  folderItem: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 12px', backgroundColor: '#e6f7ff', borderRadius: '6px', transition: 'background-color 0.2s' },
  folderIcon: { color: '#1890ff' },
  folderText: { fontSize: '13px' },
  footer: { marginTop: '20px', textAlign: 'center' },
};

const Settings: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [cacheLoading, setCacheLoading] = useState(false);
  const [folders, setFolders] = useState<string[]>([]);
  const [foldersLoading, setFoldersLoading] = useState(false);
  const [deletingFolder, setDeletingFolder] = useState<string | null>(null);

  const fetchFolders = async () => {
    setFoldersLoading(true);
    try {
      const data = await apiGet<IndexedFoldersResponse>(API_ENDPOINTS.INDEXED_FOLDERS);
      setFolders(data.folders || []);
    } catch (error) {
      console.error('获取已索引文件夹失败:', error);
    } finally {
      setFoldersLoading(false);
    }
  };

  useEffect(() => {
    fetchFolders();
  }, []);

  const handleRemoveFolder = (folderPath: string) => {
    Modal.confirm({
      title: '确认移除索引',
      icon: <ExclamationCircleOutlined />,
      content: `确认要移除 ${folderPath} 的索引数据吗？`,
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
          console.error('移除已索引文件夹失败:', error);
          message.error('移除已索引文件夹失败');
        } finally {
          setDeletingFolder(null);
        }
      }
    });
  };

  const handleClearIndex = async () => {
    Modal.confirm({
      title: '确认清空索引',
      icon: <ExclamationCircleOutlined />,
      content: '这会删除所有向量索引和关联缓存，之后需要重新建立索引。',
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
          console.error('清空索引失败:', error);
          message.error('清空索引失败');
        } finally {
          setLoading(false);
        }
      }
    });
  };

  const handleClearCache = async () => {
    setCacheLoading(true);
    try {
      const data = await apiPost<ApiResponse>(API_ENDPOINTS.CLEAR_CACHE);
      if (data.success) {
        message.success(data.message || '缓存清理完成');
      } else {
        message.error(data.error || '缓存清理失败');
      }
    } catch (error) {
      console.error('清理缓存失败:', error);
      message.error('清理缓存失败');
    } finally {
      setCacheLoading(false);
    }
  };

  return (
    <Layout style={styles.layout}>
      <Header style={styles.header}>
        <Button type="text" icon={<ArrowLeftOutlined />} onClick={() => navigate('/')} style={styles.backButton} />
        <Title level={4} style={styles.title}>应用设置</Title>
      </Header>

      <Content style={styles.content}>
        <Space direction="vertical" size="large" style={styles.fullWidth}>
          <SettingSection title="搜索设置">
            <Space direction="vertical" style={styles.fullWidth} split={<Divider style={styles.divider} />}>
              <div style={styles.row}>
                <div>
                  <Text strong>搜索范围</Text>
                  <br />
                  <Text type="secondary" style={styles.secondaryText}>决定搜索时包含哪些区域</Text>
                </div>
                <Select
                  defaultValue="indexed"
                  style={styles.select}
                  options={[
                    { value: 'all', label: '全部结果' },
                    { value: 'indexed', label: '仅已索引文件夹' },
                  ]}
                />
              </div>

              <div style={styles.row}>
                <div>
                  <Text strong>索引深度</Text>
                  <br />
                  <Text type="secondary" style={styles.secondaryText}>文件夹层级扫描的最大深度</Text>
                </div>
                <InputNumber min={1} max={20} defaultValue={5} />
              </div>
            </Space>
          </SettingSection>

          <SettingSection title="已索引文件夹">
            <Spin spinning={foldersLoading}>
              {folders.length === 0 ? (
                <Empty description="当前还没有已索引的文件夹" image={Empty.PRESENTED_IMAGE_SIMPLE} />
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
            <Space direction="vertical" style={styles.fullWidth} split={<Divider style={styles.divider} />}>
              <div style={styles.row}>
                <div>
                  <Text strong>清空本地索引</Text>
                  <br />
                  <Text type="secondary" style={styles.secondaryText}>删除所有向量索引数据，释放存储空间</Text>
                </div>
                <Button danger icon={<DeleteOutlined />} onClick={handleClearIndex} loading={loading}>
                  清空索引
                </Button>
              </div>

              <div style={styles.row}>
                <div>
                  <Text strong>清理失效缓存</Text>
                  <br />
                  <Text type="secondary" style={styles.secondaryText}>删除不存在文件的缓存记录，优化索引性能</Text>
                </div>
                <Button icon={<DeleteOutlined />} onClick={handleClearCache} loading={cacheLoading}>
                  清理缓存
                </Button>
              </div>
            </Space>
          </SettingSection>

          <SettingSection title="外观">
            <div style={styles.row}>
              <div>
                <Text strong>主题模式</Text>
                <br />
                <Text type="secondary" style={styles.secondaryText}>切换应用的视觉风格</Text>
              </div>
              <Radio.Group defaultValue="light" buttonStyle="solid">
                <Radio.Button value="light">浅色</Radio.Button>
                <Radio.Button value="dark">深色</Radio.Button>
                <Radio.Button value="system">跟随系统</Radio.Button>
              </Radio.Group>
            </div>
          </SettingSection>

          <div style={styles.footer}>
            <Text type="secondary">AI File Searcher v0.1.0</Text>
          </div>
        </Space>
      </Content>
    </Layout>
  );
};

export default Settings;
