import React from 'react';
import { Lock } from 'lucide-react';

interface EditorStatusBarProps {
  language: 'c' | 'fortran';
  accentColor: string;
  line: number;
  column: number;
  totalLines: number;
  readOnly?: boolean;
}

export const EditorStatusBar: React.FC<EditorStatusBarProps> = ({
  language,
  accentColor,
  line,
  column,
  totalLines,
  readOnly = true,
}) => {
  const langName = language === 'c' ? 'C / C++' : 'Fortran 90';

  return (
    <div className="editor-status-bar">
      <div className="editor-status-left">
        <span className="editor-status-pos" style={{ color: accentColor }}>
          Ln {line}, Col {column}
        </span>
        <span className="editor-status-sep">·</span>
        <span className="editor-status-item">{totalLines} lines</span>
      </div>
      <div className="editor-status-right">
        <span className="editor-status-item">UTF-8</span>
        <span className="editor-status-sep">·</span>
        <span className="editor-status-item" style={{ color: accentColor }}>
          {langName}
        </span>
        {readOnly && (
          <>
            <span className="editor-status-sep">·</span>
            <span className="editor-status-item editor-status-readonly">
              <Lock size={9} style={{ marginRight: 3 }} />
              Read-only
            </span>
          </>
        )}
      </div>
    </div>
  );
};
