// src/components/DegreeAccordion.jsx
import { useEffect, useState } from 'react';
import { get_degree } from '../api';
import './DegreeAccordion.css';

export default function DegreeAccordion({ degreeIds }) {
  const [treeData, setTreeData] = useState([]);
  const [error, setError] = useState();

  useEffect(() => {
    if (!degreeIds || degreeIds.length === 0) return;
    setTreeData([]);
    setError(null);

    degreeIds.forEach((degreeId) => {
      get_degree(degreeId)
        .then((raw) => setTreeData((prev) => [...prev, raw.degree ?? raw.node ?? raw]))
        .catch((err) => {
          console.error(err);
          setError('Failed to load requirements');
        });
    });
  }, [degreeIds]);

  // recursive rendering
  const renderNode = (node) => {
    const label =
      node.info || node.name || (node.dept && node.number && `${node.dept.toUpperCase()} ${node.number}`) || node.id;

    if (Array.isArray(node.options) && node.options.length > 0) {
      return (
        <details key={label} open>
          <summary>{label}</summary>
          <div className="children">{node.options.map((opt) => renderNode(opt.node ?? opt))}</div>
        </details>
      );
    }

    return (
      <div key={label} className="leaf">
        {label}
      </div>
    );
  };

  return (
    <div className="degree-accordion-container">
      {error && <div className="error">{error}</div>}
      {(!degreeIds || degreeIds.length === 0) && <div className="placeholder">Select a degree to see requirements</div>}
      {treeData.map((rootNode) => renderNode(rootNode))}
    </div>
  );
}
