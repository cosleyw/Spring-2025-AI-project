import React, { useState, useEffect } from 'react';
import { get_course } from '../api';
import './CourseDetailPanel.css';

export default function CourseDetailPanel({ courseId, onClose }) {
  const [course, setCourse] = useState(null);
  const [error, setError]   = useState('');

  useEffect(() => {
    if (!courseId) return;
    get_course(courseId)
      .then(c => setCourse(c))
      .catch(err => setError(err.message));
  }, [courseId]);

  if (!courseId) return null;

  return (
    <aside className="course-detail-panel">
      <button className="close-btn" onClick={onClose}>&times;</button>
      {error && <div className="error">{error}</div>}
      {!course ? (
        <div className="loading">Loading…</div>
      ) : (
        <>
          <h2>{course.code}: {course.name}</h2>
          <p><strong>ID:</strong> {course.id}</p>
          <h3>Description</h3>
          <p>{course.description || 'No description available.'}</p>
        </>
      )}
    </aside>
  );
}
