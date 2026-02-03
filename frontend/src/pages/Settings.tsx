import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Layout, Button, Typography, Space, Card, Select, InputNumber, Radio, Divider } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';

const { Header, Content } = Layout;
const { Title, Text } = Typography;

const Settings: React.FC = () => {
  const navigate = useNavigate();

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
                  <Text type="secondary" size="small">决定搜索时包含哪些区域</Text>
                </div>
                <Select defaultValue="indexed" style={{ width: 180 }}>
                  <option value="all">全盘搜索</option>
                  <option value="indexed">仅限已索引文件夹</option>
                </Select>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <Text strong>索引深度</Text><br/>
                  <Text type="secondary" size="small">文件夹层级扫描的最大深度</Text>
                </div>
                <InputNumber min={1} max={20} defaultValue={5} />
              </div>
            </Space>
          </Card>

          <Card title="界面外观" variant="borderless">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <Text strong>色彩主题</Text><br/>
                <Text type="secondary" size="small">切换应用的视觉风格</Text>
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
