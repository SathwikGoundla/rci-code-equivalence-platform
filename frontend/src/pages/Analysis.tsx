import React, { useState, useRef, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Header } from '../components/layout/Header';
import { uploadAndAnalyze, getAnalysis } from '../services/api';
import { useAppStore } from '../services/store';
import type { AnalysisResult, GapReport } from '../types';
import {
  Upload,
  Code2,
  FileCode,
  AlertTriangle,
  ChevronDown,
  ChevronRight,
  Info,
  ChevronsLeftRight,
} from 'lucide-react';
import Editor from '@monaco-editor/react';

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

  // Parse location for line numbers (e.g. "projectile.c:45" or "projectile.f90:12-15")
  const parseLineNumber = (locStr: string): number | null => {
    const parts = locStr.split(':');
    if (parts.length < 2) return null;
    const linePart = parts[1].split('-')[0];
    const lineNum = parseInt(linePart, 10);
    return isNaN(lineNum) ? null : lineNum;
  };

  const handleLineClick = (lang: 'c' | 'fortran', locationStr: string) => {
    const line = parseLineNumber(locationStr);
    if (line !== null && onJumpToCode) {
      onJumpToCode(lang, line);
    }
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
        <td>
          <SeverityBadge severity={gap.severity} />
        </td>
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
                <div
                  style={{
                    fontSize: 11,
                    color: 'var(--text-muted)',
                    textTransform: 'uppercase',
                    letterSpacing: '0.08em',
                    marginBottom: 4,
                  }}
                >
                  Explanation
                </div>
                <div style={{ fontSize: 13, color: 'var(--text-primary)' }}>{gap.explanation}</div>
              </div>
              <div style={{ marginBottom: 12 }}>
                <div
                  style={{
                    fontSize: 11,
                    color: 'var(--text-muted)',
                    textTransform: 'uppercase',
                    letterSpacing: '0.08em',
                    marginBottom: 4,
                  }}
                >
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
                        // Deduce language from gap ID/category/location
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
                <div
                  style={{
                    fontSize: 11,
                    color: 'var(--text-muted)',
                    textTransform: 'uppercase',
                    letterSpacing: '0.08em',
                    marginBottom: 4,
                  }}
                >
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

export const Analysis: React.FC = () => {
  const [searchParams] = useSearchParams();
  const sessionId = searchParams.get('session_id');

  const { activeProject } = useAppStore();

  const [cFile, setCFile] = useState<File | null>(null);
  const [fortranFile, setFortranFile] = useState<File | null>(null);

  const [cCode, setCCode] = useState<string>('// Upload C code to view');
  const [fortranCode, setFortranCode] = useState<string>('! Upload Fortran code to view');

  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const cInputRef = useRef<HTMLInputElement>(null);
  const fInputRef = useRef<HTMLInputElement>(null);

  const cEditorRef = useRef<any>(null);
  const fortranEditorRef = useRef<any>(null);

  // Load session from history query param if present
  useEffect(() => {
    if (sessionId) {
      const loadHistorySession = async () => {
        setLoading(true);
        setError(null);
        try {
          const data = await getAnalysis(sessionId);
          setResult(data);
          // Set placeholders for code view (since source code is in-memory only and not saved in DB metadata)
          setCCode('// History mode: source code not stored in offline DB.\n// Re-upload C and Fortran files to inspect code side-by-side.');
          setFortranCode('! History mode: source code not stored in offline DB.\n! Re-upload C and Fortran files to inspect code side-by-side.');
        } catch (e: any) {
          setError('Failed to load past session details.');
        } finally {
          setLoading(false);
        }
      };
      loadHistorySession();
    }
  }, [sessionId]);

  // Read files to populate editor preview on select
  useEffect(() => {
    if (cFile) {
      const reader = new FileReader();
      reader.onload = (e) => setCCode(e.target?.result as string);
      reader.readAsText(cFile);
    }
  }, [cFile]);

  useEffect(() => {
    if (fortranFile) {
      const reader = new FileReader();
      reader.onload = (e) => setFortranCode(e.target?.result as string);
      reader.readAsText(fortranFile);
    }
  }, [fortranFile]);

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

  const handleJumpToCode = (lang: 'c' | 'fortran', line: number) => {
    const editor = lang === 'c' ? cEditorRef.current : fortranEditorRef.current;
    if (editor) {
      editor.revealLineInCenter(line);
      editor.setPosition({ lineNumber: line, column: 1 });
      editor.focus();
    }
  };

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
            {/* C File */}
            <div
              className="card"
              style={{ cursor: 'pointer', border: cFile ? '1px solid var(--accent-blue)' : undefined }}
              onClick={() => cInputRef.current?.click()}
            >
              <input
                ref={cInputRef}
                type="file"
                accept=".c,.h"
                style={{ display: 'none' }}
                id="input-c-file"
                onChange={(e) => setCFile(e.target.files?.[0] ?? null)}
              />
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <div
                  style={{
                    width: 40,
                    height: 40,
                    borderRadius: 'var(--radius-md)',
                    background: 'rgba(61,122,245,0.1)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'var(--accent-blue)',
                  }}
                >
                  <Code2 size={20} />
                </div>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>C Source File</div>
                  <div
                    style={{
                      fontSize: 12,
                      color: 'var(--text-muted)',
                      marginTop: 2,
                      fontFamily: 'var(--font-mono)',
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      maxWidth: '220px',
                    }}
                  >
                    {cFile ? cFile.name : 'Click to upload .c file'}
                  </div>
                  {cFile && (
                    <div style={{ fontSize: 11, color: 'var(--accent-green)', marginTop: 2 }}>
                      ✓ {(cFile.size / 1024).toFixed(1)} KB
                    </div>
                  )}
                </div>
              </div>
            </div>
            {/* Fortran File */}
            <div
              className="card"
              style={{ cursor: 'pointer', border: fortranFile ? '1px solid var(--accent-purple)' : undefined }}
              onClick={() => fInputRef.current?.click()}
            >
              <input
                ref={fInputRef}
                type="file"
                accept=".f90,.f,.f95,.f03,.for"
                style={{ display: 'none' }}
                id="input-fortran-file"
                onChange={(e) => setFortranFile(e.target.files?.[0] ?? null)}
              />
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <div
                  style={{
                    width: 40,
                    height: 40,
                    borderRadius: 'var(--radius-md)',
                    background: 'rgba(139,92,246,0.1)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'var(--accent-purple)',
                  }}
                >
                  <FileCode size={20} />
                </div>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>
                    Fortran Source File
                  </div>
                  <div
                    style={{
                      fontSize: 12,
                      color: 'var(--text-muted)',
                      marginTop: 2,
                      fontFamily: 'var(--font-mono)',
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      maxWidth: '220px',
                    }}
                  >
                    {fortranFile ? fortranFile.name : 'Click to upload .f90 / .f file'}
                  </div>
                  {fortranFile && (
                    <div style={{ fontSize: 11, color: 'var(--accent-green)', marginTop: 2 }}>
                      ✓ {(fortranFile.size / 1024).toFixed(1)} KB
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          <button
            id="btn-analyze"
            className="btn btn-primary"
            onClick={handleAnalyze}
            disabled={!cFile || !fortranFile || loading}
          >
            {loading ? (
              <>
                <div className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} /> Analyzing...
              </>
            ) : (
              <>
                <Upload size={14} /> Analyze Both Files
              </>
            )}
          </button>
        </div>

        {error && (
          <div className="alert alert-error" style={{ marginBottom: 20 }}>
            <AlertTriangle size={16} />
            {error}
          </div>
        )}

        {/* ── Side-by-Side Monaco Editor Preview ── */}
        <div className="page-section">
          <div className="section-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <ChevronsLeftRight size={16} /> Code Comparison View
          </div>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: 16,
              height: '350px',
              background: 'var(--bg-card)',
              border: '1px solid var(--border-normal)',
              borderRadius: 'var(--radius-md)',
              padding: 12,
            }}
          >
            <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
              <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginBottom: 6, fontWeight: 600 }}>
                C EDITOR
              </div>
              <div style={{ flex: 1, borderRadius: 'var(--radius-sm)', overflow: 'hidden' }}>
                <Editor
                  height="100%"
                  language="c"
                  theme="vs-dark"
                  value={cCode}
                  options={{
                    readOnly: true,
                    minimap: { enabled: false },
                    fontSize: 12,
                    lineNumbersMinChars: 3,
                  }}
                  onMount={(editor) => (cEditorRef.current = editor)}
                />
              </div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
              <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginBottom: 6, fontWeight: 600 }}>
                FORTRAN EDITOR
              </div>
              <div style={{ flex: 1, borderRadius: 'var(--radius-sm)', overflow: 'hidden' }}>
                <Editor
                  height="100%"
                  language="fortran"
                  theme="vs-dark"
                  value={fortranCode}
                  options={{
                    readOnly: true,
                    minimap: { enabled: false },
                    fontSize: 12,
                    lineNumbersMinChars: 3,
                  }}
                  onMount={(editor) => (fortranEditorRef.current = editor)}
                />
              </div>
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
                    color:
                      result.ir_summary.structural_score > 0.7
                        ? 'var(--accent-green)'
                        : 'var(--accent-yellow)',
                  },
                  {
                    label: 'Matched Pairs',
                    value: result.ir_summary.matched_functions.length,
                    color: 'var(--accent-blue)',
                  },
                  { label: 'C Only', value: result.ir_summary.c_only_functions.length, color: 'var(--accent-yellow)' },
                  {
                    label: 'Fortran Only',
                    value: result.ir_summary.fortran_only_functions.length,
                    color: 'var(--accent-purple)',
                  },
                ].map((m) => (
                  <div key={m.label} className="card" style={{ textAlign: 'center', padding: '14px 12px' }}>
                    <div
                      style={{
                        fontSize: 22,
                        fontWeight: 700,
                        color: m.color,
                        fontVariantNumeric: 'tabular-nums',
                      }}
                    >
                      {m.value}
                    </div>
                    <div
                      style={{
                        fontSize: 11,
                        color: 'var(--text-muted)',
                        textTransform: 'uppercase',
                        letterSpacing: '0.08em',
                        marginTop: 4,
                      }}
                    >
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
                { title: 'C Functions', fns: result.c_analysis.functions, color: 'var(--accent-blue)', lang: 'C' },
                {
                  title: 'Fortran Units',
                  fns: result.fortran_analysis.functions,
                  color: 'var(--accent-purple)',
                  lang: 'Fortran',
                },
              ].map(({ title, fns, color, lang }) => (
                <div key={lang}>
                  <div className="section-title">
                    {title} ({fns.length})
                  </div>
                  <div className="card" style={{ padding: 0 }}>
                    {fns.length === 0 ? (
                      <div style={{ padding: 16, color: 'var(--text-muted)', fontSize: 13 }}>No units detected</div>
                    ) : (
                      <table className="data-table">
                        <thead>
                          <tr>
                            <th>Name</th>
                            <th>Params</th>
                            <th>LOC</th>
                            <th>CC</th>
                            <th>Flags</th>
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
                                {f.has_loops && (
                                  <span className="badge badge-info" style={{ fontSize: 9 }}>
                                    LOOP
                                  </span>
                                )}
                                {f.has_conditionals && (
                                  <span className="badge badge-warning" style={{ fontSize: 9 }}>
                                    IF
                                  </span>
                                )}
                                {f.has_io && (
                                  <span className="badge badge-neutral" style={{ fontSize: 9 }}>
                                    I/O
                                  </span>
                                )}
                                {f.has_implicit_none && (
                                  <span className="badge badge-success" style={{ fontSize: 9 }}>
                                    IMPL.NONE
                                  </span>
                                )}
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
                        <th>ID</th>
                        <th>Category</th>
                        <th>Severity</th>
                        <th>Location</th>
                        <th>Confidence</th>
                        <th></th>
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
