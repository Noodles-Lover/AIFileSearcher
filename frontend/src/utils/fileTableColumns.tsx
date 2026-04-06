import type { ColumnsType } from 'antd/es/table';
import FileIcon, { type FileItem } from '../components/FileIcon';
import { Space, Button, Tag, Typography, Dropdown } from 'antd';
import { 
  FileOutlined, 
  EyeOutlined, 
  DatabaseOutlined, 
  FolderOpenOutlined, 
  MoreOutlined 
} from '@ant-design/icons';

const { Text } = Typography;

interface ColumnsProps {
  onOpenFile: (path: string) => void;
  onPreview: (record: FileItem) => void;
  onViewChunk: (record: FileItem) => void;
  onOpenFolder: (path: string) => void;
}

/**
 * 生成表格列定义
 */
export const generateColumns = ({
  onOpenFile,
  onPreview,
  onViewChunk,
  onOpenFolder
}: ColumnsProps): ColumnsType<FileItem> => {
  return [
    {
      title: '名稱',
      dataIndex: 'name',
      key: 'name',
      ellipsis: true,
      width: '40%',
      render: (text, record) => (
        <Space direction="vertical" size={0} style={{ width: '100%' }}>
          <Space onClick={() => onOpenFile(record.path)} style={{ cursor: 'pointer' }}>
            <FileIcon record={record} />
            <Text strong>{text}</Text>
            {record.score && (
              <Tag color="green">相似度: {(1 / (1 + record.score)).toFixed(4)}</Tag>
            )}
            {record.chunk_count && record.chunk_count > 1 && (
              <Tag color="orange">{record.chunk_count}个分块</Tag>
            )}
          </Space>
          {record.content_preview && (
            <Text 
              type="secondary" 
              style={{ 
                fontSize: '12px', 
                marginLeft: 24,
                cursor: 'pointer',
                color: '#1890ff'
              }} 
              onClick={() => onViewChunk(record)}
            >
              {record.content_preview.length > 200 ? record.content_preview.substring(0, 200) + '...' : record.content_preview}
            </Text>
          )}
        </Space>
      ),
      sorter: (a, b) => a.name.localeCompare(b.name),
    },
    {
      title: '相对位置',
      dataIndex: 'relativePath',
      key: 'relativePath',
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
                onClick: () => onOpenFile(record.path)
              },
              {
                key: 'preview',
                label: '預覽',
                icon: <EyeOutlined />,
                onClick: () => onPreview(record),
                disabled: record.type === 'folder'
              },
              {
                key: 'view-chunk',
                label: '查看分块',
                icon: <DatabaseOutlined />,
                onClick: () => onViewChunk(record),
                disabled: record.type === 'folder' || !record.content_preview
              },
              {
                key: 'explorer',
                label: '在資源管理器中打開',
                icon: <FolderOpenOutlined />,
                onClick: () => onOpenFolder(record.path)
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
};