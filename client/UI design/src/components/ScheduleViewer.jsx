// src/components/ScheduleViewer.jsx
import React from 'react';
import { Droppable, Draggable } from '@hello-pangea/dnd';
import './ScheduleViewer.css';

export default function ScheduleViewer({
  schedule,
  setSchedule,
  onSelectCourse
}) {
  // helper to remove one course
  const removeCourse = (semIdx, courseId) => {
    setSchedule(s =>
      s.map((sem,i) =>
        i === semIdx
          ? { ...sem, courses: sem.courses.filter(c=>c.id!==courseId) }
          : sem
      )
    );
  };

  return (
    <div className="middle-panel">
      {schedule.map((sem, sIdx) => {
        const totalCredits = sem.courses.reduce((sum,c)=>sum+(c.credits||0),0);
        return (
          <Droppable key={sIdx} droppableId={`sem-${sIdx}`}>
            {provided => (
              <div
                className="semester-box"
                ref={provided.innerRef}
                {...provided.droppableProps}
              >
                <h4>
                  {sem.term} {sem.year} — {sem.name}
                  <small className="credit-badge">
                    ({totalCredits} cr)
                  </small>
                </h4>

                {sem.courses.map((c, idx) => (
                  <Draggable
                    key={c.id}
                    draggableId={c.id}
                    index={idx}
                  >
                    {prov => (
                      <div
                        className="course-card"
                        ref={prov.innerRef}
                        {...prov.draggableProps}
                        {...prov.dragHandleProps}
                      >
                        <span
                          className="remove-btn"
                          onClick={() => removeCourse(sIdx, c.id)}
                        >×</span>
                        <span
                          className="course-link"
                          onClick={() => onSelectCourse(c.id)}
                        >
                          {c.code}: {c.name}
                        </span>
                      </div>
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
