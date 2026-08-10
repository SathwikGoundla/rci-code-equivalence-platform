import React from 'react';

interface StatusCardProps {
  label: string;
  value: string | number;
  subLabel?: string;
  icon?: React.ReactNode;
  accentColor?: string;
  valueColor?: string;
}

export const StatusCard: React.FC<StatusCardProps> = ({
  label,
  value,
  subLabel,
  icon,
  accentColor = 'var(--accent-blue)',
  valueColor = 'var(--text-primary)',
}) => {
  return (
    <div className="stat-card" style={{ '--accent-color': accentColor } as React.CSSProperties}>
      {icon && (
        <div className="stat-card-icon" style={{ background: `${accentColor}18`, color: accentColor }}>
          {icon}
        </div>
      )}
      <div className="stat-card-value" style={{ color: valueColor }}>{value}</div>
      <div className="stat-card-label">{label}</div>
      {subLabel && (
        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>{subLabel}</div>
      )}
    </div>
  );
};
