import React from 'react';
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
  Wifi,
} from 'lucide-react';

interface NavItem {
  to: string;
  icon: React.ReactNode;
  label: string;
}

const navItems: NavItem[] = [
  { to: '/',              icon: <LayoutDashboard size={16} />, label: 'Dashboard' },
  { to: '/analysis',      icon: <Code2 size={16} />,           label: 'Code Analysis' },
  { to: '/gaps',          icon: <GitCompareArrows size={16} />, label: 'Gap Detection' },
  { to: '/tests',         icon: <FlaskConical size={16} />,    label: 'Test Execution' },
  { to: '/visualization', icon: <BarChart3 size={16} />,       label: 'Visualization' },
  { to: '/reports',       icon: <FileText size={16} />,        label: 'Reports' },
  { to: '/settings',      icon: <Settings size={16} />,        label: 'Settings' },
  { to: '/diagnostics',   icon: <Activity size={16} />,        label: 'System Diagnostics' },
];

export const Sidebar: React.FC = () => {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="sidebar-logo-text">Code Equivalence</div>
        <div className="sidebar-logo-sub">Platform v0.1</div>
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
    </aside>
  );
};
