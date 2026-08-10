import React, { useEffect, useState } from 'react';
import { listProjects, createProject } from '../../services/api';
import { useAppStore } from '../../services/store';
import { Plus, X, FolderKanban } from 'lucide-react';

interface Project {
  id: string;
  name: string;
  description: string;
}

interface ProjectModalProps {
  onClose: () => void;
}

export const ProjectModal: React.FC<ProjectModalProps> = ({ onClose }) => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');

  const { activeProject, setActiveProject } = useAppStore();

  const fetchProjects = async () => {
    try {
      const data = await listProjects();
      setProjects(data);
    } catch (err) {
      console.error('Error listing projects:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim()) return;
    try {
      const created = await createProject(newName, newDesc);
      const newProj = { id: created.id, name: created.name, description: newDesc };
      setProjects([newProj, ...projects]);
      setActiveProject(newProj);
      setShowCreate(false);
      setNewName('');
      setNewDesc('');
    } catch (err) {
      console.error('Error creating project:', err);
    }
  };

  return (
    <div className="modal-backdrop" style={{
      position: 'fixed',
      top: 0,
      left: 0,
      width: '100%',
      height: '100%',
      backgroundColor: 'rgba(0,0,0,0.7)',
      backdropFilter: 'blur(4px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000
    }}>
      <div className="card" style={{
        width: '500px',
        maxWidth: '90%',
        maxHeight: '85vh',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
        border: '1px solid var(--border-normal)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <FolderKanban size={18} className="text-secondary" />
            <h3 style={{ margin: 0, fontSize: 16 }}>Switch Project</h3>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
            <X size={18} />
          </button>
        </div>

        {showCreate ? (
          <form onSubmit={handleCreate} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div>
              <label style={{ fontSize: 12, color: 'var(--text-secondary)', display: 'block', marginBottom: 6 }}>Project Name</label>
              <input
                type="text"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                style={{
                  background: 'var(--bg-primary)',
                  border: '1px solid var(--border-normal)',
                  borderRadius: 'var(--radius-md)',
                  color: 'var(--text-primary)',
                  padding: '8px 12px',
                  width: '100%',
                  outline: 'none'
                }}
                placeholder="e.g. Guidance System"
                autoFocus
              />
            </div>
            <div>
              <label style={{ fontSize: 12, color: 'var(--text-secondary)', display: 'block', marginBottom: 6 }}>Description (Optional)</label>
              <textarea
                value={newDesc}
                onChange={(e) => setNewDesc(e.target.value)}
                style={{
                  background: 'var(--bg-primary)',
                  border: '1px solid var(--border-normal)',
                  borderRadius: 'var(--radius-md)',
                  color: 'var(--text-primary)',
                  padding: '8px 12px',
                  width: '100%',
                  outline: 'none',
                  minHeight: '80px',
                  resize: 'vertical'
                }}
                placeholder="Enter project details..."
              />
            </div>
            <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end', marginTop: 8 }}>
              <button type="button" className="btn btn-secondary" onClick={() => setShowCreate(false)}>Cancel</button>
              <button type="submit" className="btn btn-primary">Create Project</button>
            </div>
          </form>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12, flex: 1, overflowY: 'auto' }}>
            <button className="btn btn-secondary" style={{ width: '100%', justifyContent: 'center', gap: 8 }} onClick={() => setShowCreate(true)}>
              <Plus size={14} /> Create New Project
            </button>

            {loading ? (
              <div style={{ textAlign: 'center', padding: 20 }}>Loading projects...</div>
            ) : projects.length === 0 ? (
              <div style={{ textAlign: 'center', padding: 20, color: 'var(--text-muted)' }}>No projects found. Create one to get started.</div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8, maxHeight: '300px', overflowY: 'auto', marginTop: 8 }}>
                {projects.map((p) => {
                  const isActive = activeProject?.id === p.id;
                  return (
                    <div
                      key={p.id}
                      onClick={() => {
                        setActiveProject(p);
                        onClose();
                      }}
                      style={{
                        padding: '10px 14px',
                        borderRadius: 'var(--radius-md)',
                        border: `1px solid ${isActive ? 'var(--accent-secondary)' : 'var(--border-normal)'}`,
                        background: isActive ? 'var(--bg-card)' : 'var(--bg-primary)',
                        cursor: 'pointer',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: 4,
                        transition: 'border-color 0.2s'
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontWeight: 'bold', fontSize: 13, color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)' }}>{p.name}</span>
                        {isActive && <span className="status-badge badge-success">Active</span>}
                      </div>
                      {p.description && <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{p.description}</span>}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
