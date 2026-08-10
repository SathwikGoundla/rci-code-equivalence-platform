import React, { useState } from 'react';
import { Copy, Check, Maximize2, Minimize2, ZoomIn, ZoomOut } from 'lucide-react';

interface EditorToolbarProps {
  language: 'c' | 'fortran';
  filename?: string;
  accentColor: string;
  accentBg: string;
  expanded: boolean;
  onToggleExpand: () => void;
  fontSize: number;
  onFontSizeChange: (size: number) => void;
  getContent: () => string;
}

export const EditorToolbar: React.FC<EditorToolbarProps> = ({
  language,
  filename,
  accentColor,
  accentBg,
  expanded,
  onToggleExpand,
  fontSize,
  onFontSizeChange,
  getContent,
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      const content = getContent();
      await navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      // Fallback: ignore clipboard errors in offline env
    }
  };

  const langLabel = language === 'c' ? 'C' : 'Fortran';
  const langDesc = language === 'c' ? 'C Source' : 'Fortran 90';

  return (
    <div className="editor-toolbar">
      {/* Left: language badge + filename */}
      <div className="editor-toolbar-left">
        <span
          className="editor-lang-pill"
          style={{ background: accentBg, color: accentColor, borderColor: accentColor + '44' }}
        >
          {langLabel}
        </span>
        <span className="editor-toolbar-filename">
          {filename ?? langDesc}
        </span>
      </div>

      {/* Right: action buttons */}
      <div className="editor-toolbar-right">
        <button
          className="editor-toolbar-btn"
          onClick={() => onFontSizeChange(Math.max(10, fontSize - 1))}
          title="Decrease font size"
          aria-label="Decrease font size"
        >
          <ZoomOut size={13} />
        </button>
        <span className="editor-font-size">{fontSize}px</span>
        <button
          className="editor-toolbar-btn"
          onClick={() => onFontSizeChange(Math.min(20, fontSize + 1))}
          title="Increase font size"
          aria-label="Increase font size"
        >
          <ZoomIn size={13} />
        </button>

        <div className="editor-toolbar-divider" />

        <button
          className="editor-toolbar-btn"
          onClick={handleCopy}
          title="Copy to clipboard"
          aria-label="Copy code"
        >
          {copied ? <Check size={13} color="var(--accent-green)" /> : <Copy size={13} />}
        </button>

        <button
          className="editor-toolbar-btn"
          onClick={onToggleExpand}
          title={expanded ? 'Collapse editor' : 'Expand editor'}
          aria-label={expanded ? 'Collapse' : 'Expand'}
        >
          {expanded ? <Minimize2 size={13} /> : <Maximize2 size={13} />}
        </button>
      </div>
    </div>
  );
};
