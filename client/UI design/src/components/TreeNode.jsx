// src/components/TreeNode.jsx
import React from 'react';

export default function TreeNode({ node, level = 0 }) {
  if (!node) return null;
  const indent = { marginLeft: level * 16 };

  //  course leaf
  if (node.type === 'course') {
    const code  = `${(node.dept ?? '').toUpperCase()} ${node.number ?? ''}`;
    const title = node.name || node.info || '';
    return (
      <div style={indent}>
        📘 <strong>{code}</strong> — {title}
      </div>
    );
  }

  // tag wrapper
  if (node.type === 'tag') {
    return (
      <div style={indent}>
        <strong>▾ {node.info}</strong>
        <TreeNode node={node.node} level={level + 1} />
      </div>
    );
  }

  //  credit-range with options
  if (node.type === 'credit-range') {
    return (
      <div style={indent}>
        <em>{node.n} – {node.m} credits</em>
        {node.options.map((opt, i) => (
          <TreeNode key={i} node={opt} level={level + 1} />
        ))}
      </div>
    );
  }

  //  generic fallback
  if (Array.isArray(node.options)) {
    return (
      <div style={indent}>
        {node.options.map((opt, i) => (
          <TreeNode key={i} node={opt} level={level + 1} />
        ))}
      </div>
    );
  }

  return null;
}
