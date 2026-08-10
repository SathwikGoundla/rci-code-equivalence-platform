import React, { useRef, useState } from 'react';
import { Upload, X, FileCode, Code2, File } from 'lucide-react';

interface DropZoneProps {
  accept: string;
  label: string;
  sublabel?: string;
  accentColor: string;
  accentBg: string;
  file: File | null;
  onFileChange: (file: File | null) => void;
  icon?: 'c' | 'fortran' | 'generic';
  id?: string;
}

export const DropZone: React.FC<DropZoneProps> = ({
  accept,
  label,
  sublabel,
  accentColor,
  accentBg,
  file,
  onFileChange,
  icon = 'generic',
  id,
}) => {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(true);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    // Only clear if leaving the zone entirely (not a child element)
    if (!e.currentTarget.contains(e.relatedTarget as Node)) {
      setDragOver(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(false);
    const droppedFile = e.dataTransfer.files?.[0];
    if (droppedFile) {
      onFileChange(droppedFile);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0] ?? null;
    onFileChange(selectedFile);
    // Reset so same file can be re-selected
    e.target.value = '';
  };

  const handleRemove = (e: React.MouseEvent) => {
    e.stopPropagation();
    onFileChange(null);
  };

  const IconComponent = icon === 'c' ? Code2 : icon === 'fortran' ? FileCode : File;

  const zoneClasses = [
    'drop-zone',
    dragOver ? 'drag-over' : '',
    file ? 'has-file' : '',
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div
      className={zoneClasses}
      style={{ '--dz-accent': accentColor, '--dz-accent-bg': accentBg } as React.CSSProperties}
      onClick={() => !file && inputRef.current?.click()}
      onDragEnter={handleDragEnter}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && !file && inputRef.current?.click()}
      aria-label={`Upload ${label}`}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        style={{ display: 'none' }}
        id={id}
        onChange={handleInputChange}
      />

      {file ? (
        /* ── Has File State ── */
        <div className="drop-zone-file-info">
          <div className="drop-zone-file-icon" style={{ background: accentBg, color: accentColor }}>
            <IconComponent size={18} />
          </div>
          <div className="drop-zone-file-meta">
            <div className="drop-zone-file-name">{file.name}</div>
            <div className="drop-zone-file-size">
              {(file.size / 1024).toFixed(1)} KB &nbsp;·&nbsp;
              <span style={{ color: 'var(--accent-green)' }}>Ready</span>
            </div>
          </div>
          <button
            className="drop-zone-remove"
            onClick={handleRemove}
            title="Remove file"
            aria-label="Remove file"
          >
            <X size={14} />
          </button>
        </div>
      ) : (
        /* ── Empty / Drag State ── */
        <div className="drop-zone-empty">
          <div
            className={`drop-zone-icon-wrap${dragOver ? ' drop-zone-icon-wrap--active' : ''}`}
            style={{ background: accentBg, color: accentColor }}
          >
            {dragOver ? <Upload size={22} /> : <IconComponent size={22} />}
          </div>
          <div className="drop-zone-label">{label}</div>
          {sublabel && (
            <div className="drop-zone-sublabel">{sublabel}</div>
          )}
          <div className="drop-zone-hint">
            {dragOver ? 'Drop to upload' : 'Drag & drop or click to browse'}
          </div>
        </div>
      )}
    </div>
  );
};
