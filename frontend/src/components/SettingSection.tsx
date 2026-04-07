import React from 'react';
import type { ReactNode } from 'react';
import { Divider } from 'antd';

interface SettingSectionProps {
  title: string;
  children: ReactNode;
}

const SettingSection: React.FC<SettingSectionProps> = ({ title, children }) => {
  return (
    <div style={{ padding: '16px' }}>
      <Divider
        variant="dashed"
        style={{ margin: '8px 0', fontSize: '20px', borderColor: '#7cb305' }}
      >
        {title}
      </Divider>
      {children}
    </div>
  );
};

export default SettingSection;
