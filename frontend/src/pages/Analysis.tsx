import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Header } from '../components/layout/Header';
import { uploadAndAnalyze, getAnalysis } from '../services/api';
import { useAppStore } from '../services/store';
import type { AnalysisResult, GapReport } from '../types';
import { DropZone } from '../components/ui/DropZone';
import { EditorToolbar } from '../components/ui/EditorToolbar';
import { EditorStatusBar } from '../components/ui/EditorStatusBar';
import { AnalysisProgressBar } from '../components/ui/AnalysisProgressBar';
import {
  AlertTriangle,
  ChevronDown,
  ChevronRight,
  Info,
  ChevronsLeftRight,
  PlayCircle,
} from 'lucide-react';
import Editor, { useMonaco } from '@monaco-editor/react';

/* ── Fortran language registration ───────────────────────────────────────── */
const FORTRAN_KEYWORDS = [
  'PROGRAM','END','SUBROUTINE','FUNCTION','MODULE','USE','IMPLICIT','NONE',
  'REAL','INTEGER','DOUBLE','PRECISION','CHARACTER','LOGICAL','COMPLEX',
  'DO','ENDDO','IF','THEN','ELSE','ELSEIF','ENDIF','WHILE','CONTINUE',
  'CALL','RETURN','STOP','PRINT','WRITE','READ','FORMAT','OPEN','CLOSE',
  'ALLOCATE','DEALLOCATE','PARAMETER','DATA','COMMON','DIMENSION',
  'INTENT','IN','OUT','INOUT','KIND','LEN','SIZE','SQRT','ABS',
  'DBLE','REAL','INT','NINT','MOD','MIN','MAX','SUM','PRODUCT',
];

