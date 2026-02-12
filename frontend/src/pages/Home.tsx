import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Input, Button, Table, Space, Layout, Typography, message, Tag, Tooltip, Dropdown } from 'antd';
import { 
  SearchOutlined, 
  FolderOpenOutlined, 
  SettingOutlined, 
  FileOutlined,
  FolderFilled,
  MoreOutlined,
  GlobalOutlined
} from '@ant-design/icons';
import { 
  FileIcon as LucideFile, 
  Folder, 
  FileImage, 
  FileVideo, 
  FileAudio, 
  FileText, 
  FileArchive, 
  FileCode, 
  FileSpreadsheet, 
  FileBox,
  FileSearch
} from 'lucide-react';
import type { ColumnsType } from 'antd/es/table';

const { Header, Content } = Layout;
const { Text } = Typography;

interface FileItem {
  key: string;
  name: string;
  path: string;
  size: string;
  size_bytes: number;
  modified: string;
  created: string;
  extension: string;
  type: 'file' | 'folder';
}

const FileIcon: React.FC<{ record: FileItem }> = ({ record }) => {
  const [iconError, setIconError] = React.useState(false);
  
  // 生成圖標請求 URL
  const iconUrl = `http://localhost:8000/api/icon?path=${encodeURIComponent(record.path)}`;

  if (!iconError) {
    return (
      <img 
        src={iconUrl} 
        alt="" 
        style={{ width: 18, height: 18, objectFit: 'contain' }}
        onError={() => setIconError(true)}
      />
    );
  }

  // 如果系統圖標加載失敗，退回到 Lucide 圖標
  if (record.type === 'folder') {
    return <Folder size={18} color="#ffca28" fill="#ffca28" />;
  }

  const ext = (record.extension || '').toLowerCase();
  
  // 图片
  if (['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.ico'].includes(ext)) {
    return <FileImage size={18} color="#52c41a" />;
  }
  
  // 视频
  if (['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv'].includes(ext)) {
    return <FileVideo size={18} color="#722ed1" />;
  }
  
  // 音频
  if (['.mp3', '.wav', '.flac', '.ogg', '.m4a'].includes(ext)) {
    return <FileAudio size={18} color="#fa8c16" />;
  }
  
  // 文档
  if (['.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx'].includes(ext)) {
    return <FileSpreadsheet size={18} color="#1890ff" />;
  }
  
  if (['.md', '.txt'].includes(ext)) {
    return <FileText size={18} color="#8c8c8c" />;
  }
  
  // 压缩包
  if (['.zip', '.rar', '.7z', '.tar', '.gz'].includes(ext)) {
    return <FileArchive size={18} color="#faad14" />;
  }
  
  // 代码
  if (['.js', '.ts', '.tsx', '.jsx', '.py', '.java', '.cpp', '.h', '.html', '.css', '.json', '.sh', '.bat', '.ps1'].includes(ext)) {
    return <FileCode size={18} color="#1890ff" />;
  }

  return <LucideFile size={18} color="#8c8c8c" />;
};

