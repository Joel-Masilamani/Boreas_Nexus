import React from 'react';
import clsx from 'clsx';

export type BadgeVariant = 
  | 'cyan' 
  | 'purple' 
  | 'blue' 
  | 'cool' 
  | 'moderate' 
  | 'warm' 
  | 'hot' 
  | 'extreme'
  | 'muted';

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  className?: string;
  dot?: boolean;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'cyan',
  className,
  dot = false,
}) => {
  const variantStyles: Record<BadgeVariant, string> = {
    cyan: 'bg-[#4DFFDF]/10 text-[#4DFFDF] border-[#4DFFDF]/30',
    purple: 'bg-[#942BE6]/10 text-[#C084FC] border-[#942BE6]/30',
    blue: 'bg-[#176BF8]/15 text-[#60A5FA] border-[#176BF8]/40',
    cool: 'bg-[#3B82F6]/15 text-[#93C5FD] border-[#3B82F6]/40',
    moderate: 'bg-[#5EFF5A]/15 text-[#5EFF5A] border-[#5EFF5A]/40',
    warm: 'bg-[#FFA63F]/15 text-[#FFA63F] border-[#FFA63F]/40',
    hot: 'bg-[#FF7A00]/20 text-[#FF9233] border-[#FF7A00]/50',
    extreme: 'bg-[#FF0707]/20 text-[#FF4D4D] border-[#FF0707]/60 shadow-[0_0_12px_rgba(255,7,7,0.3)]',
    muted: 'bg-[#25245D]/40 text-[#6A6A9F] border-[#323273]',
  };

  const dotStyles: Record<BadgeVariant, string> = {
    cyan: 'bg-[#4DFFDF] shadow-[0_0_6px_#4DFFDF]',
    purple: 'bg-[#942BE6] shadow-[0_0_6px_#942BE6]',
    blue: 'bg-[#176BF8] shadow-[0_0_6px_#176BF8]',
    cool: 'bg-[#3B82F6] shadow-[0_0_6px_#3B82F6]',
    moderate: 'bg-[#5EFF5A] shadow-[0_0_6px_#5EFF5A]',
    warm: 'bg-[#FFA63F] shadow-[0_0_6px_#FFA63F]',
    hot: 'bg-[#FF7A00] shadow-[0_0_6px_#FF7A00]',
    extreme: 'bg-[#FF0707] shadow-[0_0_8px_#FF0707]',
    muted: 'bg-[#6A6A9F]',
  };

  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold tracking-wider uppercase border',
        variantStyles[variant],
        className
      )}
    >
      {dot && <span className={clsx('w-1.5 h-1.5 rounded-full', dotStyles[variant])} />}
      {children}
    </span>
  );
};
