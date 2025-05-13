import { Link } from 'react-router-dom';
import './Layout.css';

export default function Layout({ links, children }) {
  /*
  <Link to="/editor">Home</Link>
  <Link to="/generate">Generate</Link>
  */
  return (
    <div className="layout">
      <header className="layout-header">
        <h1 className="logo">Course Scheduler</h1>
        <nav className="layout-nav">
          {links}
          <Link to="https://cosleyw.github.io/Spring-2025-AI-project/client/tree_view/tree_view.html" target="_blank">
            Dependency Visualizer
          </Link>
        </nav>
      </header>
      <main className="layout-content">{children}</main>
      <footer className="layout-footer">© {new Date().getFullYear()} University Scheduler</footer>
    </div>
  );
}
