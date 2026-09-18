import React from 'react';
import clsx from 'clsx';

interface PanelProps {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  badge?: React.ReactNode;
  headerAction?: React.ReactNode;
  className?: string;
  variant?: 'base' | 'elevated' | 'active';
  compact?: boolean;
}

export const Panel: React.FC<PanelProps> = ({
  children,
  title,
  subtitle,
  badge,
  headerAction,
  className,
  variant = 'base',
  compact = false,
}) => {
  const variantStyles = {
    base: 'bg-[#191932] border-[#323273]',
    elevated: 'bg-[#1F1F43] border-[#323273]',
    active: 'bg-[#25245D] border-[#4DFFDF] shadow-[0_0_20px_rgba(77,255,223,0.15)]',
  };

  return (
    <div
      className={clsx(
        'rounded-2xl border transition-all duration-200',
        variantStyles[variant],
        compact ? 'p-3' : 'p-4 md:p-5',
        className
      )}
    >
      {(title || badge || headerAction) && (
        <div className="flex items-center justify-between gap-2 mb-3.5 pb-2 border-b border-[#242748]">
          <div>
            {title && (
              <h3 className="text-sm md:text-base font-bold text-white tracking-wide flex items-center gap-2">
                {title}
                {badge}
              </h3>
            )}
            {subtitle && (
              <p className="text-[11px] text-[#6A6A9F] tracking-wide mt-0.5">{subtitle}</p>
            )}
          </div>
          {headerAction && <div>{headerAction}</div>}
        </div>
      )}
      {children}
    </div>
  );
};
