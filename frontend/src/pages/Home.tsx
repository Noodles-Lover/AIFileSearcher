import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Input, Button, Table, Space, Layout, Typography, message, Tag, Tooltip, Dropdown, Spin, Progress, DatePicker, Select } from 'antd';
import CustomModal from '../components/CustomModal';
import FileIcon, { type FileItem } from '../components/FileIcon';
import { API_ENDPOINTS, apiGet, apiPost } from '../utils/api';
import { processSemanticSearchResults, getRelativePath, convertSizeToBytes } from '../utils/fileUtils';
import { generateColumns } from '../utils/fileTableColumns';
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
  EyeOutlined,
  DatabaseOutlined,
  ThunderboltOutlined,
  LoadingOutlined,
  DownOutlined,
  FunnelPlotOutlined,
  ClearOutlined
} from '@ant-design/icons';

const { Header, Content } = Layout;
const { Text } = Typography;
const { RangePicker } = DatePicker;

const Home: React.FC = () => {
  const navigate = useNavigate();
  
  // Search State
  const [searchQuery, setSearchQuery] = useState('');
  const [files, setFiles] = useState<FileItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [currentPath, setCurrentPath] = useState<string | null>(null);
  
  // Path Input State
  const [showPathInput, setShowPathInput] = useState(false);
  const [inputPath, setInputPath] = useState('');

  // Filter State
  const [showFilterModal, setShowFilterModal] = useState(false);
  const [filterExtensions, setFilterExtensions] = useState('');
  const [filterMinSize, setFilterMinSize] = useState<number | null>(null);
  const [filterMaxSize, setFilterMaxSize] = useState<number | null>(null);
  const [filterMinSizeUnit, setFilterMinSizeUnit] = useState<string>('B');
  const [filterMaxSizeUnit, setFilterMaxSizeUnit] = useState<string>('B');
  const [filterDateRange, setFilterDateRange] = useState<[Date | null, Date | null]>([null, null]);

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
  const [chunkData, setChunkData] = useState<any[]>([]);

  // 处理文件预览
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

  // 处理查看分块
  const handleViewChunk = async (record: FileItem) => {
    if (!searchQuery.trim()) {
      message.warning('只能在搜索后查看分块');
      return;
    }
    
    try {
      setChunkTitle(`${record.name} - 匹配的分块内容`);
      setChunkContent('正在加载分块内容...');
      setChunkVisible(true);
      
      // 检查是否有存储的分块
      if (record.all_chunks && record.all_chunks.length > 0) {
        // 使用存储的分块
        setChunkData(record.all_chunks);
      } else {
        // 回退到API请求
        const response = await fetch(`http://localhost:8000/api/file_chunks?q=${encodeURIComponent(searchQuery)}&file_path=${encodeURIComponent(record.path)}`);
        const data = await response.json();
        
        if (!response.ok) {
          throw new Error(data.detail || '获取分块失败');
        }
        
        const chunks = data.chunks || [];
        
        if (chunks.length === 0) {
          setChunkContent('未找到匹配的分块内容');
          return;
        }
        
        // 准备分块数据用于UI渲染
        setChunkData(chunks);
      }
      
    } catch (error) {
      console.error('查看分块失败:', error);
      setChunkContent('加载分块内容失败');
      message.error('查看分块失败');
    }
  };

  // 处理选择文件夹
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

  // 处理设置文件夹
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

  // 处理索引文件夹
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

  // 执行搜索
  const performSearch = async (query: string, path: string | null) => {
    setLoading(true);
    setFiles([]);
    
    try {
      if (!query) {
        // 如果没有查询词但有路径，则列出文件夹内容
        if (path) {
          const params = new URLSearchParams();
          params.append('parent_path', path);
          const url = `http://localhost:8000/api/list?${params.toString()}`;
          
          const response = await fetch(url);
          const data = await response.json();
          
          if (!response.ok) {
            const errorMessage = data.detail || data.message || '获取文件列表失败';
            console.error('List API Error:', { status: response.status, data });
            throw new Error(errorMessage);
          }
          
          const mappedFiles = data.results.map((item: any) => ({
            name: item.name,
            path: item.path,
            type: item.type,
            size: item.size,
            modified: item.modified,
            size_bytes: item.size_bytes,
            relativePath: getRelativePath(item.path, path)
          }));
          setFiles(mappedFiles);
          if (mappedFiles.length === 0) {
            message.info('文件夹为空');
          }
        } else {
          message.warning('请先选择文件夹或输入搜索关键词');
          setLoading(false);
          return;
        }
      } else {
        // 执行语义搜索
        const params = new URLSearchParams();
        params.append('q', query);
        params.append('k', '30');
        params.append('decay_rate', '-1');  // 使用设置中的值
        
        if (filterExtensions) {
          // 将空格分隔的扩展名转换为逗号分隔
          const extensions = filterExtensions.split(/\s+/).filter(ext => ext.trim()).join(',');
          params.append('file_extensions', extensions);
        }
        const minSizeBytes = convertSizeToBytes(filterMinSize, filterMinSizeUnit);
        const maxSizeBytes = convertSizeToBytes(filterMaxSize, filterMaxSizeUnit);
        if (minSizeBytes) params.append('min_size', minSizeBytes.toString());
        if (maxSizeBytes) params.append('max_size', maxSizeBytes.toString());
        if (filterDateRange[0] && filterDateRange[0] instanceof Date) params.append('min_modified', Math.floor(filterDateRange[0].getTime() / 1000).toString());
        if (filterDateRange[1] && filterDateRange[1] instanceof Date) params.append('max_modified', Math.floor(filterDateRange[1].getTime() / 1000).toString());
        
        const url = `http://localhost:8000/api/vector_search?${params.toString()}`;
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.msg) {
          message.warning(data.msg);
        }
        
        const mappedFiles = processSemanticSearchResults(data.results, path);
        setFiles(mappedFiles);
        if (mappedFiles.length === 0) {
          message.info('未找到相關內容');
        }
      }
    } catch (error: unknown) {
      console.error('Search failed:', error);
      message.error((error as Error).message || '搜索失敗，請確保後端服務已啟動');
    } finally {
      setLoading(false);
    }
  };

  // 处理打开文件
  const handleOpenFile = async (path: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/open-file?path=${encodeURIComponent(path)}`);
      if (!response.ok) throw new Error('Failed to open file');
    } catch {
      message.error('無法打開文件');
    }
  };

  // 处理打开文件夹
  const handleOpenFolder = async (path: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/open-folder?path=${encodeURIComponent(path)}`);
      if (!response.ok) throw new Error('Failed to open folder');
    } catch {
      message.error('無法在資源管理器中打開');
    }
  };

  // 处理搜索
  const handleSearch = () => {
    if (!searchQuery.trim() && !currentPath) {
      message.warning('请先选择文件夹或输入搜索关键词');
      return;
    }
    performSearch(searchQuery, currentPath);
  };

  // 清除路径
  const clearPath = () => {
    setCurrentPath(null);
    setFiles([]);
    message.info('已切換回全盤搜索模式');
  };

  // 生成表格列定义
  const columns = generateColumns({
    onOpenFile: handleOpenFile,
    onPreview: handlePreview,
    onViewChunk: handleViewChunk,
    onOpenFolder: handleOpenFolder
  });

  return (
    <Layout style={{ height: '100vh', background: '#fff', overflow: 'hidden' }}>
      {/* 头部区域 */}
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
            prefix={<ThunderboltOutlined style={{ color: '#52c41a' }} />}
            placeholder={
              currentPath 
                ? `在 ${currentPath.split('\\').pop()} 中搜索...`
                : "输入语义关键词进行智能搜索..."
            }
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onPressEnter={handleSearch}
            size="large"
            allowClear
          />
          <Button type="primary" size="large" onClick={handleSearch} loading={loading}>
            搜索
          </Button>
          <Button 
            icon={<FunnelPlotOutlined />} 
            onClick={() => setShowFilterModal(true)}
            type="default"
            size="large"
          />
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
            trigger={['click']}
          >
            <Button icon={<FolderOpenOutlined />}>
              文件夹 <DownOutlined />
            </Button>
          </Dropdown>
          <Button 
            icon={<ThunderboltOutlined />} 
            onClick={() => handleIndexFolder(currentPath || '')}
            loading={indexing}
          >
            建立索引
          </Button>
          <Button type="text" icon={<SettingOutlined style={{ fontSize: '18px' }} />} onClick={() => navigate('/settings')} />
        </Space>
      </Header>

      {/* 内容区域 */}
      <Content style={{ flex: 1, background: '#fff', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        {currentPath && (
          <div style={{ 
            padding: '12px 24px', 
            borderBottom: '1px solid #f0f0f0',
            background: '#fafafa',
            flexShrink: 0
          }}>
            <Text strong style={{ fontSize: '14px', color: '#1890ff' }}>
              📁 {currentPath}
            </Text>
          </div>
        )}
        <Table 
          columns={columns} 
          dataSource={files} 
          loading={loading}
          pagination={{
            defaultPageSize: 20, 
            showSizeChanger: true, 
            pageSizeOptions: ['10', '20', '50', '100'],
            showTotal: (total) => `共 ${total} 項`
          }}
          style={{ flex: 1, overflow: 'auto' }}
        />
      </Content>

      {/* 索引进度 - 使用顶部抽屉，适合进度显示 */}
      <CustomModal
        title="正在建立索引"
        open={indexing}
        onClose={() => {}}
        placement="top"
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

      {/* 预览模态框 */}
      <CustomModal
        title={previewTitle}
        open={previewVisible}
        onClose={() => setPreviewVisible(false)}
        width={800}
        placement="center"
        height={600}
      >
        {previewLoading ? (
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
            <Spin size="large" />
          </div>
        ) : (
          <pre style={{ 
            whiteSpace: 'pre-wrap', 
            wordBreak: 'break-word',
            margin: 0,
            padding: '16px',
            background: '#f5f5f5',
            borderRadius: '4px',
            maxHeight: '500px',
            overflow: 'auto'
          }}>
            {previewContent}
          </pre>
        )}
      </CustomModal>

      {/* 分块查看模态框 */}
      <CustomModal
        title={chunkTitle}
        open={chunkVisible}
        onClose={() => setChunkVisible(false)}
        width={800}
        placement="center"
        height={600}
      >
        <div>
          {chunkData.length > 0 ? (
            chunkData.map((chunk, index) => (
              <div key={index} style={{ 
                marginBottom: '16px',
                padding: '12px',
                background: '#ffffecff', 
                borderRadius: '6px',
                border: '4px groove #9a9a9aff'
              }}>
                <div style={{ marginBottom: '8px' }}>
                  <Tag color="blue">分块 {chunk.chunk_index !== undefined ? chunk.chunk_index + 1 : index + 1}</Tag>
                  <Tag color="green">相似度: {(1 / (1 + chunk.score)).toFixed(4)}</Tag>
                </div>
                <Text style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                  {chunk.chunk_text || chunk.content}
                </Text>
              </div>
            ))
          ) : (
            <Text>{chunkContent}</Text>
          )}
        </div>
      </CustomModal>

      {/* 路径输入模态框 */}
      <CustomModal
        title="输入文件夹路径"
        open={showPathInput}
        onClose={() => setShowPathInput(false)}
        width={500}
        placement="center"
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

      {/* 过滤模态框 */}
      <CustomModal
        title="过滤条件"
        open={showFilterModal}
        onClose={() => setShowFilterModal(false)}
        width={600}
        placement="center"
      >
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          <div>
            <Text strong>文件扩展名</Text>
            <Input 
              placeholder="例如：pdf docx txt（空格分隔）"
              value={filterExtensions}
              onChange={(e) => setFilterExtensions(e.target.value)}
              style={{ marginTop: '8px' }}
            />
          </div>
          
          <div>
            <Text strong>文件大小</Text>
            <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
              <Input 
                type="number"
                placeholder="最小大小"
                value={filterMinSize || ''}
                onChange={(e) => setFilterMinSize(e.target.value ? parseFloat(e.target.value) : null)}
                style={{ flex: 1 }}
              />
              <Select
                value={filterMinSizeUnit}
                onChange={setFilterMinSizeUnit}
                style={{ width: 80 }}
                options={[
                  { value: 'B', label: 'B' },
                  { value: 'KB', label: 'KB' },
                  { value: 'MB', label: 'MB' },
                  { value: 'GB', label: 'GB' }
                ]}
              />
              <Input 
                type="number"
                placeholder="最大大小"
                value={filterMaxSize || ''}
                onChange={(e) => setFilterMaxSize(e.target.value ? parseFloat(e.target.value) : null)}
                style={{ flex: 1 }}
              />
              <Select
                value={filterMaxSizeUnit}
                onChange={setFilterMaxSizeUnit}
                style={{ width: 80 }}
                options={[
                  { value: 'B', label: 'B' },
                  { value: 'KB', label: 'KB' },
                  { value: 'MB', label: 'MB' },
                  { value: 'GB', label: 'GB' }
                ]}
              />
            </div>
          </div>
          
          <div>
            <Text strong>修改时间</Text>
            <div style={{ marginTop: '8px' }}>
              <RangePicker 
                value={filterDateRange}
                onChange={(dates) => setFilterDateRange(dates)}
                style={{ width: '100%' }}
              />
            </div>
          </div>
          
          <div style={{ display: 'flex', justifyContent: 'center', marginTop: '16px' }}>
            <Button 
              icon={<ClearOutlined />}
              onClick={() => {
                setFilterExtensions('');
                setFilterMinSize(null);
                setFilterMaxSize(null);
                setFilterMinSizeUnit('B');
                setFilterMaxSizeUnit('B');
                setFilterDateRange([null, null]);
              }}
            >
              清除过滤
            </Button>
          </div>
        </Space>
      </CustomModal>
    </Layout>
  );
};

export default Home;