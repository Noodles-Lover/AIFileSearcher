import React from 'react';
import { 
  File as LucideFile, 
  Folder, 
  FileImage, 
  FileVideo, 
  FileAudio, 
  FileText, 
  FileArchive, 
  FileCode, 
  FileSpreadsheet 
} from 'lucide-react';

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
  chunk_count?: number;
}

interface FileIconProps {
  record: FileItem;
}

const FileIcon: React.FC<FileIconProps> = ({ record }) => {
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

export default FileIcon;
export type { FileItem };
