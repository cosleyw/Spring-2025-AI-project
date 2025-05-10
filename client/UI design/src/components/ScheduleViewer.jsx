// src/components/ScheduleViewer.jsx
import { Draggable, Droppable } from '@hello-pangea/dnd';
import { displayCourseHours } from '../util/CourseHelper';
import CourseCard from './CourseCard';
import './ScheduleViewer.css';

export default function ScheduleViewer({ schedule, setSchedule, onSelectCourse }) {
  // helper to remove one course
  const removeCourse = (semIdx, courseId) => {
    setSchedule((s) =>
      s.map((sem, i) => (i === semIdx ? { ...sem, courses: sem.courses.filter((c) => c.id !== courseId) } : sem))
    );
  };

  return (
    <div className="middle-panel">
      {schedule.map((sem, sIdx) => {
        const totalCredits = sem.courses.length > 0 ? displayCourseHours(...sem.courses) : '0';
        return (
          <Droppable key={sIdx} droppableId={`sem-${sIdx}`}>
            {(provided) => (
              <div className="semester-box" ref={provided.innerRef} {...provided.droppableProps}>
                <h4>
                  {sem.term} {sem.year} — {sem.name}
                  <small className="credit-badge">({totalCredits} cr)</small>
                </h4>

                {sem.courses.map((c, idx) => (
                  <Draggable key={c.id} draggableId={c.id} index={idx}>
                    {(prov) => (
                      <CourseCard
                        provided={prov}
                        course={c}
                        removeCourse={() => removeCourse(sIdx, c.id)}
                        onSelectCourse={() => onSelectCourse(c.id)}
                      />
                    )}
                  </Draggable>
                ))}
                {provided.placeholder}
              </div>
            )}
          </Droppable>
        );
      })}
    </div>
  );
}
