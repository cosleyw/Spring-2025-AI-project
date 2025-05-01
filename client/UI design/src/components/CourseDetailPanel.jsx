// src/components/CourseDetailPanel.jsx
import React, { useState, useEffect } from 'react';
import { get_course } from '../api';
import './CourseDetailPanel.css';

export default function CourseDetailPanel({ courseId, onClose }) {
  const [course, setCourse] = useState(null);
  const [error, setError]   = useState('');

  useEffect(() => {
    setCourse(null);
    get_course(courseId)
      .then(setCourse)
      .catch(err => {
        console.error(err);
        setError('Failed to load details.');
      });
  }, [courseId]);

  return (
    <div className="course-detail-panel">
      <button className="close-btn" onClick={onClose}>×</button>
      {error && <div className="error">{error}</div>}
      {!course
        ? <div className="loading">Loading…</div>
        : (
          <div className="details">
            <h2>{course.code}: {course.name}</h2>
            <p><strong>Description:</strong></p>
            <p>{course.description || 'No description available.'}</p>
            {/* add more fields here as you'd like */}
          </div>
        )
      }
    </div>
  );
}
