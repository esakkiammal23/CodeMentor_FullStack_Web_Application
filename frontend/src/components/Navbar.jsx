import React from 'react';
import { Link, useLocation } from 'react-router-dom';

export default function Navbar({ user, onLogout }) {
  const location = useLocation();
  const active = (path) => location.pathname === path ? 'nav-btn active' : 'nav-btn';

  return (
    <nav className="navbar">
      <span className="navbar-brand">🎓 CodeMentor</span>
      <div className="navbar-links">
        <Link className={active('/dashboard')} to="/dashboard">Home</Link>
        <Link className={active('/learn')} to="/learn">Learn</Link>
        <Link className={active('/test')} to="/test">Test</Link>
        <Link className={active('/certificates')} to="/certificates">Certificates</Link>
        <span style={{ color: '#9ca3af', fontSize: '0.85rem' }}>Hi, {user.full_name || user.email}</span>
        <button className="nav-btn" onClick={onLogout}>Logout</button>
      </div>
    </nav>
  );
}