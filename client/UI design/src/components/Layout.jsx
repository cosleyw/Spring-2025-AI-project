import React from 'react';
import { Link } from 'react-router-dom';
import './Layout.css';

export default function Layout({ children }) {
  return (
    <div className="layout">
      <header className="layout-header">
        <h1 className="logo">Course Scheduler</h1>
        <nav className="layout-nav">
          <Link to="/">Home</Link>
          <Link to="/schedule/generate">Generate</Link>
          <Link to="/degrees">Degrees</Link>
        </nav>
      </header>
      <main className="layout-content">
        {children}
      </main>
      <footer className="layout-footer">
        © {new Date().getFullYear()} University Scheduler
      </footer>
    </div>
  );
}
