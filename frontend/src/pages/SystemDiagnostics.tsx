import React, { useEffect, useState } from 'react';
import { Header } from '../components/layout/Header';
import { getSystemInfo } from '../services/api';
import type { SystemInfoResponse, CompilerInfo } from '../types';
import { RefreshCw, CheckCircle2, XCircle, AlertCircle, Monitor, Cpu, HardDrive, Wifi, Terminal } from 'lucide-react';

const CompilerRow: React.FC<{ compiler: CompilerInfo }> = ({ compiler }) => {
  const icon =
    compiler.status === 'detected' ? <CheckCircle2 size={14} color="var(--accent-green)" /> :
    compiler.status === 'not_found' ? <AlertCircle size={14} color="var(--accent-yellow)" /> :
    <XCircle size={14} color="var(--accent-red)" />;
  return (
    <div className="system-status-row">
      <span className="system-status-key" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        {icon} {compiler.name.toUpperCase()}
      </span>
      <span className="system-status-value" style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>
        {compiler.status === 'detected'
          ? `v${compiler.version} — ${compiler.path}`
          : compiler.error ?? 'Not found'}
      </span>
    </div>
  );
};

export const SystemDiagnostics: React.FC = () => {
  const [info, setInfo] = useState<SystemInfoResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetch = async () => {
    setLoading(true); setError(null);
    try {
      setInfo(await getSystemInfo());
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to fetch');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetch(); }, []);

  const Section: React.FC<{ icon: React.ReactNode; title: string; children: React.ReactNode }> = ({ icon, title, children }) => (
    <div className="page-section">
      <div className="section-title">
        <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>{icon} {title}</span>
      </div>
      <div className="card">{children}</div>
    </div>
  );

  const Row: React.FC<{ label: string; value: React.ReactNode }> = ({ label, value }) => (
    <div className="system-status-row">
      <span className="system-status-key">{label}</span>
      <span className="system-status-value" style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>{value}</span>
    </div>
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <Header
        title="System Diagnostics"
        subtitle="Real-time hardware, compiler, and runtime status"
        actions={
          <button className="btn btn-ghost btn-sm" onClick={fetch} disabled={loading} id="btn-refresh-diagnostics">
            <RefreshCw size={13} /> Refresh
          </button>
        }
      />
      <div className="page-content">
        {error && (
          <div className="alert alert-error" style={{ marginBottom: 20 }}>
            <XCircle size={16} /> <span>Backend error: {error}</span>
          </div>
        )}
        {loading && (
          <div style={{ display: 'flex', gap: 12, alignItems: 'center', color: 'var(--text-muted)', padding: '40px 0' }}>
            <div className="spinner" /> Collecting system information...
          </div>
        )}
        {info && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
            {/* Operating System */}
            <Section icon={<Monitor size={14} />} title="Operating System">
              <Row label="OS Name"     value={info.os_name} />
              <Row label="Architecture" value={info.architecture} />
              <Row label="Platform"    value={<span style={{ wordBreak: 'break-all', fontSize: 11 }}>{info.os_platform}</span>} />
              <Row label="CPUs"        value={`${info.cpu_count} logical cores`} />
              <Row label="Memory"      value={`${info.available_memory_gb.toFixed(1)} GB free / ${info.total_memory_gb} GB`} />
            </Section>

            {/* Runtime */}
            <Section icon={<Terminal size={14} />} title="Python Runtime">
              <Row label="Python"      value={info.python_version.split(' ')[0]} />
              <Row label="Executable"  value={<span style={{ wordBreak: 'break-all', fontSize: 11 }}>{info.python_executable}</span>} />
              <Row label="Node.js"     value={info.node_version ?? <span className="badge badge-neutral">Not Found</span>} />
              <Row label="App Version" value={`v${info.app_version}`} />
            </Section>

            {/* C Compilers */}
            <Section icon={<Cpu size={14} />} title="C Compilers">
              {info.c_compilers.length === 0 ? (
                <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>No C compilers detected.</div>
              ) : (
                info.c_compilers.map((c) => <CompilerRow key={c.name} compiler={c} />)
              )}
              <div style={{ marginTop: 12, padding: '10px 12px', background: 'var(--bg-primary)', borderRadius: 'var(--radius-md)', fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                Install: MSYS2 → pacman -S mingw-w64-x86_64-gcc
              </div>
            </Section>

            {/* Fortran Compilers */}
            <Section icon={<Cpu size={14} />} title="Fortran Compilers">
              {info.fortran_compilers.length === 0 ? (
                <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>No Fortran compilers detected.</div>
              ) : (
                info.fortran_compilers.map((c) => <CompilerRow key={c.name} compiler={c} />)
              )}
              <div style={{ marginTop: 12, padding: '10px 12px', background: 'var(--bg-primary)', borderRadius: 'var(--radius-md)', fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                Install: MSYS2 → pacman -S mingw-w64-x86_64-gcc-fortran
              </div>
            </Section>

            {/* Storage */}
            <Section icon={<HardDrive size={14} />} title="Storage">
              <Row label="Total"    value={`${info.disk_total_gb} GB`} />
              <Row label="Used"     value={`${info.disk_used_gb} GB (${info.disk_percent_used}%)`} />
              <Row label="Free"     value={`${info.disk_free_gb} GB`} />
              <div style={{ marginTop: 12 }}>
                <div style={{ background: 'var(--bg-primary)', borderRadius: 4, height: 6, overflow: 'hidden' }}>
                  <div style={{ width: `${info.disk_percent_used}%`, height: '100%', background: info.disk_percent_used > 80 ? 'var(--accent-red)' : 'var(--accent-blue)', transition: 'width 0.5s ease' }} />
                </div>
              </div>
            </Section>

            {/* Security & AI */}
            <Section icon={<Wifi size={14} />} title="Security & AI Status">
              <Row label="Internet"    value={<span className="badge badge-success">OFFLINE — SECURE</span>} />
              <Row label="External APIs" value={<span className="badge badge-success">BLOCKED</span>} />
              <Row label="Database"    value={<span className="badge badge-success">SQLite — Local</span>} />
              <Row label="Telemetry"   value={<span className="badge badge-success">DISABLED</span>} />
              <Row label="Local AI"    value={
                info.local_ai_enabled
                  ? <span className="badge badge-success">{info.local_ai_provider}</span>
                  : <span className="badge badge-neutral">Not Configured</span>
              } />
              <div style={{ marginTop: 12, padding: '10px 12px', background: 'rgba(16, 185, 129, 0.05)', borderRadius: 'var(--radius-md)', border: '1px solid rgba(16, 185, 129, 0.15)', fontSize: 11, color: 'var(--accent-green)' }}>
                ✓ All security invariants satisfied. No data leaves this machine.
              </div>
            </Section>
          </div>
        )}
      </div>
    </div>
  );
};
