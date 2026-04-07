import React, { useEffect, useState } from 'react';
import { Button } from 'antd';
import '../styles/customModal.css';

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
      }

      setAnimating(false);
      const timer3 = setTimeout(() => setVisible(false), 300);
      return () => clearTimeout(timer3);
    }, 0);

    return () => clearTimeout(timer1);
  }, [open]);

  if (!visible) return null;

  const modalStyle = {
    ['--modal-width' as string]: `${width}px`,
    ['--modal-height' as string]: height ? `${height}px` : 'auto',
  };

  return (
    <>
      <div
        className={`custom-modal-overlay${animating ? ' custom-modal-overlay--open' : ''}`}
        onClick={onClose}
      />

      <div
        className={`custom-modal custom-modal--${placement}${animating ? ' custom-modal--open' : ''}`}
        style={modalStyle}
      >
        <div className="custom-modal__header">
          <div className="custom-modal__title">{title}</div>
          {footer ? null : (
            <Button
              type="text"
              onClick={onClose}
              className="custom-modal__close"
            >
              ×
            </Button>
          )}
        </div>

        <div className="custom-modal__body">{children}</div>

        {footer && (
          <div className="custom-modal__footer">{footer}</div>
        )}
      </div>
    </>
  );
};

export default CustomModal;