const Home: React.FC = () => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [files, setFiles] = useState<FileItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [currentPath, setCurrentPath] = useState<string | null>(null);

  const performSearch = async (query: string, path: string | null) => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (query) params.append('q', query);
      if (path) params.append('parent_path', path);
      
      let url = `http://localhost:8000/api/search?${params.toString()}`;
      
      if (!query && path) {
         url = `http://localhost:8000/api/list?path=${encodeURIComponent(path)}`;
      } else if (!query && !path) {
         setLoading(false);
         return;
      }

      const response = await fetch(url);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || '搜索失败');
      }
      
      const mappedFiles = data.results.map((item: any, index: number) => ({
        key: index.toString(),
        name: item.name,
        path: item.path,
        size: item.size,
        size_bytes: item.size_bytes,
        modified: item.modified,
        created: item.created,
        extension: item.extension,
        type: item.type
      }));
      
      setFiles(mappedFiles);
      if (mappedFiles.length === 0) {
        message.info('未找到匹配的文件');
      }
    } catch (error: any) {
      console.error('Search failed:', error);
      message.error(error.message || '搜索失败，请确保后端服务已启动');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenFile = async (path: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/open-file?path=${encodeURIComponent(path)}`);
      if (!response.ok) throw new Error('Failed to open file');
    } catch (error) {
      message.error('无法打开文件');
    }
  };

  const handleOpenFolder = async (path: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/open-folder?path=${encodeURIComponent(path)}`);
      if (!response.ok) throw new Error('Failed to open folder');
    } catch (error) {
      message.error('无法在资源管理器中打开');
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
        setSearchQuery('');
        performSearch('', data.path);
      }
    } catch (error) {
      console.error('Pick folder failed:', error);
      message.error('无法打开文件夹选择框');
    }
  };

  const clearPath = () => {
    setCurrentPath(null);
    setFiles([]);
    message.info('已切换回全盘搜索模式');
  };

  const copyToClipboard = (text: string) => {
    // 接口占位，目前不执行任何操作
    console.log('Copy path requested for:', text);
  };

  const columns: ColumnsType<FileItem> = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      ellipsis: true,
      width: '40%',
      render: (text, record) => (
        <Space onClick={() => handleOpenFile(record.path)} style={{ cursor: 'pointer' }}>
          <FileIcon record={record} />
          <Text strong>{text}</Text>
        </Space>
      ),
      sorter: (a, b) => a.name.localeCompare(b.name),
    },
    {
      title: '位置',
      dataIndex: 'path',
      key: 'path',
      ellipsis: true,
      render: (text) => (
        <Text 
          type="secondary" 
          style={{ fontSize: '12px' }}
        >
          {text}
        </Text>
      ),
    },
    {
      title: '大小',
      dataIndex: 'size',
      key: 'size',
      width: 120,
      align: 'right',
      render: (text, record) => record.type === 'folder' ? '-' : (text === '0.00 B' ? '-' : text),
      sorter: (a, b) => a.size_bytes - b.size_bytes,
    },
    {
      title: '修改时间',
      dataIndex: 'modified',
      key: 'modified',
      width: 180,
      render: (text) => <Text type="secondary" style={{ fontSize: '12px' }}>{text}</Text>,
      sorter: (a, b) => a.modified.localeCompare(b.modified),
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      align: 'center',
      render: (_, record) => (
        <Dropdown
          menu={{
            items: [
              {
                key: 'open',
                label: '打开',
                icon: <FileOutlined />,
                onClick: () => handleOpenFile(record.path)
              },
              {
                key: 'explorer',
                label: '在资源管理器中打开',
                icon: <FolderOpenOutlined />,
                onClick: () => handleOpenFolder(record.path)
              }
            ]
          }}
          trigger={['click']}
        >
          <Button type="text" icon={<MoreOutlined />} onClick={(e) => e.stopPropagation()} />
        </Dropdown>
      ),
    },
  ];

  return (
    <Layout style={{ height: '100vh', background: '#fff', overflow: 'hidden' }}>
      <Header style={{ 
        background: '#fff', 
        padding: '0 24px', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'space-between',
        borderBottom: '1px solid #f0f0f0',
        height: '64px',
        flexShrink: 0,
        zIndex: 1,
        width: '100%'
      }}>
        <Space size="middle" style={{ flex: 1, maxWidth: '800px' }}>
          <Input 
            prefix={<SearchOutlined style={{ color: '#bfbfbf' }} />}
            placeholder={currentPath ? `在 ${currentPath.split('\\').pop()} 中搜索...` : "搜索本地文件 (Everything)..."}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onPressEnter={handleSearch}
            size="large"
            allowClear
            suffix={
              !currentPath && <Tooltip title="正在使用全盘搜索"><GlobalOutlined style={{ color: '#1890ff' }} /></Tooltip>
            }
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
              style={{ padding: '4px 10px', fontSize: '13px', borderRadius: '4px' }}
            >
              范围: {currentPath.length > 30 ? '...' + currentPath.slice(-30) : currentPath}
            </Tag>
          )}
          <Tooltip title="指定文件夹范围">
            <Button icon={<FolderOpenOutlined />} onClick={handlePickFolder}>限制范围</Button>
          </Tooltip>
          <Button 
            type="text" 
            icon={<SettingOutlined style={{ fontSize: '18px' }} />} 
            onClick={() => navigate('/settings')}
          />
        </Space>
      </Header>

      <Content style={{ flex: 1, background: '#fff', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        <Table 
          columns={columns} 
          dataSource={files} 
          loading={loading}
          pagination={{
            defaultPageSize: 50, 
            showSizeChanger: true, 
            pageSizeOptions: ['20', '50', '100', '200'],
            showTotal: (total) => `共 ${total} 个项目`,
            size: 'small',
            style: { margin: '12px 16px' }
          }}
          size="middle"
          scroll={{ y: 'calc(100vh - 64px - 55px - 56px)' }} // 64(header) + 55(table head) + 56(pagination)
          onRow={(record) => ({
            onDoubleClick: () => handleOpenFile(record.path),
          })}
          locale={{
            emptyText: searchQuery || currentPath ? '没有找到匹配项' : '请输入关键词开始搜索'
          }}
          style={{ flex: 1 }}
        />
      </Content>
    </Layout>
  );
};

export default Home;
