import CoursePreview from './CoursePreview';
import './SemesterPreview.css';

export default function SemesterPreview({ courses, id }) {
  return (
    <div className="semester-preview">
      <h4>Semester {id}:</h4>
      <div className="semester-preview-courses">
        {courses.map((course) => {
          console.debug(course);
          return <CoursePreview id={course['id']} name={course['name']} />;
        })}
      </div>
    </div>
  );
}
