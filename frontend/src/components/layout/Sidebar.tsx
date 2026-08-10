import React, { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Code2,
  GitCompareArrows,
  FlaskConical,
  BarChart3,
  FileText,
  Settings,
  Activity,
  FolderKanban,
  ChevronDown,
} from 'lucide-react';
import { useAppStore } from '../../services/store';
import { ProjectModal } from '../ui/ProjectModal';
import { listProjects } from '../../services/api';

interface NavItem {
  to: string;
  icon: React.ReactNode;
  label: string;
}

const navItems: NavItem[] = [
  { to: '/',              icon: <LayoutDashboard size={16} />, label: 'Dashboard' },
  { to: '/analysis',      icon: <Code2 size={16} />,           label: 'Code Analysis' },
  { to: '/history',       icon: <Activity size={16} />,        label: 'Analysis History' },
  { to: '/gaps',          icon: <GitCompareArrows size={16} />, label: 'Gap Detection' },
  { to: '/tests',         icon: <FlaskConical size={16} />,    label: 'Test Execution' },
  { to: '/visualization', icon: <BarChart3 size={16} />,       label: 'Visualization' },
  { to: '/reports',       icon: <FileText size={16} />,        label: 'Reports' },
  { to: '/settings',      icon: <Settings size={16} />,        label: 'Settings' },
  { to: '/diagnostics',   icon: <Activity size={16} />,        label: 'System Diagnostics' },
];

export const Sidebar: React.FC = () => {
  const { activeProject, setActiveProject } = useAppStore();
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    // If no active project is selected, fetch the list and select the first one as default
    const loadDefaultProject = async () => {
      if (!activeProject) {
        try {
          const projects = await listProjects();
          if (projects && projects.length > 0) {
            setActiveProject(projects[0]);
          }
        } catch (err) {
          console.error('Failed to load default project:', err);
        }
      }
    };
    loadDefaultProject();
  }, [activeProject, setActiveProject]);

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="sidebar-logo-text">Code Equivalence</div>
        <div className="sidebar-logo-sub">Platform v0.1</div>
      </div>

      <div style={{ padding: '0 16px', marginBottom: 20 }}>
        <div className="sidebar-section-label">Active Project</div>
        <button
          onClick={() => setShowModal(true)}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            width: '100%',
            background: 'var(--bg-card)',
            border: '1px solid var(--border-normal)',
            borderRadius: 'var(--radius-md)',
            padding: '8px 12px',
            color: 'var(--text-primary)',
            cursor: 'pointer',
            textAlign: 'left',
            marginTop: 4,
            outline: 'none',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, overflow: 'hidden' }}>
            <FolderKanban size={14} className="text-secondary" style={{ flexShrink: 0 }} />
            <span style={{ fontSize: 13, fontWeight: 500, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {activeProject ? activeProject.name : 'Select Project...'}
            </span>
          </div>
          <ChevronDown size={14} style={{ opacity: 0.5, flexShrink: 0 }} />
        </button>
      </div>

      <nav className="sidebar-nav">
        <div className="sidebar-section-label">Navigation</div>
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              `nav-item${isActive ? ' active' : ''}`
            }
          >
            <span className="nav-icon">{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="offline-badge">
          <div className="offline-dot" />
          <span>OFFLINE — SECURE</span>
        </div>
        <div style={{ marginTop: 6, fontSize: 10, color: 'var(--text-muted)' }}>
          No internet connection required
        </div>
      </div>

      {showModal && <ProjectModal onClose={() => setShowModal(false)} />}
    </aside>
  );
};

