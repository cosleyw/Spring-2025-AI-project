// src/components/ScheduleViewer.jsx
import React from 'react';
import { Droppable, Draggable } from 'react-beautiful-dnd';
import './ScheduleViewer.css';

export default function ScheduleViewer({ schedule }) {
  return (
    <div className="middle-panel">
      {schedule.map(sem => (
        <Droppable
          key={sem.id}
          droppableId={sem.id}     // one unique id per semester
        >
          {(provided, snapshot) => (
            <div
              className={`semester-box ${snapshot.isDraggingOver ? 'over' : ''}`}
              ref={provided.innerRef}
              {...provided.droppableProps}
            >
              <h4>{sem.name}</h4>
              {sem.courses.map((course, idx) => (
                <Draggable
                  key={course.id}
                  draggableId={course.id}
                  index={idx}
                >
                  {(prov, snap) => (
                    <div
                      className={`course-card ${snap.isDragging ? 'dragging' : ''}`}
                      ref={prov.innerRef}
                      {...prov.draggableProps}
                      {...prov.dragHandleProps}
                    >
                      {course.code}: {course.name}
                    </div>
                  )}
                </Draggable>
              ))}
              {provided.placeholder}
            </div>
          )}
        </Droppable>
      ))}
    </div>
  );
}
