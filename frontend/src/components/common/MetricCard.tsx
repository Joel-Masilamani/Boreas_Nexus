import React from 'react';
import clsx from 'clsx';

interface MetricCardProps {
  label: string;
  value: string | number;
  unit?: string;
  subtext?: string;
  icon?: React.ReactNode;
  trend?: {
    value: string;
    isPositive: boolean;
  };
  highlightColor?: 'cyan' | 'purple' | 'blue' | 'warm' | 'hot' | 'extreme' | 'none';
  className?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  unit,
  subtext,
  icon,
  trend,
  highlightColor = 'none',
  className,
}) => {
  const highlightStyles = {
    none: 'border-[#323273] bg-[#191932]',
    cyan: 'border-[#4DFFDF]/40 bg-[#191932] shadow-[0_0_15px_rgba(77,255,223,0.1)]',
    purple: 'border-[#942BE6]/40 bg-[#191932] shadow-[0_0_15px_rgba(148,43,230,0.1)]',
    blue: 'border-[#176BF8]/40 bg-[#191932]',
    warm: 'border-[#FFA63F]/40 bg-[#191932]',
    hot: 'border-[#FF7A00]/50 bg-[#191932]',
    extreme: 'border-[#FF0707]/60 bg-[#191932] shadow-[0_0_20px_rgba(255,7,7,0.15)]',
  };

  const textColors = {
    none: 'text-white',
    cyan: 'text-[#4DFFDF]',
    purple: 'text-[#C084FC]',
    blue: 'text-[#60A5FA]',
    warm: 'text-[#FFA63F]',
    hot: 'text-[#FF9233]',
    extreme: 'text-[#FF4D4D]',
  };

  return (
    <div
      className={clsx(
        'p-3.5 md:p-4 rounded-2xl border transition-all duration-200',
        highlightStyles[highlightColor],
        className
      )}
    >
      <div className="flex items-center justify-between gap-2 mb-1.5">
        <span className="text-[10px] font-bold tracking-[3px] uppercase text-[#6A6A9F]">
          {label}
        </span>
        {icon && <div className="text-[#6A6A9F]">{icon}</div>}
      </div>

      <div className="flex items-baseline gap-1.5">
        <span
          className={clsx(
            'text-2xl md:text-3xl font-extrabold tracking-tight font-sans tabular-nums',
            textColors[highlightColor]
          )}
        >
          {value}
        </span>
        {unit && <span className="text-xs font-semibold text-[#6A6A9F]">{unit}</span>}
      </div>

      {(subtext || trend) && (
        <div className="flex items-center justify-between gap-2 mt-2 pt-2 border-t border-[#242748]/60 text-[11px]">
          {subtext && <span className="text-[#6A6A9F] truncate">{subtext}</span>}
          {trend && (
            <span
              className={clsx(
                'font-bold ml-auto',
                trend.isPositive ? 'text-[#5EFF5A]' : 'text-[#FF4D4D]'
              )}
            >
              {trend.value}
            </span>
          )}
        </div>
      )}
    </div>
  );
};
