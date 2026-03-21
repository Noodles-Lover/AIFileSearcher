import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Layout, Button, Typography, Space, Card, Select, InputNumber, Radio, Divider, message, Modal } from 'antd';
import { ArrowLeftOutlined, DeleteOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import { API_ENDPOINTS, apiPost } from '../utils/api';

interface ApiResponse {
  success?: boolean;
  message?: string;
  error?: string;
}

const { Header, Content } = Layout;
const { Title, Text } = Typography;

const Settings: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [cacheLoading, setCacheLoading] = useState(false);

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
          <Card title="常规设置" variant="borderless">
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
          </Card>

          <Card title="空间管理" variant="borderless">
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
          </Card>

          <Card title="界面外观" variant="borderless">
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
          </Card>

          <div style={{ textAlign: 'center', marginTop: '20px' }}>
            <Text type="secondary">AI File Searcher v0.1.0</Text>
          </div>
        </Space>
      </Content>
    </Layout>
  );
};

export default Settings;
