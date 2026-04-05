import React, { useEffect, useState } from 'react';
import { Button } from 'antd';

interface CustomModalProps {
  title: string;
  open: boolean;
  onClose: () => void;
  footer?: React.ReactNode;
  width?: number;
  height?: number;
  children: React.ReactNode;
  placement?: 'center' | 'top' | 'right';
}

const CustomModal: React.FC<CustomModalProps> = ({
  title,
  open,
  onClose,
  footer,
  width = 600,
  height,
  children,
  placement = 'center'
}) => {
  const [visible, setVisible] = useState(false);
  const [animating, setAnimating] = useState(false);

  useEffect(() => {
    const timer1 = setTimeout(() => {
      if (open) {
        setVisible(true);
        const timer2 = setTimeout(() => setAnimating(true), 10);
        return () => clearTimeout(timer2);
      } else {
        setAnimating(false);
        const timer3 = setTimeout(() => setVisible(false), 300);
        return () => clearTimeout(timer3);
      }
    }, 0);
    
    return () => clearTimeout(timer1);
  }, [open]);

  if (!visible) return null;

  const getAnimationStyle = () => {
    const baseStyle = {
      transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
    };

    switch (placement) {
      case 'top':
        return {
          ...baseStyle,
          transform: animating ? 'translateY(0)' : 'translateY(-100%)',
          opacity: animating ? 1 : 0
        };
      case 'right':
        return {
          ...baseStyle,
          transform: animating ? 'translateX(0)' : 'translateX(100%)',
          opacity: animating ? 1 : 0
        };
      default:
        return {
          ...baseStyle,
          transform: animating ? 'translate(-50%, -50%) scale(1)' : 'translate(-50%, -50%) scale(0.8)',
          opacity: animating ? 1 : 0
        };
    }
  };

  const getStyle = () => {
    const baseStyle = {
      position: 'fixed' as const,
      backgroundColor: 'white',
      boxShadow: '0 4px 16px rgba(0, 0, 0, 0.15)',
      zIndex: 1000,
      display: 'flex',
      flexDirection: 'column' as const,
      ...getAnimationStyle()
    };

    switch (placement) {
      case 'top':
        return {
          ...baseStyle,
          top: 0,
          left: 0,
          right: 0,
          height: height || 200,
        };
      case 'right':
        return {
          ...baseStyle,
          top: 0,
          right: 0,
          bottom: 0,
          width: width || 800,
        };
      default:
        return {
          ...baseStyle,
          top: '50%',
          left: '50%',
          width: width || 600,
          height: height || 'auto',
          borderRadius: '8px',
          maxHeight: '80vh'
        };
    }
  };

  return (
    <>
      {/* 遮罩层 */}
      <div
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: `rgba(0, 0, 0, ${animating ? 0.45 : 0})`,
          zIndex: 999,
          transition: 'opacity 0.3s ease'
        }}
        onClick={onClose}
      />
      
      {/* 弹窗内容 */}
      <div style={getStyle()}>
        {/* 标题栏 */}
        <div
          style={{
            padding: '16px 24px',
            borderBottom: '1px solid #f0f0f0',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}
        >
          <div style={{ fontSize: '16px', fontWeight: 500 }}>
            {title}
          </div>
          {footer ? null : (
            <Button
              type="text"
              onClick={onClose}
              style={{ fontSize: '18px', height: '22px', width: '22px' }}
            >
              ×
            </Button>
          )}
        </div>
        
        {/* 内容区域 */}
        <div
          style={{
            flex: 1,
            padding: '24px',
            overflow: 'auto'
          }}
        >
          {children}
        </div>
        
        {/* 底部区域 */}
        {footer && (
          <div
            style={{
              padding: '10px 16px',
              borderTop: '1px solid #f0f0f0',
              textAlign: 'right'
            }}
          >
            {footer}
          </div>
        )}
      </div>
    </>
  );
};

export default CustomModal;
