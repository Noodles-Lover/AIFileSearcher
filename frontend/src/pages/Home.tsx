import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Input, Button, Table, Space, Layout, Typography, message, Tag } from 'antd';
import { SearchOutlined, FolderOpenOutlined, SettingOutlined, CloseCircleOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';

const { Header, Content } = Layout;
const { Text } = Typography;

interface FileItem {
  key: string;
  name: string;
  path: string;
  size: string;
  modified: string;
}

const Home: React.FC = () => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [files, setFiles] = useState<FileItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [currentPath, setCurrentPath] = useState<string | null>(null);

  const performSearch = async (query: string, path: string | null) => {
    setLoading(true);
    try {
      // 构建 URL参数
      const params = new URLSearchParams();
      if (query) params.append('q', query);
      if (path) params.append('parent_path', path);
      
      // 如果既没有查询词也没有路径，默认显示什么都不做，或者显示根目录？
      // 这里为了体验，如果没有 query 但有 path，就列出 path 下的所有文件
      let url = `http://localhost:8000/api/search?${params.toString()}`;
      
      // 如果只是列出文件夹内容（没有搜索词），可以使用 list 接口，或者让 search 接口处理空 query
      // Everything 如果 query 为空，search 接口可能报错，所以如果是纯浏览模式：
      if (!query && path) {
         url = `http://localhost:8000/api/list?path=${encodeURIComponent(path)}`;
      } else if (!query && !path) {
         // 什么都不做
         setLoading(false);
         return;
      }

      const response = await fetch(url);
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      const data = await response.json();
      
      const mappedFiles = data.results.map((item: any, index: number) => ({
        key: index.toString(),
        name: item.name,
        path: item.path,
        size: item.size,
        modified: item.modified
      }));
      
      setFiles(mappedFiles);
      if (mappedFiles.length === 0) {
        message.info('未找到匹配的文件');
      }
    } catch (error) {
      console.error('Search failed:', error);
      message.error('搜索失败，请确保后端服务已启动');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    if (!searchQuery.trim() && !currentPath) {
      message.warning('请输入搜索关键词或选择文件夹');
      return;
    }
    performSearch(searchQuery, currentPath);
  };

  const handlePickFolder = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/pick-folder');
      const data = await response.json();
      
      if (!data.cancelled && data.path) {
        setCurrentPath(data.path);
        message.success(`当前范围: ${data.path}`);
        // 自动列出该文件夹内容
        setSearchQuery(''); // 清空搜索词，变为浏览模式
        performSearch('', data.path);
      }
    } catch (error) {
      console.error('Pick folder failed:', error);
      message.error('无法打开文件夹选择框');
    }
  };

  const clearPath = () => {
    setCurrentPath(null);
    setFiles([]); // 清空列表
    message.info('已切换回全盘搜索模式');
  };

  const columns: ColumnsType<FileItem> = [
    {
      title: '文件名',
      dataIndex: 'name',
      key: 'name',
      render: (text) => <Text strong color="primary">{text}</Text>,
      sorter: (a, b) => a.name.localeCompare(b.name),
    },
    {
      title: '路径',
      dataIndex: 'path',
      key: 'path',
      render: (text) => <Text type="secondary" style={{ fontSize: '12px' }}>{text}</Text>,
    },
    {
      title: '修改时间',
      dataIndex: 'modified',
      key: 'modified',
      width: 180,
      render: (text) => <Text type="secondary" style={{ fontSize: '12px' }}>{text}</Text>,
    },
    {
      title: '大小',
      dataIndex: 'size',
      key: 'size',
      width: 120,
      align: 'right',
    },
  ];

  return (
    <Layout style={{ minHeight: '100vh', background: '#fff' }}>
      <Header style={{ 
        background: '#fff', 
        padding: '0 24px', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'space-between',
        borderBottom: '1px solid #f0f0f0',
        height: '64px'
      }}>
        <Space size="middle" style={{ flex: 1, maxWidth: '600px' }}>
          <Input 
            prefix={<SearchOutlined style={{ color: '#bfbfbf' }} />}
            placeholder={currentPath ? `在 ${currentPath.split('\\').pop()} 中搜索...` : "搜索本地文件..."}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onPressEnter={handleSearch}
            size="large"
            allowClear
          />
          <Button type="primary" size="large" onClick={handleSearch} loading={loading}>
            搜索
          </Button>
        </Space>
        
        <Space size="small">
          {currentPath && (
            <Tag 
              closable 
              onClose={clearPath} 
              color="blue" 
              style={{ padding: '4px 10px', fontSize: '14px' }}
            >
              范围: {currentPath.length > 20 ? '...' + currentPath.slice(-20) : currentPath}
            </Tag>
          )}
          <Button icon={<FolderOpenOutlined />} onClick={handlePickFolder}>上传文件夹</Button>
          <Button 
            type="text" 
            icon={<SettingOutlined style={{ fontSize: '18px' }} />} 
            onClick={() => navigate('/settings')}
          />
        </Space>
      </Header>

      <Content style={{ padding: '24px' }}>
        <Table 
          columns={columns} 
          dataSource={files} 
          loading={loading}
          pagination={{ pageSize: 20 }}
          size="middle"
          onRow={(record) => ({
            onClick: () => console.log('Clicked row:', record),
            style: { cursor: 'pointer' }
          })}
        />
      </Content>
    </Layout>
  );
};

export default Home;
