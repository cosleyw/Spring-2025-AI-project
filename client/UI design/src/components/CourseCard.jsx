import { useSchedule } from '../context/ScheduleContext';

function CourseCard({ provided, course, removeCourse, onSelectCourse }) {
  const { toggleDesiredCourse } = useSchedule();
  return (
    <div
      className={'course-card ' + (course.hasOwnProperty('desired') ? 'course-card-desired' : '')}
      ref={provided.innerRef}
      {...provided.draggableProps}
      {...provided.dragHandleProps}
    >
      <span className="remove-btn" onClick={removeCourse}>
        ×
      </span>
      <span className="toggle-desired-btn" onClick={() => toggleDesiredCourse(course.id)}>
        =
      </span>
      <span className="course-link" onClick={onSelectCourse}>
        {course.code}: {course.name} <span className="course-semester">({course.semester})</span>
      </span>
    </div>
  );
}

export default CourseCard;
