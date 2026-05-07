import React from 'react';
import type { CSSProperties } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Button,
  DatePicker,
  Dropdown,
  Input,
  Layout,
  Progress,
  Select,
  Space,
  Spin,
  Table,
  Tag,
  Typography
} from 'antd';
import {
  ClearOutlined,
  DownOutlined,
  FolderOpenOutlined,
  FunnelPlotOutlined,
  LoadingOutlined,
  SettingOutlined,
  ThunderboltOutlined
} from '@ant-design/icons';
import CustomModal from '../components/CustomModal';
import { generateColumns } from '../utils/home/fileTableColumns';
import { useIndexingFeature } from '../utils/home/useIndexingFeature';
import { usePreviewFeature } from '../utils/home/usePreviewFeature';
import { useSearchFeature } from '../utils/home/useSearchFeature';
import '../styles/progress.css';

const { Header, Content } = Layout;
const { Text } = Typography;
const { RangePicker } = DatePicker;

const styles: Record<string, CSSProperties> = {
  layout: { height: '100vh', overflow: 'hidden', background: '#fff' },
  header: {
    zIndex: 1,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    width: '100%',
    height: '64px',
    padding: '0 24px',
    background: '#fff',
    borderBottom: '1px solid #f0f0f0',
    flexShrink: 0,
  },
  headerControls: { flex: 1, maxWidth: '800px' },
  content: { display: 'flex', flex: 1, flexDirection: 'column', overflow: 'hidden', background: '#fff', minHeight: 0 },
  currentPathBar: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '12px 24px',
    background: '#fafafa',
    borderBottom: '1px solid #f0f0f0',
    flexShrink: 0,
  },
  currentPathText: { fontSize: '14px', color: '#1890ff' },
  folderBarIcon: { color: '#1890ff', fontSize: '16px' },
  tableWrapper: { flex: 1, minHeight: 0, overflow: 'hidden' },
  fullWidth: { width: '100%' },
  progressStatus: { display: 'flex', alignItems: 'center', gap: '8px' },
  progressFooter: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '4px 0',
    fontSize: '12px',
    color: '#666',
  },
  progressState: { display: 'flex', alignItems: 'center', gap: '4px' },
  progressComplete: { color: '#52c41a', fontWeight: 700 },
  progressDot: {
    display: 'inline-block',
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    backgroundColor: '#1890ff',
  },
  previewLoading: { display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' },
  previewContent: {
    margin: 0,
    padding: '16px',
    overflow: 'auto',
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-word',
    background: '#f5f5f5',
    borderRadius: '4px',
    maxHeight: '500px',
  },
  chunkItem: {
    marginBottom: '16px',
    padding: '12px',
    background: '#ffffec',
    border: '4px groove #9a9a9a',
    borderRadius: '6px',
  },
  chunkTags: { marginBottom: '8px' },
  chunkText: { whiteSpace: 'pre-wrap', wordBreak: 'break-word' },
  previewInfo: {
    marginBottom: '16px',
    padding: '8px 12px',
    background: '#e6f7ff',
    borderRadius: '4px',
    fontSize: '13px',
    color: '#1890ff',
  },
  previewChunkItem: {
    marginBottom: '16px',
    padding: '12px',
    background: '#ffffec',
    border: '1px solid #d9d9d9',
    borderRadius: '6px',
    boxShadow: '0 1px 2px rgba(0, 0, 0, 0.1)',
  },
  input: { fontSize: '14px' },
  inputActions: { display: 'flex', justifyContent: 'space-between', marginTop: '10px' },
  filterInput: { marginTop: '8px' },
  filterRow: { display: 'flex', gap: '8px', marginTop: '8px' },
  filterGrow: { flex: 1 },
  filterUnit: { width: 80 },
  filterActions: { display: 'flex', justifyContent: 'center', marginTop: '16px' },
};

