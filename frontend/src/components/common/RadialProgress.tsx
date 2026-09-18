import React from 'react';
import clsx from 'clsx';

interface RadialProgressProps {
  value: number; // 0 - 100
  size?: number;
  strokeWidth?: number;
  label?: string;
  sublabel?: string;
  gradient?: 'cyan-purple' | 'thermal' | 'emerald' | 'blue';
  className?: string;
}

export const RadialProgress: React.FC<RadialProgressProps> = ({
  value,
  size = 110,
  strokeWidth = 9,
  label,
  sublabel,
  gradient = 'cyan-purple',
  className,
}) => {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const clamped = Math.max(0, Math.min(100, value));
  const offset = circumference - (clamped / 100) * circumference;

  const gradientDefs = {
    'cyan-purple': (
      <linearGradient id="cyanPurpleGrad" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#4DFFDF" />
        <stop offset="100%" stopColor="#942BE6" />
      </linearGradient>
    ),
    'thermal': (
      <linearGradient id="thermalGrad" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#5EFF5A" />
        <stop offset="50%" stopColor="#FFA63F" />
        <stop offset="100%" stopColor="#FF0707" />
      </linearGradient>
    ),
    'emerald': (
      <linearGradient id="emeraldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#4DFFDF" />
        <stop offset="100%" stopColor="#5EFF5A" />
      </linearGradient>
    ),
    'blue': (
      <linearGradient id="blueGrad" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#38BDF8" />
        <stop offset="100%" stopColor="#176BF8" />
      </linearGradient>
    ),
  };

  const strokeUrl = {
    'cyan-purple': 'url(#cyanPurpleGrad)',
    'thermal': 'url(#thermalGrad)',
    'emerald': 'url(#emeraldGrad)',
    'blue': 'url(#blueGrad)',
  }[gradient];

  return (
    <div className={clsx('relative inline-flex flex-col items-center justify-center', className)}>
      <svg width={size} height={size} className="transform -rotate-90">
        <defs>{gradientDefs[gradient]}</defs>
        {/* Track */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="#25245D"
          strokeWidth={strokeWidth}
          fill="none"
        />
        {/* Progress Arc */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={strokeUrl}
          strokeWidth={strokeWidth}
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-all duration-700 ease-out"
        />
      </svg>

      {/* Center Label */}
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
        <span className="text-xl font-extrabold text-white tracking-tight leading-none">
          {Math.round(value)}%
        </span>
        {sublabel && (
          <span className="text-[10px] text-[#6A6A9F] tracking-wider uppercase mt-0.5">
            {sublabel}
          </span>
        )}
      </div>

      {label && (
        <span className="text-[11px] font-semibold text-[#A5A5D8] tracking-wide mt-2 text-center">
          {label}
        </span>
      )}
    </div>
  );
};
