import React, { ReactNode } from 'react';
import { Card, Divider, Typography } from 'antd';

interface SettingSectionProps {
  title: string;
  children: ReactNode;
}

const { Title } = Typography;

const SettingSection: React.FC<SettingSectionProps> = ({ title, children }) => {
  return (
    <div style={{ padding: '16px'}}>
      <Divider variant="dashed" style={{ borderColor: '#7cb305', margin: '8px 0', fontSize: '20px'}}>{title}</Divider>
      {children}
    </div>
  );
};

export default SettingSection;