const Home: React.FC = () => {
  const navigate = useNavigate();
  const search = useSearchFeature();
  const indexing = useIndexingFeature();
  const preview = usePreviewFeature(search.searchQuery);

  const columns = generateColumns({
    onOpenFile: search.handleOpenFile,
    onPreview: preview.handlePreview,
    onViewChunk: preview.handleViewChunk,
    onOpenFolder: search.handleOpenFolder
  });

  const folderMenuItems = [
    { key: 'pick', label: '选择文件夹', icon: <FolderOpenOutlined />, onClick: search.handlePickFolder },
    { key: 'input', label: '手动输入路径', icon: <FolderOpenOutlined />, onClick: () => search.setShowPathInput(true) }
  ];

  return (
    <Layout style={styles.layout}>
      <Header style={styles.header}>
        <Space size="middle" style={styles.headerControls}>
          <Input
            prefix={<ThunderboltOutlined style={{ color: '#52c41a' }} />}
            placeholder={search.currentPath ? `在 ${search.currentPath.split('\\').pop()} 中搜索...` : '输入语义关键词开始搜索...'}
            value={search.searchQuery}
            onChange={(e) => search.setSearchQuery(e.target.value)}
            onPressEnter={search.handleSearch}
            size="large"
            allowClear
          />
          <Button type="primary" size="large" onClick={search.handleSearch} loading={search.loading}>
            搜索
          </Button>
          <Button
            icon={<FunnelPlotOutlined />}
            onClick={() => search.setShowFilterModal(true)}
            type="default"
            size="large"
          />
          <Dropdown menu={{ items: folderMenuItems }} trigger={['click']}>
            <Button icon={<FolderOpenOutlined />}>
              文件夹 <DownOutlined />
            </Button>
          </Dropdown>
          <Button
            icon={<ThunderboltOutlined />}
            onClick={() => indexing.handleIndexFolder(search.currentPath || '')}
            loading={indexing.indexing}
          >
            建立索引
          </Button>
          <Button
            type="text"
            icon={<SettingOutlined style={{ fontSize: '18px' }} />}
            onClick={() => navigate('/settings')}
          />
        </Space>
      </Header>

      <Content style={styles.content}>
        {search.currentPath && (
          <div style={styles.currentPathBar}>
            <FolderOpenOutlined style={styles.folderBarIcon} />
            <Text strong style={styles.currentPathText}>
              当前文件夹: {search.currentPath}
            </Text>
          </div>
        )}

        <div style={styles.tableWrapper}>
          <Table
            className="home-results-table"
            columns={columns}
            dataSource={search.files}
            loading={search.loading}
            scroll={{ y: search.currentPath ? 'calc(100vh - 258px)' : 'calc(100vh - 210px)' }}
            pagination={{
              defaultPageSize: 20,
              showSizeChanger: true,
              pageSizeOptions: ['10', '20', '50', '100'],
              showTotal: (total) => `共 ${total} 条`,
            }}
          />
        </div>
      </Content>

      <CustomModal title="正在建立索引" open={indexing.indexing} onClose={() => {}} placement="top">
        <Space direction="vertical" style={styles.fullWidth}>
          <div style={styles.progressStatus}>
            <Spin indicator={<LoadingOutlined style={{ fontSize: '16px', color: '#1890ff' }} />} />
            <Text strong style={{ color: '#1890ff' }}>{indexing.indexProgress.msg}</Text>
          </div>
          <Progress
            percent={indexing.indexProgress.percent}
            status={indexing.indexProgress.status === 'error' ? 'exception' : 'active'}
            strokeColor={{ '0%': '#108ee9', '50%': '#1890ff', '100%': '#52c41a' }}
            trailColor="#f0f0f0"
            strokeWidth={8}
            format={(percent) => (
              <span style={{ fontWeight: 700, color: percent === 100 ? '#52c41a' : '#1890ff' }}>
                {percent}%
              </span>
            )}
          />
          <div style={styles.progressFooter}>
            <span style={styles.progressState}>
              {indexing.indexProgress.percent === 100 ? (
                <span style={styles.progressComplete}>完成</span>
              ) : (
                <>
                  <span className="pulse-dot" style={styles.progressDot} />
                  <span>处理中...</span>
                </>
              )}
            </span>
            <span>进度: {indexing.indexProgress.current} / {indexing.indexProgress.total}</span>
          </div>
        </Space>
      </CustomModal>

      <CustomModal
        title={preview.previewTitle}
        open={preview.previewVisible}
        onClose={() => preview.setPreviewVisible(false)}
        width={800}
        placement="center"
        height={600}
      >
        {preview.previewLoading ? (
          <div style={styles.previewLoading}>
            <Spin size="large" />
          </div>
        ) : preview.previewChunks && preview.previewChunks.length > 0 ? (
          <div>
            <div style={styles.previewInfo}>
              <span>分块策略: {preview.previewStrategy}</span>
              <span style={{ marginLeft: '16px' }}>总分块数: {preview.previewTotalChunks}</span>
            </div>
            {preview.previewChunks.map((chunk, index) => (
              <div key={index} style={styles.previewChunkItem}>
                <div style={styles.chunkTags}>
                  <Tag color="blue">分块 {index + 1}</Tag>
                </div>
                <Text style={styles.chunkText}>{chunk}</Text>
              </div>
            ))}
            {preview.previewHasMore && (
              <div style={{ textAlign: 'center', color: '#999', marginTop: '16px' }}>
                ... (更多内容已省略，共 {preview.previewTotalChunks} 个分块)
              </div>
            )}
          </div>
        ) : (
          <pre style={styles.previewContent}>{preview.previewContent || '无预览内容'}</pre>
        )}
      </CustomModal>

      <CustomModal
        title={preview.chunkTitle}
        open={preview.chunkVisible}
        onClose={() => preview.setChunkVisible(false)}
        width={800}
        placement="center"
        height={600}
      >
        <div>
          {preview.chunkData.length > 0 ? (
            preview.chunkData.map((chunk, index) => (
              <div key={index} style={styles.chunkItem}>
                <div style={styles.chunkTags}>
                  <Tag color="blue">分块 {chunk.chunk_index !== undefined ? chunk.chunk_index + 1 : index + 1}</Tag>
                  <Tag color="green">相似度: {(1 / (1 + chunk.score)).toFixed(4)}</Tag>
                </div>
                <Text style={styles.chunkText}>{chunk.chunk_text || chunk.content}</Text>
              </div>
            ))
          ) : (
            <Text>{preview.chunkContent}</Text>
          )}
        </div>
      </CustomModal>

      <CustomModal
        title="输入文件夹路径"
        open={search.showPathInput}
        onClose={() => search.setShowPathInput(false)}
        width={500}
        placement="center"
      >
        <Space direction="vertical" style={styles.fullWidth}>
          <Text>请输入要搜索或索引的文件夹路径</Text>
          <Input
            placeholder="例如: C:\\Documents\\ProjectFiles"
            value={search.inputPath}
            onChange={(e) => search.setInputPath(e.target.value)}
            onPressEnter={() => search.handleSetFolder(search.inputPath)}
            style={styles.input}
          />
          <div style={styles.inputActions}>
            <Button onClick={() => search.setShowPathInput(false)}>取消</Button>
            <Button type="primary" onClick={() => search.handleSetFolder(search.inputPath)} disabled={!search.inputPath.trim()}>
              确认
            </Button>
          </div>
        </Space>
      </CustomModal>

      <CustomModal
        title="筛选条件"
        open={search.showFilterModal}
        onClose={() => search.setShowFilterModal(false)}
        width={600}
        placement="center"
      >
        <Space direction="vertical" style={styles.fullWidth} size="middle">
          <div>
            <Text strong>文件扩展名</Text>
            <Input
              placeholder="例如: pdf docx txt"
              value={search.filterExtensions}
              onChange={(e) => search.setFilterExtensions(e.target.value)}
              style={styles.filterInput}
            />
          </div>

          <div>
            <Text strong>文件大小</Text>
            <div style={styles.filterRow}>
              <Input
                type="number"
                placeholder="最小值"
                value={search.filterMinSize || ''}
                onChange={(e) => search.setFilterMinSize(e.target.value ? parseFloat(e.target.value) : null)}
                style={styles.filterGrow}
              />
              <Select
                value={search.filterMinSizeUnit}
                onChange={search.setFilterMinSizeUnit}
                style={styles.filterUnit}
                options={[
                  { value: 'B', label: 'B' },
                  { value: 'KB', label: 'KB' },
                  { value: 'MB', label: 'MB' },
                  { value: 'GB', label: 'GB' }
                ]}
              />
              <Input
                type="number"
                placeholder="最大值"
                value={search.filterMaxSize || ''}
                onChange={(e) => search.setFilterMaxSize(e.target.value ? parseFloat(e.target.value) : null)}
                style={styles.filterGrow}
              />
              <Select
                value={search.filterMaxSizeUnit}
                onChange={search.setFilterMaxSizeUnit}
                style={styles.filterUnit}
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
            <div style={styles.filterInput}>
              <RangePicker
                value={search.filterDateRange}
                onChange={(dates) => search.setFilterDateRange((dates as [any, any]) || [null, null])}
                style={styles.fullWidth}
              />
            </div>
          </div>

          <div style={styles.filterActions}>
            <Button icon={<ClearOutlined />} onClick={search.resetFilters}>
              重置筛选
            </Button>
          </div>
        </Space>
      </CustomModal>
    </Layout>
  );
};

export default Home;
