import React, { useEffect, useState } from 'react';
import { Header } from '../components/layout/Header';
import { StatusCard } from '../components/ui/StatusCard';
import { CompilerStatusCard } from '../components/ui/CompilerStatus';
import { getStatus, getSystemInfo, listAnalyses } from '../services/api';
import type { SystemStatusResponse, SystemInfoResponse, AnalysisSummary } from '../types';
import {
  Code2,
  GitCompareArrows,
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
} from 'lucide-react';

export const Dashboard: React.FC = () => {
  const [status, setStatus] = useState<SystemStatusResponse | null>(null);
  const [sysInfo, setSysInfo] = useState<SystemInfoResponse | null>(null);
  const [analyses, setAnalyses] = useState<AnalysisSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [statusData, sysData, analysesData] = await Promise.all([
        getStatus(),
        getSystemInfo(),
        listAnalyses(),
      ]);
      setStatus(statusData);
      setSysInfo(sysData);
      setAnalyses(analysesData);
      setLastRefresh(new Date());
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to connect to backend';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const totalGaps = analyses.reduce((s, a) => s + (a.gaps_detected ?? 0), 0);
  const highSeverityGaps = analyses.reduce((s, a) => s + (a.high_severity_gaps ?? 0), 0);
  const completedAnalyses = analyses.filter((a) => a.status === 'completed').length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <Header
        title="Dashboard"
        subtitle="RCI Code Equivalence Platform — Offline Mode"
        actions={
          <button
            className="btn btn-ghost btn-sm"
            onClick={fetchData}
            disabled={loading}
            id="btn-refresh-dashboard"
          >
            <RefreshCw size={13} className={loading ? 'spinning' : ''} />
            Refresh
          </button>
        }
      />

      <div className="page-content">
        {error && (
          <div className="alert alert-error" style={{ marginBottom: 20 }}>
            <AlertTriangle size={16} />
            <div>
              <strong>Backend connection error:</strong> {error}
              <div style={{ marginTop: 4, fontSize: 12 }}>
                Make sure the backend is running: <code style={{ fontFamily: 'var(--font-mono)' }}>uvicorn app.main:app --reload</code>
              </div>
            </div>
          </div>
        )}

        {/* ── Compiler Status ── */}
        <div className="page-section">
          <div className="section-title">Compiler Status</div>
          <div className="compiler-status-grid">
            <CompilerStatusCard
              language="C"
              compilers={sysInfo?.c_compilers ?? []}
              loading={loading}
            />
            <CompilerStatusCard
              language="Fortran"
              compilers={sysInfo?.fortran_compilers ?? []}
              loading={loading}
            />
          </div>
        </div>

        {/* ── Platform Metrics ── */}
        <div className="page-section">
          <div className="section-title">Platform Metrics</div>
          <div className="stats-grid">
            <StatusCard
              label="Analysis Sessions"
              value={loading ? '—' : analyses.length}
              subLabel="Total uploaded"
              icon={<Code2 size={16} />}
              accentColor="var(--accent-blue)"
            />
            <StatusCard
              label="Completed"
              value={loading ? '—' : completedAnalyses}
              subLabel="Successfully analyzed"
              icon={<CheckCircle2 size={16} />}
              accentColor="var(--accent-green)"
              valueColor={completedAnalyses > 0 ? 'var(--accent-green)' : undefined}
            />
            <StatusCard
              label="Detected Gaps"
              value={loading ? '—' : totalGaps}
              subLabel="Across all sessions"
              icon={<GitCompareArrows size={16} />}
              accentColor="var(--accent-yellow)"
            />
            <StatusCard
              label="High Severity Gaps"
              value={loading ? '—' : highSeverityGaps}
              subLabel="Require immediate review"
              icon={<AlertTriangle size={16} />}
              accentColor="var(--accent-red)"
              valueColor={highSeverityGaps > 0 ? 'var(--accent-red)' : undefined}
            />
          </div>
        </div>

        {/* ── System + Recent Analyses ── */}
        <div className="dashboard-grid">
          {/* System Status */}
          <div className="page-section">
            <div className="section-title">System Status</div>
            <div className="card">
              {loading ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: 'var(--text-muted)', padding: '8px 0' }}>
                  <div className="spinner" />
                  Loading system information...
                </div>
              ) : status ? (
                <>
                  <div className="system-status-row">
                    <span className="system-status-key">Application Status</span>
                    <span className="badge badge-success">{status.status}</span>
                  </div>
                  <div className="system-status-row">
                    <span className="system-status-key">Version</span>
                    <span className="system-status-value">{status.version}</span>
                  </div>
                  <div className="system-status-row">
                    <span className="system-status-key">Environment</span>
                    <span className="system-status-value">{status.environment}</span>
                  </div>
                  <div className="system-status-row">
                    <span className="system-status-key">Uptime</span>
                    <span className="system-status-value">{Math.round(status.uptime_seconds)}s</span>
                  </div>
                  <div className="system-status-row">
                    <span className="system-status-key">Internet</span>
                    <span className="badge badge-success">OFFLINE — SECURE</span>
                  </div>
                  <div className="system-status-row">
                    <span className="system-status-key">Local AI</span>
                    <span className="badge badge-neutral">
                      {status.local_ai_enabled ? 'Enabled' : 'Not Configured'}
                    </span>
                  </div>
                  <div className="system-status-row">
                    <span className="system-status-key">Database</span>
                    <span className="badge badge-success">SQLite — Connected</span>
                  </div>
                  {sysInfo && (
                    <>
                      <div className="system-status-row">
                        <span className="system-status-key">OS</span>
                        <span className="system-status-value">{sysInfo.os_name}</span>
                      </div>
                      <div className="system-status-row">
                        <span className="system-status-key">Memory</span>
                        <span className="system-status-value">
                          {sysInfo.available_memory_gb.toFixed(1)} GB free / {sysInfo.total_memory_gb} GB total
                        </span>
                      </div>
                      <div className="system-status-row">
                        <span className="system-status-key">Disk</span>
                        <span className="system-status-value">
                          {sysInfo.disk_free_gb.toFixed(1)} GB free ({sysInfo.disk_percent_used}% used)
                        </span>
                      </div>
                    </>
                  )}
                  <div style={{ marginTop: 12, fontSize: 11, color: 'var(--text-muted)' }}>
                    Last refresh: {lastRefresh.toLocaleTimeString()}
                  </div>
                </>
              ) : (
                <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>
                  Backend not reachable. Start the FastAPI server to see system status.
                </div>
              )}
            </div>
          </div>

          {/* Recent Analyses */}
          <div className="page-section">
            <div className="section-title">Recent Analyses</div>
            <div className="card" style={{ padding: 0 }}>
              {loading ? (
                <div style={{ padding: 20, color: 'var(--text-muted)', display: 'flex', gap: 10, alignItems: 'center' }}>
                  <div className="spinner" /> Loading...
                </div>
              ) : analyses.length === 0 ? (
                <div style={{ padding: 24, textAlign: 'center', color: 'var(--text-muted)' }}>
                  <Code2 size={32} style={{ margin: '0 auto 12px', display: 'block', opacity: 0.3 }} />
                  <div style={{ fontSize: 13 }}>No analyses yet</div>
                  <div style={{ fontSize: 12, marginTop: 4 }}>
                    Upload C and Fortran files in <strong>Code Analysis</strong> to begin.
                  </div>
                </div>
              ) : (
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Files</th>
                      <th>Gaps</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {analyses.slice(0, 8).map((a) => (
                      <tr key={a.session_id}>
                        <td>
                          <div style={{ fontSize: 12, fontFamily: 'var(--font-mono)', color: 'var(--text-code)' }}>
                            {a.c_filename ?? '—'}
                          </div>
                          <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                            {a.fortran_filename ?? '—'}
                          </div>
                        </td>
                        <td>
                          {a.gaps_detected != null ? (
                            <span style={{ color: a.high_severity_gaps ? 'var(--accent-red)' : 'var(--text-primary)' }}>
                              {a.gaps_detected}
                              {a.high_severity_gaps ? ` (${a.high_severity_gaps} high)` : ''}
                            </span>
                          ) : '—'}
                        </td>
                        <td>
                          <span className={`badge ${a.status === 'completed' ? 'badge-success' : a.status === 'failed' ? 'badge-error' : 'badge-warning'}`}>
                            {a.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </div>

        {/* ── Pipeline Status ── */}
        <div className="page-section">
          <div className="section-title">Analysis Pipeline Status</div>
          <div className="card">
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: 10 }}>
              {[
                { label: 'Source Input', done: true },
                { label: 'Source Validation', done: true },
                { label: 'C Parsing', done: true },
                { label: 'Fortran Parsing', done: true },
                { label: 'IR Generation', done: true },
                { label: 'Comparison', done: true },
                { label: 'Gap Detection', done: true },
                { label: 'Patch Generation', phase: 7 },
                { label: 'Compilation', phase: 8 },
                { label: 'Execution', phase: 8 },
                { label: 'Output Comparison', phase: 10 },
                { label: 'Visualization', phase: 11 },
                { label: 'Reports', phase: 12 },
              ].map((item) => (
                <div
                  key={item.label}
                  style={{
                    padding: '8px 12px',
                    borderRadius: 'var(--radius-md)',
                    background: item.done
                      ? 'rgba(16, 185, 129, 0.08)'
                      : 'rgba(255,255,255,0.02)',
                    border: `1px solid ${item.done ? 'rgba(16, 185, 129, 0.2)' : 'var(--border-subtle)'}`,
                    fontSize: 11,
                    color: item.done ? 'var(--accent-green)' : 'var(--text-muted)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                  }}
                >
                  {item.done ? '✓' : `P${item.phase}`} {item.label}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
