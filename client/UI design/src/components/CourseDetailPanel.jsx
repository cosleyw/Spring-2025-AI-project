// src/components/CourseDetailPanel.jsx
import React from 'react';
import { useCourses } from '../hooks/useCourses';
import './CourseDetailPanel.css';

export default function CourseDetailPanel({ courseId, onClose }) {
  const { courses } = useCourses();
  const course      = courses.find(c => c.id === courseId);

  // if they clicked “×” or route changed
  if (!courseId || !course) return null;

  return (
    <aside className="course-detail-panel">
      <button className="close-btn" onClick={onClose}>&times;</button>
      <h2>{course.code}: {course.name}</h2>

      <p>
        <strong>Credits:</strong> {course.credits ?? '—'}
      </p>

      <section>
        <h3>Description</h3>
        <p>{course.description || 'No description available.'}</p>
      </section>
    </aside>
  );
}
