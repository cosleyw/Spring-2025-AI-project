import React from 'react';
import { useParams }   from 'react-router-dom';
import { useCourses }  from '../hooks/useCourses';
import './CourseDetails.css';

export default function CourseDetails() {
  const { id } = useParams();
  const { courses } = useCourses();
  const course = courses.find(c => c.id === id);

  if (!course) {
    return (
      <div className="right-panel course-details">
        <p>Course not found.</p>
      </div>
    );
  }

  const {
    code,
    name,
    description = 'No description available.',
    credits    = '—',
    instructor = 'TBA',
    offered    = 'TBA',
  } = course;

  return (
    <div className="right-panel course-details">
      <h3>{code}: {name}</h3>
      <p><strong>Credits:</strong> {credits}</p>
      <p><strong>Instructor:</strong> {instructor}</p>
      <p><strong>Offered:</strong> {offered}</p>
      <h4>Description</h4>
      <p>{description}</p>
    </div>
  );
}
