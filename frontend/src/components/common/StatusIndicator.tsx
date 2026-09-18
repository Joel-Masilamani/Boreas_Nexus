import React from 'react';
import clsx from 'clsx';

interface StatusIndicatorProps {
  status: 'READY' | 'REAL_DATA' | 'PROJECTED' | 'WARNING' | 'PROCESSING';
  label?: string;
  className?: string;
}

export const StatusIndicator: React.FC<StatusIndicatorProps> = ({
  status,
  label,
  className,
}) => {
  const configs = {
    READY: {
      dot: 'bg-[#5EFF5A] shadow-[0_0_8px_#5EFF5A]',
      text: 'text-[#5EFF5A]',
      defaultLabel: 'SYSTEM READY',
    },
    REAL_DATA: {
      dot: 'bg-[#4DFFDF] shadow-[0_0_8px_#4DFFDF]',
      text: 'text-[#4DFFDF]',
      defaultLabel: 'OBSERVED ANALYTICAL DATA',
    },
    PROJECTED: {
      dot: 'bg-[#C084FC] shadow-[0_0_8px_#942BE6]',
      text: 'text-[#C084FC]',
      defaultLabel: 'DEMONSTRATION MODEL / PROJECTED',
    },
    WARNING: {
      dot: 'bg-[#FFA63F] shadow-[0_0_8px_#FFA63F]',
      text: 'text-[#FFA63F]',
      defaultLabel: 'DATA UNAVAILABLE',
    },
    PROCESSING: {
      dot: 'bg-[#176BF8] animate-ping shadow-[0_0_8px_#176BF8]',
      text: 'text-[#60A5FA]',
      defaultLabel: 'PROCESSING SIMULATION...',
    },
  };

  const cfg = configs[status];

  return (
    <div className={clsx('inline-flex items-center gap-2 text-xs font-bold tracking-wider', className)}>
      <span className={clsx('w-2 h-2 rounded-full inline-block', cfg.dot)} />
      <span className={clsx('uppercase text-[10px] tracking-[2px]', cfg.text)}>
        {label || cfg.defaultLabel}
      </span>
    </div>
  );
};
