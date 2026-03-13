import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Input, Button, Table, Space, Layout, Typography, message, Tag, Tooltip, Dropdown, Modal, Spin, Progress, Radio } from 'antd';
import { 
  SearchOutlined, 
  FolderOpenOutlined, 
  SettingOutlined, 
  FileOutlined,
  MoreOutlined,
  GlobalOutlined,
  EyeOutlined,
  DatabaseOutlined,
  ThunderboltOutlined
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
  FileSpreadsheet 
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
  score?: number;
  content_preview?: string;
}

const FileIcon: React.FC<{ record: FileItem }> = ({ record }) => {
  const [iconError, setIconError] = React.useState(false);
  
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

  if (record.type === 'folder') {
    return <Folder size={18} color="#ffca28" fill="#ffca28" />;
  }

  const ext = (record.extension || '').toLowerCase();
  
  if (['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.ico'].includes(ext)) {
    return <FileImage size={18} color="#52c41a" />;
  }
  
  if (['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv'].includes(ext)) {
    return <FileVideo size={18} color="#722ed1" />;
  }
  
  if (['.mp3', '.wav', '.flac', '.ogg', '.m4a'].includes(ext)) {
    return <FileAudio size={18} color="#fa8c16" />;
  }
  
  if (['.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx'].includes(ext)) {
    return <FileSpreadsheet size={18} color="#1890ff" />;
  }
  
  if (['.md', '.txt'].includes(ext)) {
    return <FileText size={18} color="#8c8c8c" />;
  }
  
  if (['.zip', '.rar', '.7z', '.tar', '.gz'].includes(ext)) {
    return <FileArchive size={18} color="#faad14" />;
  }
  
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
  const [searchMode, setSearchMode] = useState<'filename' | 'semantic'>('filename');

  // Indexing State
  const [indexing, setIndexing] = useState(false);
  const [indexProgress, setIndexProgress] = useState({ status: '', current: 0, total: 0, file: '', percent: 0, msg: '' });

  // Preview State
  const [previewVisible, setPreviewVisible] = useState(false);
  const [previewContent, setPreviewContent] = useState('');
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewTitle, setPreviewTitle] = useState('');

  // Chunk State
  const [chunkVisible, setChunkVisible] = useState(false);
  const [chunkContent, setChunkContent] = useState('');
  const [chunkTitle, setChunkTitle] = useState('');

  const handlePreview = async (record: FileItem) => {
    setPreviewTitle(record.name);
    setPreviewVisible(true);
    setPreviewLoading(true);
    setPreviewContent('');
    
    try {
      const response = await fetch(`http://localhost:8000/api/preview?path=${encodeURIComponent(record.path)}`);
      const data = await response.json();
      
      if (data.error) {
        setPreviewContent(`Error: ${data.error}`);
      } else {
        setPreviewContent(data.content || '無內容');
      }
    } catch {
      setPreviewContent('Failed to load preview');
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleViewChunk = (record: FileItem) => {
    setChunkTitle(`${record.name} - 匹配的分块内容`);
    setChunkContent(record.content_preview || '無分块内容');
    setChunkVisible(true);
  };

  const handlePickFolderAndIndex = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/pick-folder');
      const data = await response.json();
      
      if (!data.cancelled && data.path) {
        setCurrentPath(data.path);
        message.success(`當前範圍: ${data.path}`);
        setSearchQuery('');
        performSearch('', data.path);
        
        // 自动开始索引
        setIndexing(true);
        setIndexProgress({ status: 'init', current: 0, total: 0, file: '', percent: 0, msg: '正在初始化系統...' });
        
        try {
          const indexResponse = await fetch('http://localhost:8000/api/index_folder', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: data.path })
          });
          
          const reader = indexResponse.body?.getReader();
          const decoder = new TextDecoder();
          
          if (!reader) return;
          
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value);
            const lines = chunk.split('\n\n');
            
            for (const line of lines) {
              if (line.startsWith('data: ')) {
                try {
                  const eventData = JSON.parse(line.substring(6));
                  if (eventData.status === 'complete') {
                    message.success('索引完成!');
                    setTimeout(() => setIndexing(false), 1000);
                  } else if (eventData.status === 'fatal') {
                    message.error(`錯誤: ${eventData.msg}`);
                    setIndexing(false);
                  } else {
                    setIndexProgress(prev => ({ ...prev, ...eventData }));
                  }
                } catch (e) {
                  console.error('Parse error', e);
                }
              }
            }
          }
        } catch (err) {
          console.error(err);
          message.error('索引啟動失敗');
          setIndexing(false);
        }
      }
    } catch (error) {
      console.error('Pick folder failed:', error);
      message.error('無法打開文件夾選擇框');
    }
  };

  const performSearch = async (query: string, path: string | null) => {
    setLoading(true);
    setFiles([]);
    
    try {
      if (searchMode === 'semantic') {
        if (!query) {
          setLoading(false);
          return;
        }
        const response = await fetch(`http://localhost:8000/api/vector_search?q=${encodeURIComponent(query)}&k=50`);
        const data = await response.json();
        
        if (data.msg) {
          message.warning(data.msg);
        }
        
        const mappedFiles = (data.results || []).map((item: any, index: number) => ({
          key: index.toString(),
          name: item.file_path.split('\\').pop() || item.file_path.split('/').pop(),
          path: item.file_path,
          size: '-',
          size_bytes: 0,
          modified: '-',
          created: '-',
          extension: '.' + (item.file_path.split('.').pop() || ''),
          type: 'file',
          score: item.score,
          content_preview: item.content
        }));
        setFiles(mappedFiles);
        if (mappedFiles.length === 0) {
          message.info('未找到相關內容');
        }
        
      } else {
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
          throw new Error(data.detail || '搜索失敗');
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
      }
    } catch (error: any) {
      console.error('Search failed:', error);
      message.error(error.message || '搜索失敗，請確保後端服務已啟動');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenFile = async (path: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/open-file?path=${encodeURIComponent(path)}`);
      if (!response.ok) throw new Error('Failed to open file');
    } catch (error) {
      message.error('無法打開文件');
    }
  };

  const handleOpenFolder = async (path: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/open-folder?path=${encodeURIComponent(path)}`);
      if (!response.ok) throw new Error('Failed to open folder');
    } catch (error) {
      message.error('無法在資源管理器中打開');
    }
  };

  const handleSearch = () => {
    if (!searchQuery.trim() && !currentPath && searchMode === 'filename') {
      message.warning('請輸入搜索關鍵詞或選擇文件夾');
      return;
    }
    if (!searchQuery.trim() && searchMode === 'semantic') {
      message.warning('語義搜索需要輸入關鍵詞');
      return;
    }
    performSearch(searchQuery, currentPath);
  };


  const clearPath = () => {
    setCurrentPath(null);
    setFiles([]);
    message.info('已切換回全盤搜索模式');
  };

  const columns: ColumnsType<FileItem> = [
    {
      title: '名稱',
      dataIndex: 'name',
      key: 'name',
      ellipsis: true,
      width: '40%',
      render: (text, record) => (
        <Space orientation="vertical" size={0} style={{ width: '100%' }}>
          <Space onClick={() => handleOpenFile(record.path)} style={{ cursor: 'pointer' }}>
            <FileIcon record={record} />
            <Text strong>{text}</Text>
            {searchMode === 'semantic' && record.score && (
              <Tag color="green">相似度: {(1 / (1 + record.score)).toFixed(4)}</Tag>
            )}
          </Space>
          {searchMode === 'semantic' && record.content_preview && (
            <Text 
              type="secondary" 
              style={{ 
                fontSize: '12px', 
                marginLeft: 24,
                cursor: 'pointer',
                color: '#1890ff'
              }} 
              onClick={() => handleViewChunk(record)}
            >
              {record.content_preview.length > 200 ? record.content_preview.substring(0, 200) + '...' : record.content_preview}
            </Text>
          )}
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
        <Text type="secondary" style={{ fontSize: '12px' }}>{text}</Text>
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
      title: '修改時間',
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
                label: '打開',
                icon: <FileOutlined />,
                onClick: () => handleOpenFile(record.path)
              },
              {
                key: 'preview',
                label: '預覽',
                icon: <EyeOutlined />,
                onClick: () => handlePreview(record),
                disabled: record.type === 'folder'
              },
              {
                key: 'view-chunk',
                label: '查看分块',
                icon: <DatabaseOutlined />,
                onClick: () => handleViewChunk(record),
                disabled: record.type === 'folder' || searchMode !== 'semantic' || !record.content_preview
              },
              {
                key: 'explorer',
                label: '在資源管理器中打開',
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
            prefix={searchMode === 'filename' ? <SearchOutlined style={{ color: '#bfbfbf' }} /> : <ThunderboltOutlined style={{ color: '#52c41a' }} />}
            placeholder={
              searchMode === 'filename' 
                ? (currentPath ? `在 ${currentPath.split('\\').pop()} 中搜索...` : "搜索本地文件 (Everything)...")
                : "輸入語義關鍵詞進行智能搜索..."
            }
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onPressEnter={handleSearch}
            size="large"
            allowClear
            suffix={
              !currentPath && searchMode === 'filename' && <Tooltip title="正在使用全盤搜索"><GlobalOutlined style={{ color: '#1890ff' }} /></Tooltip>
            }
          />
          <Button type="primary" size="large" onClick={handleSearch} loading={loading}>
            搜索
          </Button>
          <Radio.Group 
            value={searchMode} 
            onChange={e => {
              setSearchMode(e.target.value);
              setSearchQuery('');
            }}
            buttonStyle="solid"
          >
            <Radio.Button value="filename">文件名</Radio.Button>
            <Radio.Button value="semantic">語義</Radio.Button>
          </Radio.Group>
        </Space>
        
        <Space size="small">
          {currentPath && (
            <Tag closable onClose={clearPath} color="blue" style={{ padding: '4px 10px', fontSize: '13px', borderRadius: '4px' }}>
              範圍: {currentPath.length > 30 ? '...' + currentPath.slice(-30) : currentPath}
            </Tag>
          )}
          <Tooltip title="選擇文件夾並自動建立索引">
            <Button icon={<FolderOpenOutlined />} onClick={handlePickFolderAndIndex} loading={indexing}>選擇文件夾</Button>
          </Tooltip>
          <Button type="text" icon={<SettingOutlined style={{ fontSize: '18px' }} />} onClick={() => navigate('/settings')} />
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
            showTotal: (total) => `共 ${total} 個項目`,
            size: 'small',
            style: { margin: '12px 16px' }
          }}
          size="middle"
          scroll={{ y: 'calc(100vh - 64px - 55px - 56px)' }}
          onRow={(record) => ({
            onDoubleClick: () => handleOpenFile(record.path),
          })}
          locale={{ emptyText: searchQuery || currentPath ? '沒有找到匹配項' : '請輸入關鍵詞開始搜索' }}
          style={{ flex: 1 }}
        />
      </Content>

      <Modal
        title="正在建立索引"
        open={indexing}
        footer={null}
        closable={false}
        maskClosable={false}
      >
        <Space orientation="vertical" style={{ width: '100%' }}>
          <Text>{indexProgress.msg}</Text>
          <Progress percent={indexProgress.percent} status={indexProgress.status === 'error' ? 'exception' : 'active'} />
          {indexProgress.file && <Text type="secondary" ellipsis>正在處理: {indexProgress.file}</Text>}
          <Text type="secondary">進度: {indexProgress.current} / {indexProgress.total}</Text>
        </Space>
      </Modal>

      <Modal
        title={`預覽: ${previewTitle || ''}`}
        open={previewVisible}
        onCancel={() => setPreviewVisible(false)}
        footer={null}
        width={800}
        styles={{ body: { maxHeight: '70vh', overflowY: 'auto' } }}
      >
        {previewLoading ? (
          <div style={{ textAlign: 'center', padding: '20px' }}>
            <Spin tip="加載中..." />
          </div>
        ) : (
          <pre style={{ 
            whiteSpace: 'pre-wrap', 
            wordWrap: 'break-word',
            fontFamily: 'Consolas, Monaco, "Courier New", monospace',
            fontSize: '14px',
            backgroundColor: '#f5f5f5',
            padding: '12px',
            borderRadius: '4px'
          }}>
            {previewContent}
          </pre>
        )}
      </Modal>

      <Modal
        title={chunkTitle || ''}
        open={chunkVisible}
        onCancel={() => setChunkVisible(false)}
        footer={null}
        width={800}
        styles={{ body: { maxHeight: '70vh', overflowY: 'auto' } }}
      >
        <pre style={{ 
          whiteSpace: 'pre-wrap', 
          wordWrap: 'break-word',
          fontFamily: 'Consolas, Monaco, "Courier New", monospace',
          fontSize: '14px',
          backgroundColor: '#f0f9ff',
          padding: '12px',
          borderRadius: '4px',
          border: '1px solid #e6f7ff'
        }}>
          {chunkContent}
        </pre>
      </Modal>
    </Layout>
  );
};

export default Home;
