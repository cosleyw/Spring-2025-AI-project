// src/components/DegreeBrowser.jsx
import React, { useState, useEffect } from 'react';
import { get_degrees, get_degree }   from '../api';
import TreeNode                       from './TreeNode';
import './DegreeBrowser.css';

export default function DegreeBrowser() {
  const [list,    setList]   = useState([]);
  const [tree,    setTree]   = useState(null);
  const [error,   setError]  = useState('');
  const [loading, setLoading] = useState(false);

  // 1) load degree IDs
  useEffect(() => {
    get_degrees()
      .then(setList)
      .catch(e => setError(e.message));
  }, []);

  // 2) when one is clicked
  const onSelect = async (id) => {
    setLoading(true);
    setError('');
    try {
      const node = await get_degree(id);
      setTree(node);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="degree-browser">
      <div className="degree-list">
        <h3>Available Degrees</h3>
        {error && <div className="error">Error: {error}</div>}
        <ul>
          {list.map(d => (
            <li key={d.id}>
              <button onClick={() => onSelect(d.id)}>
                {d.name}
              </button>
            </li>
          ))}
        </ul>
      </div>
      <div className="degree-tree">
        <h3>Degree Tree</h3>
        {loading && <p>Loading tree…</p>}
        {!loading && !tree && <p>Select one above</p>}
        {tree && <TreeNode node={tree} />}
      </div>
    </div>
  );
}
