import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Layout, Button, Typography, Space, Select, InputNumber, Radio, Divider, message, Modal, Empty, Spin } from 'antd';
import { ArrowLeftOutlined, DeleteOutlined, ExclamationCircleOutlined, FolderOutlined } from '@ant-design/icons';
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
      title: '确认删除索引',
      icon: <ExclamationCircleOutlined />,
      content: `确定要删除 ${folderPath} 的所有索引数据吗？`,
      okText: '确认删除',
      cancelText: '取消',
      okType: 'danger',
      onOk: async () => {
        setDeletingFolder(folderPath);
        try {
          const data = await apiPost<ApiResponse>(API_ENDPOINTS.REMOVE_INDEXED_FOLDER, { path: folderPath });
          if (data.success) {
            message.success(data.message || '删除成功');
            fetchFolders();
          } else {
            message.error(data.error || '删除失败');
          }
        } catch (error) {
          console.error('删除文件夹索引失败:', error);
          message.error('删除文件夹索引失败');
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
      content: '此操作将删除所有向量索引数据和元数据，需要重新建立索引才能进行语义搜索。确定要继续吗？',
      okText: '确认清空',
      cancelText: '取消',
      okType: 'danger',
      onOk: async () => {
        setLoading(true);
        try {
          await apiPost(API_ENDPOINTS.CLEAR_INDEX);
          message.success('索引已成功清空');
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
        message.success(data.message || '清理缓存成功');
      } else {
        message.error(data.error || '清理缓存失败');
      }
    } catch (error) {
      console.error('清理缓存失败:', error);
      message.error('清理缓存失败');
    } finally {
      setCacheLoading(false);
    }
  };

  return (
    <Layout style={{ minHeight: '100vh', background: '#f5f5f7' }}>
      <Header style={{ 
        background: '#fff', 
        padding: '0 24px', 
        display: 'flex', 
        alignItems: 'center',
        borderBottom: '1px solid #f0f0f0'
      }}>
        <Button 
          type="text" 
          icon={<ArrowLeftOutlined />} 
          onClick={() => navigate('/')}
          style={{ marginRight: '16px' }}
        />
        <Title level={4} style={{ margin: 0 }}>应用设置</Title>
      </Header>
      
      <Content style={{ padding: '40px', maxWidth: '800px', margin: '0 auto', width: '100%' }}>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <SettingSection title="常规设置">
            <Space direction="vertical" style={{ width: '100%' }} split={<Divider style={{ margin: '8px 0' }} />}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <Text strong>搜索范围</Text><br/>
                  <Text type="secondary" style={{ fontSize: '12px' }}>决定搜索时包含哪些区域</Text>
                </div>
                <Select 
                  defaultValue="indexed" 
                  style={{ width: 180 }}
                  options={[
                    { value: 'all', label: '全盘搜索' },
                    { value: 'indexed', label: '仅限已索引文件夹' },
                  ]}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <Text strong>索引深度</Text><br/>
                  <Text type="secondary" style={{ fontSize: '12px' }}>文件夹层级扫描的最大深度</Text>
                </div>
                <InputNumber min={1} max={20} defaultValue={5} />
              </div>
            </Space>
          </SettingSection>

          <SettingSection title="已索引文件夹">
            <Spin spinning={foldersLoading}>
              {folders.length === 0 ? (
                <Empty 
                  description="暂无已索引的文件夹" 
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                />
              ) : (
                <div style={{ 
                  maxHeight: '200px', 
                  overflowY: 'auto',
                  border: '1px solid #f0f0f0',
                  borderRadius: '8px',
                  padding: '4px 0'
                }}>
                  {folders.map((folder) => (
                    <div 
                      key={folder}
                      style={{ 
                        display: 'flex', 
                        justifyContent: 'space-between', 
                        alignItems: 'center',
                        padding: '8px 12px',
                        borderRadius: '6px',
                        transition: 'background-color 0.2s',
                        backgroundColor: '#e6f7ff',
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#bae7ff')}
                      onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = '#e6f7ff')}
                    >
                      <Space>
                        <FolderOutlined style={{ color: '#1890ff' }} />
                        <Text style={{ fontSize: '13px' }}>{folder}</Text>
                      </Space>
                      <Button 
                        type="text" 
                        danger 
                        size="small"
                        icon={<DeleteOutlined />}
                        onClick={() => handleRemoveFolder(folder)}
                        loading={deletingFolder === folder}
                      >
                        删除
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </Spin>
          </SettingSection>

          <SettingSection title="空间管理">
            <Space direction="vertical" style={{ width: '100%' }} split={<Divider style={{ margin: '8px 0' }} />}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <Text strong>清空本地索引</Text><br/>
                  <Text type="secondary" style={{ fontSize: '12px' }}>删除所有向量索引数据，释放存储空间</Text>
                </div>
                <Button 
                  danger 
                  icon={<DeleteOutlined />} 
                  onClick={handleClearIndex}
                  loading={loading}
                >
                  清空索引
                </Button>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <Text strong>清理无用缓存</Text><br/>
                  <Text type="secondary" style={{ fontSize: '12px' }}>删除不存在文件的缓存记录，优化索引性能</Text>
                </div>
                <Button 
                  icon={<DeleteOutlined />} 
                  onClick={handleClearCache}
                  loading={cacheLoading}
                >
                  清理缓存
                </Button>
              </div>
            </Space>
          </SettingSection>

          <SettingSection title="界面外观">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <Text strong>色彩主题</Text><br/>
                <Text type="secondary" style={{ fontSize: '12px' }}>切换应用的视觉风格</Text>
              </div>
              <Radio.Group defaultValue="light" buttonStyle="solid">
                <Radio.Button value="light">浅色</Radio.Button>
                <Radio.Button value="dark">深色</Radio.Button>
                <Radio.Button value="system">跟随系统</Radio.Button>
              </Radio.Group>
            </div>
          </SettingSection>

          <div style={{ textAlign: 'center', marginTop: '20px' }}>
            <Text type="secondary">AI File Searcher v0.1.0</Text>
          </div>
        </Space>
      </Content>
    </Layout>
  );
};

export default Settings;