// src/components/CourseDetailPanel.jsx
import { useCourses } from '../hooks/useCourses';
import { displayCourseHours } from '../util/CourseHelper';
import './CourseDetailPanel.css';

export default function CourseDetailPanel({ courseId, onClose }) {
  const { courses } = useCourses();
  const course = courses.find((c) => c.id === courseId);

  // if they clicked “×” or route changed
  if (!courseId || !course) return null;

  return (
    <aside className="course-detail-panel">
      <button className="close-btn" onClick={onClose}>
        &times;
      </button>
      <h2>
        {course.code}: {course.name}
      </h2>

      <p>
        <strong>Credits:</strong> {displayCourseHours(course)}
      </p>

      <section>
        <h3>Description</h3>
        <p>{course.desc || 'No description available.'}</p>
      </section>
    </aside>
  );
}
