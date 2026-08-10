import React, { useEffect, useState } from 'react';
import { Header } from '../components/layout/Header';
import { History as HistoryIcon, ArrowRight, Trash2 } from 'lucide-react';
import { api } from '../services/api';
import { Link } from 'react-router-dom';

interface SessionItem {
  id: string;
  status: string;
  c_filename: string;
  fortran_filename: string;
  c_functions_found: number;
  fortran_functions_found: number;
  gaps_detected: number;
  high_severity_gaps: number;
  created_at: string;
}

export const History: React.FC = () => {
  const [sessions, setSessions] = useState<SessionItem[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchHistory = async () => {
    try {
      const res = await api.get('/analysis/');
      setSessions(res.data);
    } catch (err) {
      console.error('Error fetching history:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this session?')) return;
    try {
      await api.delete(`/analysis/${id}`);
      fetchHistory();
    } catch (err) {
      console.error('Failed to delete session:', err);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <Header title="Analysis History" subtitle="Browse and inspect past analysis sessions" />
      <div className="page-content">
        <div className="page-section">
          <div className="section-title">Past Sessions</div>
          {loading ? (
            <div>Loading history...</div>
          ) : sessions.length === 0 ? (
            <div className="card" style={{ textAlign: 'center', padding: '40px 20px' }}>
              <HistoryIcon size={48} style={{ opacity: 0.2, marginBottom: 12 }} />
              <p style={{ color: 'var(--text-secondary)' }}>No past analysis sessions found.</p>
            </div>
          ) : (
            <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
              <table className="analysis-table">
                <thead>
                  <tr>
                    <th>C File</th>
                    <th>Fortran File</th>
                    <th>Gaps</th>
                    <th>High Severity</th>
                    <th>Created At</th>
                    <th style={{ width: 100 }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {sessions.map((s) => (
                    <tr key={s.id}>
                      <td style={{ fontFamily: 'var(--font-mono)' }}>{s.c_filename || 'N/A'}</td>
                      <td style={{ fontFamily: 'var(--font-mono)' }}>{s.fortran_filename || 'N/A'}</td>
                      <td>
                        <span className={`status-badge ${s.gaps_detected > 0 ? 'badge-error' : 'badge-success'}`}>
                          {s.gaps_detected} gaps
                        </span>
                      </td>
                      <td>
                        <span className={`status-badge ${s.high_severity_gaps > 0 ? 'badge-error' : 'badge-neutral'}`}>
                          {s.high_severity_gaps} high
                        </span>
                      </td>
                      <td style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                        {new Date(s.created_at).toLocaleString()}
                      </td>
                      <td>
                        <div style={{ display: 'flex', gap: 8 }}>
                          <Link to={`/analysis?session_id=${s.id}`} className="btn btn-secondary" style={{ padding: '4px 8px' }}>
                            <ArrowRight size={14} />
                          </Link>
                          <button onClick={() => handleDelete(s.id)} className="btn btn-secondary" style={{ padding: '4px 8px', color: 'var(--status-error)' }}>
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
