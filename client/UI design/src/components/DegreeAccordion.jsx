// src/components/DegreeAccordion.jsx
import { useEffect, useState } from 'react';
import { get_degrees_full } from '../api';
import './DegreeAccordion.css';

export default function DegreeAccordion({ degreeIds }) {
  const [treeData, setTreeData] = useState([]);
  const [error, setError] = useState();
  const [degrees, setDegrees] = useState([]);

  useEffect(() => {
    async function get_data() {
      get_degrees_full()
        .then((response) => setDegrees(Object.values(response)))
        .catch((err) => {
          console.error(err);
          setError('Failed to load requirements');
        });
    }
    get_data();
  }, []);

  useEffect(() => {
    setError(null);

    setTreeData(() => {
      return degrees.filter((degree) => degreeIds.includes(degree.id)).sort((a, b) => a.id.localeCompare(b.id));
    });
  }, [degrees, degreeIds]);

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