function registerFortranLanguage(monaco: ReturnType<typeof useMonaco>) {
  if (!monaco) return;
  const langs = monaco.languages.getLanguages();
  if (langs.some((l) => l.id === 'fortran')) return; // already registered

  monaco.languages.register({ id: 'fortran', extensions: ['.f90', '.f', '.f95', '.f03', '.for'] });
  monaco.languages.setMonarchTokensProvider('fortran', {
    ignoreCase: true,
    keywords: FORTRAN_KEYWORDS,
    tokenizer: {
      root: [
        [/!.*$/, 'comment'],
        [/[0-9]+(\.[0-9]+)?([eEdD][+-]?[0-9]+)?/, 'number'],
        [/"([^"\\]|\\.)*$/, 'string.invalid'],
        [/"/, { token: 'string.quote', bracket: '@open', next: '@string_dq' }],
        [/'([^'\\]|\\.)*$/, 'string.invalid'],
        [/'/, { token: 'string.quote', bracket: '@open', next: '@string_sq' }],
        [/[a-zA-Z_][a-zA-Z0-9_]*/,
          { cases: { '@keywords': 'keyword', '@default': 'identifier' } }],
        [/[=<>!+\-*/%&|^~]/, 'operator'],
        [/[(){}\[\],;.]/, 'delimiter'],
      ],
      string_dq: [
        [/[^\\"]+/, 'string'],
        [/"/, { token: 'string.quote', bracket: '@close', next: '@pop' }],
      ],
      string_sq: [
        [/[^\\']+/, 'string'],
        [/'/, { token: 'string.quote', bracket: '@close', next: '@pop' }],
      ],
    },
  } as any);

  monaco.editor.defineTheme('rci-dark', {
    base: 'vs-dark',
    inherit: true,
    rules: [
      { token: 'keyword',    foreground: '7DD3FC', fontStyle: 'bold' },
      { token: 'comment',    foreground: '4A5570', fontStyle: 'italic' },
      { token: 'string',     foreground: 'A5D6A7' },
      { token: 'number',     foreground: 'FFCC80' },
      { token: 'operator',   foreground: '90CAF9' },
      { token: 'identifier', foreground: 'E8EDF5' },
    ],
    colors: {
      'editor.background':           '#0d1117',
      'editor.foreground':           '#E8EDF5',
      'editor.lineHighlightBackground': '#1a2035',
      'editorLineNumber.foreground': '#3a4a65',
      'editorCursor.foreground':     '#3D7AF5',
      'editor.selectionBackground':  '#1c3a6e',
    },
  });
}

/* ── Gap row ─────────────────────────────────────────────────────────────── */
const SeverityBadge: React.FC<{ severity: string }> = ({ severity }) => {
  const cls =
    severity === 'CRITICAL' || severity === 'HIGH'
      ? 'badge-error'
      : severity === 'MEDIUM'
      ? 'badge-warning'
      : 'badge-success';
  return <span className={`badge ${cls}`}>{severity}</span>;
};

const GapRow: React.FC<{
  gap: GapReport;
  onJumpToCode?: (lang: 'c' | 'fortran', line: number) => void;
}> = ({ gap, onJumpToCode }) => {
  const [expanded, setExpanded] = useState(false);

  const parseLineNumber = (locStr: string): number | null => {
    const parts = locStr.split(':');
    if (parts.length < 2) return null;
    const linePart = parts[1].split('-')[0];
    const lineNum = parseInt(linePart, 10);
    return isNaN(lineNum) ? null : lineNum;
  };

  const handleLineClick = (lang: 'c' | 'fortran', locationStr: string) => {
    const line = parseLineNumber(locationStr);
    if (line !== null && onJumpToCode) onJumpToCode(lang, line);
  };

  return (
    <>
      <tr onClick={() => setExpanded(!expanded)} style={{ cursor: 'pointer' }}>
        <td>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--accent-cyan)' }}>
            {gap.gap_id}
          </span>
        </td>
        <td style={{ textTransform: 'capitalize' }}>{gap.category.replace(/_/g, ' ')}</td>
        <td><SeverityBadge severity={gap.severity} /></td>
        <td style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
          {gap.location}
        </td>
        <td>{Math.round(gap.confidence * 100)}%</td>
        <td>{expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}</td>
      </tr>
      {expanded && (
        <tr>
          <td colSpan={6} style={{ padding: '0 0 12px 0' }}>
            <div
              style={{
                background: 'var(--bg-primary)',
                borderRadius: 'var(--radius-md)',
                padding: 16,
                margin: '0 0 4px 0',
                border: '1px solid var(--border-subtle)',
              }}
            >
              <div style={{ marginBottom: 12 }}>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 4 }}>
                  Explanation
                </div>
                <div style={{ fontSize: 13, color: 'var(--text-primary)' }}>{gap.explanation}</div>
              </div>
              <div style={{ marginBottom: 12 }}>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 4 }}>
                  Evidence
                </div>
                <div
                  style={{
                    fontSize: 12,
                    fontFamily: 'var(--font-mono)',
                    color: 'var(--text-code)',
                    background: 'var(--bg-secondary)',
                    padding: '8px 12px',
                    borderRadius: 'var(--radius-sm)',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <span>{gap.evidence}</span>
                  {onJumpToCode && (
                    <button
                      className="btn btn-secondary"
                      style={{ padding: '2px 6px', fontSize: 10 }}
                      onClick={(e) => {
                        e.stopPropagation();
                        const isFortran = gap.location.toLowerCase().includes('.f90') || gap.location.toLowerCase().includes('.f');
                        handleLineClick(isFortran ? 'fortran' : 'c', gap.location);
                      }}
                    >
                      Jump to Code
                    </button>
                  )}
                </div>
              </div>
              <div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 4 }}>
                  Suggested Resolution
                </div>
                <div style={{ fontSize: 13, color: 'var(--accent-green)' }}>{gap.suggested_resolution}</div>
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  );
};

/* ── Main Analysis Page ──────────────────────────────────────────────────── */
export const Analysis: React.FC = () => {
  const [searchParams] = useSearchParams();
  const sessionId = searchParams.get('session_id');
  const { activeProject } = useAppStore();
  const monaco = useMonaco();

  /* ── File state ── */
  const [cFile, setCFile] = useState<File | null>(null);
  const [fortranFile, setFortranFile] = useState<File | null>(null);
  const [cCode, setCCode] = useState<string>('// Upload C code to view');
  const [fortranCode, setFortranCode] = useState<string>('! Upload Fortran code to view');

  /* ── Analysis state ── */
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /* ── Editor refs ── */
  const cEditorRef = useRef<any>(null);
  const fortranEditorRef = useRef<any>(null);

  /* ── Editor UI state ── */
  const [cFontSize, setCFontSize] = useState(12);
  const [fortranFontSize, setFortranFontSize] = useState(12);
  const [cExpanded, setCExpanded] = useState(false);
  const [fortranExpanded, setFortranExpanded] = useState(false);
  const [cCursor, setCCursor] = useState({ line: 1, col: 1 });
  const [fortranCursor, setFortranCursor] = useState({ line: 1, col: 1 });

  /* ── Resize handle state ── */
  const [leftPct, setLeftPct] = useState(50); // % width for left pane
  const containerRef = useRef<HTMLDivElement>(null);
  const draggingRef = useRef(false);

  /* ── Register Fortran + custom theme once Monaco loads ── */
  useEffect(() => {
    if (monaco) registerFortranLanguage(monaco);
  }, [monaco]);

  /* ── Load session from history ── */
  useEffect(() => {
    if (sessionId) {
      const load = async () => {
        setLoading(true);
        setError(null);
        try {
          const data = await getAnalysis(sessionId);
          setResult(data);
          setCCode('// History mode: source code not stored in offline DB.\n// Re-upload C and Fortran files to inspect code side-by-side.');
          setFortranCode('! History mode: source code not stored in offline DB.\n! Re-upload C and Fortran files to inspect code side-by-side.');
        } catch {
          setError('Failed to load past session details.');
        } finally {
          setLoading(false);
        }
      };
      load();
    }
  }, [sessionId]);

  /* ── File reader effects ── */
  useEffect(() => {
    if (cFile) {
      const reader = new FileReader();
      reader.onload = (e) => setCCode(e.target?.result as string);
      reader.readAsText(cFile);
    } else {
      setCCode('// Upload C code to view');
    }
  }, [cFile]);

  useEffect(() => {
    if (fortranFile) {
      const reader = new FileReader();
      reader.onload = (e) => setFortranCode(e.target?.result as string);
      reader.readAsText(fortranFile);
    } else {
      setFortranCode('! Upload Fortran code to view');
    }
  }, [fortranFile]);

  /* ── Resize handle logic ── */
  const onMouseDownResize = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    draggingRef.current = true;
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';

    const onMove = (ev: MouseEvent) => {
      if (!containerRef.current || !draggingRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const pct = Math.min(80, Math.max(20, ((ev.clientX - rect.left) / rect.width) * 100));
      setLeftPct(pct);
    };

    const onUp = () => {
      draggingRef.current = false;
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
    };

    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
  }, []);

  /* ── Analyze ── */
  const handleAnalyze = async () => {
    if (!cFile || !fortranFile) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await uploadAndAnalyze(cFile, fortranFile, activeProject?.id || null);
      setResult(data);
    } catch (e: any) {
      setError(e.response?.data?.detail?.detail || e.message || 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  /* ── Jump to code ── */
  const handleJumpToCode = (lang: 'c' | 'fortran', line: number) => {
    const editor = lang === 'c' ? cEditorRef.current : fortranEditorRef.current;
    if (editor) {
      editor.revealLineInCenter(line);
      editor.setPosition({ lineNumber: line, column: 1 });
      editor.focus();
    }
  };

  /* ── Editor options ── */
  const baseEditorOptions = (fontSize: number) => ({
    readOnly: true,
    minimap: { enabled: false },
    fontSize,
    lineNumbersMinChars: 3,
    scrollBeyondLastLine: false,
    renderLineHighlight: 'line' as const,
    renderWhitespace: 'none' as const,
    smoothScrolling: true,
    cursorBlinking: 'smooth' as const,
    padding: { top: 8, bottom: 8 },
  });

  const editorTheme = 'rci-dark';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <Header
        title="Code Analysis"
        subtitle={
          activeProject
            ? `Analyzing in project: ${activeProject.name}`
            : 'Upload C and Fortran source files for structural and semantic analysis'
        }
      />
      <div className="page-content">

        {/* ── Upload ── */}
        <div className="page-section">
          <div className="section-title">Source Files</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
            <DropZone
              id="input-c-file"
              accept=".c,.h"
              label="C Source File"
              sublabel=".c / .h"
              accentColor="var(--accent-blue)"
              accentBg="rgba(61,122,245,0.12)"
              icon="c"
              file={cFile}
              onFileChange={setCFile}
            />
            <DropZone
              id="input-fortran-file"
              accept=".f90,.f,.f95,.f03,.for"
              label="Fortran Source File"
              sublabel=".f90 / .f / .f95"
              accentColor="var(--accent-purple)"
              accentBg="rgba(139,92,246,0.12)"
              icon="fortran"
              file={fortranFile}
              onFileChange={setFortranFile}
            />
          </div>

          <button
            id="btn-analyze"
            className="btn btn-primary"
            onClick={handleAnalyze}
            disabled={!cFile || !fortranFile || loading}
          >
            {loading ? (
              <>
                <div className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} />
                Analyzing…
              </>
            ) : (
              <>
                <PlayCircle size={14} />
                Analyze Both Files
              </>
            )}
          </button>
        </div>

        {/* ── Progress Bar ── */}
        <AnalysisProgressBar active={loading} />

        {/* ── Error ── */}
        {error && (
          <div className="alert alert-error" style={{ marginBottom: 20 }}>
            <AlertTriangle size={16} />
            {error}
          </div>
        )}

        {/* ── Side-by-Side Monaco Editor ── */}
        <div className="page-section">
          <div className="section-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <ChevronsLeftRight size={16} /> Code Comparison View
          </div>

          {/* Editor container with resize */}
          <div
            ref={containerRef}
            style={{
              display: 'flex',
              height: 400,
              gap: 0,
              borderRadius: 'var(--radius-md)',
              overflow: 'hidden',
            }}
          >
            {/* ── C Editor ── */}
            <div
              className={`editor-wrapper${cExpanded ? ' expanded' : ''}`}
              style={{
                width: cExpanded ? undefined : `calc(${leftPct}% - 4px)`,
                '--ew-accent': 'var(--accent-blue)',
              } as React.CSSProperties}
            >
              <EditorToolbar
                language="c"
                filename={cFile?.name}
                accentColor="var(--accent-blue)"
                accentBg="rgba(61,122,245,0.12)"
                expanded={cExpanded}
                onToggleExpand={() => setCExpanded((v) => !v)}
                fontSize={cFontSize}
                onFontSizeChange={setCFontSize}
                getContent={() => cCode}
              />
              <div style={{ flex: 1, overflow: 'hidden' }}>
                <Editor
                  height="100%"
                  language="c"
                  theme={editorTheme}
                  value={cCode}
                  options={baseEditorOptions(cFontSize)}
                  onMount={(editor) => {
                    cEditorRef.current = editor;
                    editor.onDidChangeCursorPosition((e) => {
                      setCCursor({ line: e.position.lineNumber, col: e.position.column });
                    });
                  }}
                />
              </div>
              <EditorStatusBar
                language="c"
                accentColor="var(--accent-blue)"
                line={cCursor.line}
                column={cCursor.col}
                totalLines={cCode.split('\n').length}
              />
            </div>

            {/* ── Resize Handle ── */}
            <div
              className="editor-resize-handle"
              onMouseDown={onMouseDownResize}
              title="Drag to resize"
              style={{ alignSelf: 'stretch' }}
            />

            {/* ── Fortran Editor ── */}
            <div
              className={`editor-wrapper${fortranExpanded ? ' expanded' : ''}`}
              style={{
                width: fortranExpanded ? undefined : `calc(${100 - leftPct}% - 4px)`,
                '--ew-accent': 'var(--accent-purple)',
              } as React.CSSProperties}
            >
              <EditorToolbar
                language="fortran"
                filename={fortranFile?.name}
                accentColor="var(--accent-purple)"
                accentBg="rgba(139,92,246,0.12)"
                expanded={fortranExpanded}
                onToggleExpand={() => setFortranExpanded((v) => !v)}
                fontSize={fortranFontSize}
                onFontSizeChange={setFortranFontSize}
                getContent={() => fortranCode}
              />
              <div style={{ flex: 1, overflow: 'hidden' }}>
                <Editor
                  height="100%"
                  language="fortran"
                  theme={editorTheme}
                  value={fortranCode}
                  options={baseEditorOptions(fortranFontSize)}
                  onMount={(editor) => {
                    fortranEditorRef.current = editor;
                    editor.onDidChangeCursorPosition((e) => {
                      setFortranCursor({ line: e.position.lineNumber, col: e.position.column });
                    });
                  }}
                />
              </div>
              <EditorStatusBar
                language="fortran"
                accentColor="var(--accent-purple)"
                line={fortranCursor.line}
                column={fortranCursor.col}
                totalLines={fortranCode.split('\n').length}
              />
            </div>
          </div>
        </div>

        {/* ── Results ── */}
        {result && (
          <>
            {/* IR Summary */}
            <div className="page-section">
              <div className="section-title">Structural Comparison</div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
                {[
                  {
                    label: 'Structural Score',
                    value: `${Math.round(result.ir_summary.structural_score * 100)}%`,
                    color: result.ir_summary.structural_score > 0.7 ? 'var(--accent-green)' : 'var(--accent-yellow)',
                  },
                  { label: 'Matched Pairs',   value: result.ir_summary.matched_functions.length, color: 'var(--accent-blue)' },
                  { label: 'C Only',          value: result.ir_summary.c_only_functions.length, color: 'var(--accent-yellow)' },
                  { label: 'Fortran Only',    value: result.ir_summary.fortran_only_functions.length, color: 'var(--accent-purple)' },
                ].map((m) => (
                  <div key={m.label} className="card" style={{ textAlign: 'center', padding: '14px 12px' }}>
                    <div style={{ fontSize: 22, fontWeight: 700, color: m.color, fontVariantNumeric: 'tabular-nums' }}>
                      {m.value}
                    </div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginTop: 4 }}>
                      {m.label}
                    </div>
                  </div>
                ))}
              </div>
              {result.ir_summary.notes.length > 0 && (
                <div className="alert alert-info" style={{ marginTop: 12 }}>
                  <Info size={14} />
                  <div>{result.ir_summary.notes.join(' ')}</div>
                </div>
              )}
            </div>

            {/* Function Analysis */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }} className="page-section">
              {[
                { title: 'C Functions',   fns: result.c_analysis.functions,       color: 'var(--accent-blue)',   lang: 'C' },
                { title: 'Fortran Units', fns: result.fortran_analysis.functions, color: 'var(--accent-purple)', lang: 'Fortran' },
              ].map(({ title, fns, color, lang }) => (
                <div key={lang}>
                  <div className="section-title">{title} ({fns.length})</div>
                  <div className="card" style={{ padding: 0 }}>
                    {fns.length === 0 ? (
                      <div style={{ padding: 16, color: 'var(--text-muted)', fontSize: 13 }}>No units detected</div>
                    ) : (
                      <table className="data-table">
                        <thead>
                          <tr>
                            <th>Name</th><th>Params</th><th>LOC</th><th>CC</th><th>Flags</th>
                          </tr>
                        </thead>
                        <tbody>
                          {fns.map((f: any) => (
                            <tr key={f.name}>
                              <td style={{ fontFamily: 'var(--font-mono)', color, fontSize: 12 }}>{f.name}</td>
                              <td>{f.parameters.length}</td>
                              <td>{f.loc}</td>
                              <td>{f.cyclomatic_complexity}</td>
                              <td style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                                {f.has_loops && <span className="badge badge-info" style={{ fontSize: 9 }}>LOOP</span>}
                                {f.has_conditionals && <span className="badge badge-warning" style={{ fontSize: 9 }}>IF</span>}
                                {f.has_io && <span className="badge badge-neutral" style={{ fontSize: 9 }}>I/O</span>}
                                {f.has_implicit_none && <span className="badge badge-success" style={{ fontSize: 9 }}>IMPL.NONE</span>}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* Gap Detection */}
            {result.gaps.length > 0 && (
              <div className="page-section">
                <div className="section-title">Detected Gaps ({result.gaps.length})</div>
                <div className="card" style={{ padding: 0 }}>
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>ID</th><th>Category</th><th>Severity</th>
                        <th>Location</th><th>Confidence</th><th></th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.gaps.map((g) => (
                        <GapRow key={g.id} gap={g} onJumpToCode={handleJumpToCode} />
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};
