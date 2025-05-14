import './CoursePreview.css';
export default function CoursePreview({ id, name }) {
  return (
    <div className="course-preview">
      <h4>
        {id}: {name}
      </h4>
    </div>
  );
}
