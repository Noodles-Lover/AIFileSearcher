import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Input, Button, Table, Space, Layout, Typography, message, Tag, Tooltip, Dropdown, Spin, Progress, Radio } from 'antd';
import CustomModal from '../components/CustomModal';
import FileIcon, { type FileItem } from '../components/FileIcon';
import { API_ENDPOINTS, apiGet, apiPost } from '../utils/api';
import '../styles/progress.css';

interface PreviewResponse {
  error?: string;
  content?: string;
}

interface FolderResponse {
  path?: string;
  cancelled?: boolean;
  error?: string;
}

interface SetFolderResponse {
  path?: string;
  success?: boolean;
  message?: string;
  error?: string;
}
import { 
  SearchOutlined, 
  FolderOpenOutlined, 
  SettingOutlined, 
  FileOutlined,
  MoreOutlined,
  GlobalOutlined,
  EyeOutlined,
  DatabaseOutlined,
  ThunderboltOutlined,
  LoadingOutlined,
  DownOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';

const { Header, Content } = Layout;
const { Text } = Typography;

const Home: React.FC = () => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [files, setFiles] = useState<FileItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [currentPath, setCurrentPath] = useState<string | null>(null);
  const [searchMode, setSearchMode] = useState<'filename' | 'semantic'>('filename');
  const [showPathInput, setShowPathInput] = useState(false);
  const [inputPath, setInputPath] = useState('');

  // Indexing State
  const [indexing, setIndexing] = useState(false);
  const [indexProgress, setIndexProgress] = useState({ status: '', current: 0, total: 0, file: '', percent: 0, msg: '' });

  // 切换搜索模式
  const handleSearchModeChange = (mode: 'filename' | 'semantic') => {
    setSearchMode(mode);
  };

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
      const data = await apiGet<PreviewResponse>(`${API_ENDPOINTS.PREVIEW}?path=${encodeURIComponent(record.path)}`);
      
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

  const handlePickFolder = async () => {
    try {
      // 使用后端API选择文件夹
      const data = await apiGet<FolderResponse>(API_ENDPOINTS.PICK_FOLDER);
      
      if (data && !data.cancelled && data.path) {
        const folderPath = data.path;
        setCurrentPath(folderPath);
        
        // 清空之前的搜索结果
        setFiles([]);
        setSearchQuery('');
        
        message.success(`已選擇文件夾: ${folderPath}`);
        
        // 自动显示文件夹中的文件
        await performSearch('', folderPath);
      } else if (data && data.cancelled) {
        message.info('用戶取消了選擇');
      } else if (data.error) {
        message.error(data.error);
      } else {
        message.error('選擇文件夾失敗');
      }
    } catch (e) {
      console.error('無法打開文件夾選擇框:', e);
      message.error('無法打開文件夾選擇框');
    }
  };

  const handleSetFolder = async (path: string) => {
    if (!path.trim()) {
      message.error('请输入文件夹路径');
      return;
    }

    try {
      const data = await apiPost<SetFolderResponse>(API_ENDPOINTS.SET_FOLDER, { path });
      
      if (data.success) {
        setCurrentPath(data.path || path);
        message.success(data.message || '文件夹设置成功');
        setShowPathInput(false);
        setInputPath('');
        
        // 清空之前的搜索结果
        setFiles([]);
        setSearchQuery('');
        
        // 自动显示文件夹中的文件
        await performSearch('', data.path || path);
      } else {
        message.error(data.error || '设置文件夹失败');
      }
    } catch (error) {
      console.error('设置文件夹失败:', error);
      message.error('设置文件夹失败');
    }
  };

  const handleIndexFolder = async (path: string) => {
    if (!path) {
      message.warning('请先选择一个文件夹');
      return;
    }
    
    setIndexing(true);
    setIndexProgress({ status: '', current: 0, total: 0, file: '', percent: 0, msg: '正在启动索引...' });
    
    try {
      const indexResponse = await fetch('http://localhost:8000/api/index_folder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path })
      });
      
      if (!indexResponse.ok) {
        throw new Error(`索引请求失败: ${indexResponse.status} ${indexResponse.statusText}`);
      }
      
      const reader = indexResponse.body?.getReader();
      const decoder = new TextDecoder();
      
      if (!reader) {
        throw new Error('无法获取响应流');
      }
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n').filter(line => line.trim() !== '');
        
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
              } else if (eventData.status === 'start') {
                setIndexProgress(prev => ({ 
                  ...prev, 
                  status: eventData.status,
                  total: eventData.total || 0,
                  current: eventData.current || 0,
                  percent: eventData.percent || 0,
                  file: eventData.file || '',
                  msg: eventData.msg || '开始索引'
                }));
              } else if (eventData.status === 'progress') {
                setIndexProgress(prev => ({ 
                  ...prev, 
                  status: eventData.status,
                  current: eventData.current || prev.current,
                  total: eventData.total || prev.total,
                  percent: eventData.percent || prev.percent,
                  file: eventData.file || prev.file || '',
                  msg: eventData.msg || prev.msg
                }));
              } else if (eventData.status === 'init') {
                setIndexProgress(prev => ({ 
                  ...prev, 
                  status: eventData.status,
                  current: eventData.current || 0,
                  total: eventData.total || 0,
                  percent: eventData.percent || 0,
                  msg: eventData.msg || '初始化中...'
                }));
              } else if (eventData.status === 'scanning') {
                setIndexProgress(prev => ({ 
                  ...prev, 
                  status: eventData.status,
                  current: eventData.current || 0,
                  total: eventData.total || 0,
                  percent: eventData.percent || 0,
                  msg: eventData.msg || '扫描中...'
                }));
              }
            } catch (e) {
              console.error('解析错误', e, '原始行:', line);
            }
          }
        }
      }
    } catch (error) {
      console.error('索引请求错误:', error);
      message.error(`索引启动失败: ${error instanceof Error ? error.message : '未知错误'}`);
      setIndexing(false);
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
        const response = await fetch(`http://localhost:8000/api/vector_search?q=${encodeURIComponent(query)}&k=30`);
        const data = await response.json();
        
        if (data.msg) {
          message.warning(data.msg);
        }
        
        const mappedFiles = (data.results || []).map((item: {
          file_path: string;
          content: string;
          score: number;
        }, index: number) => ({
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
        
        const mappedFiles = data.results.map((item: {
          name: string;
          path: string;
          size: string;
          size_bytes: number;
          modified: string;
          type: string;
          created?: string;
          extension?: string;
        }, index: number) => ({
          key: index.toString(),
          name: item.name,
          path: item.path,
          size: item.size,
          size_bytes: item.size_bytes,
          modified: item.modified,
          created: item.created || '-',
          extension: item.extension || '',
          type: item.type
        }));
        
        setFiles(mappedFiles);
        if (mappedFiles.length === 0) {
          message.info('未找到匹配的文件');
        }
      }
    } catch (error: unknown) {
      console.error('Search failed:', error);
      message.error((error as Error).message || '搜索失敗，請確保後端服務已啟動');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenFile = async (path: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/open-file?path=${encodeURIComponent(path)}`);
      if (!response.ok) throw new Error('Failed to open file');
    } catch {
      message.error('無法打開文件');
    }
  };

  const handleOpenFolder = async (path: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/open-folder?path=${encodeURIComponent(path)}`);
      if (!response.ok) throw new Error('Failed to open folder');
    } catch {
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
            onChange={(e) => handleSearchModeChange(e.target.value)}
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
          <Button 
            icon={<ThunderboltOutlined />} 
            onClick={() => handleIndexFolder(currentPath || '')}
            loading={indexing}
          >
            建立索引
          </Button>
          <Dropdown 
            menu={{
              items: [
                {
                  key: 'pick',
                  label: '选择文件夹',
                  icon: <FolderOpenOutlined />,
                  onClick: handlePickFolder
                },
                {
                  key: 'input',
                  label: '直接输入路径',
                  icon: <FolderOpenOutlined />,
                  onClick: () => setShowPathInput(true)
                }
              ]
            }}
          >
            <Button icon={<FolderOpenOutlined />}>
              文件夹 <DownOutlined />
            </Button>
          </Dropdown>
          <Button type="text" icon={<SettingOutlined style={{ fontSize: '18px' }} />} onClick={() => navigate('/settings')} />
        </Space>
      </Header>

      <Content style={{ flex: 1, background: '#fff', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        <Table 
          columns={columns} 
          dataSource={files} 
          loading={loading}
          pagination={{
            defaultPageSize: 20, 
            showSizeChanger: true, 
            pageSizeOptions: ['10', '20', '50', '100'],
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

      {/* 索引进度 - 使用顶部抽屉，适合进度显示 */}
      <CustomModal
        title="正在建立索引"
        open={indexing}
        onClose={() => {}}
        placement="top"
        height={200}
      >
        <Space orientation="vertical" style={{ width: '100%' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Spin 
              indicator={
                <LoadingOutlined 
                  style={{ 
                    fontSize: '16px',
                    color: '#1890ff'
                  }} 
                />
              } 
            />
            <Text strong style={{ color: '#1890ff' }}>{indexProgress.msg}</Text>
          </div>
          <Progress 
            percent={indexProgress.percent} 
            status={indexProgress.status === 'error' ? 'exception' : 'active'}
            strokeColor={{
              '0%': '#108ee9',
              '50%': '#1890ff',
              '100%': '#52c41a',
            }}
            trailColor="#f0f0f0"
            strokeWidth={8}
            format={(percent) => (
              <span style={{ 
                fontWeight: 'bold',
                color: percent === 100 ? '#52c41a' : '#1890ff',
                fontSize: '14px'
              }}>
                {percent}%
              </span>
            )}
          />
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between',
            alignItems: 'center',
            fontSize: '12px',
            color: '#666',
            padding: '4px 0'
          }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              {indexProgress.percent === 100 ? (
                <>
                  <span style={{ color: '#52c41a' }}>✅</span>
                  <span style={{ color: '#52c41a', fontWeight: 'bold' }}>完成</span>
                </>
              ) : (
                <>
                  <span className="pulse-dot" style={{ 
                    display: 'inline-block',
                    width: '8px',
                    height: '8px',
                    borderRadius: '50%',
                    backgroundColor: '#1890ff'
                  }}></span>
                  <span>處理中...</span>
                </>
              )}
            </span>
            <span>進度: {indexProgress.current} / {indexProgress.total}</span>
          </div>
        </Space>
      </CustomModal>

      {/* 文件预览 - 使用居中弹窗，适合内容查看 */}
      <CustomModal
        title={`預覽: ${previewTitle || ''}`}
        open={previewVisible}
        onClose={() => setPreviewVisible(false)}
        width={800}
        placement="center"
        height={600}
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
      </CustomModal>

      {/* 分块查看 - 使用居中弹窗，适合内容查看 */}
      <CustomModal
        title={chunkTitle || ''}
        open={chunkVisible}
        onClose={() => setChunkVisible(false)}
        width={800}
        placement="center"
        height={600}
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
      </CustomModal>

      {/* 路径输入模态框 */}
      <CustomModal
        title="直接输入文件夹路径"
        open={showPathInput}
        onClose={() => setShowPathInput(false)}
        width={500}
        placement="center"
        height={200}
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <Text>请输入要索引的文件夹完整路径：</Text>
          <Input 
            placeholder="例如：D:\Documents\项目文件"
            value={inputPath}
            onChange={(e) => setInputPath(e.target.value)}
            onPressEnter={() => {
              handleSetFolder(inputPath);
              setShowPathInput(false);
              setInputPath('');
            }}
            style={{ fontSize: '14px' }}
          />
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '10px' }}>
            <Button 
              onClick={() => setShowPathInput(false)}
            >
              取消
            </Button>
            <Button 
              type="primary" 
              onClick={() => {
                handleSetFolder(inputPath);
                setShowPathInput(false);
                setInputPath('');
              }}
              disabled={!inputPath.trim()}
            >
              确认
            </Button>
          </div>
        </Space>
      </CustomModal>
    </Layout>
  );
};

export default Home;
