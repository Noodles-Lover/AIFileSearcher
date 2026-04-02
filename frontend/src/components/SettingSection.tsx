import React, { ReactNode } from 'react';
import { Card, Divider, Typography } from 'antd';

interface SettingSectionProps {
  title: string;
  children: ReactNode;
}

const { Title } = Typography;

const SettingSection: React.FC<SettingSectionProps> = ({ title, children }) => {
  return (
    <Card title={title} variant="borderless">
      <Divider style={{ margin: '8px 0', borderTop: '2px solid #d9d9d9' }} />
      {children}
    </Card>
  );
};

export default SettingSection;