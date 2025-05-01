// src/components/ScheduleViewer.jsx
import React from 'react';
import './ScheduleViewer.css';

export default function ScheduleViewer({
  schedule,
  allCourses,
  onSelectCourse
}) {
  if (!Array.isArray(schedule)) {
    return <div className="middle-panel">No schedule to display</div>;
  }

  return (
    <div className="middle-panel">
      {schedule.map((sem, sIdx) => {
        const title = sem.name || `Semester ${sIdx + 1}`;
        // sem.courses array or fallback to sem itself if array
        const items = Array.isArray(sem.courses)
          ? sem.courses
          : Array.isArray(sem)
          ? sem
          : [];

        return (
          <div key={sIdx} className="semester-box">
            <h4>{title}</h4>
            {items.map((item, idx) => {
              // unify item → { id, code, name }
              let id, code, name;
              if (typeof item === 'string') {
                id = item;
                const meta = allCourses.find(c => c.id === item) || {};
                code = meta.code || item;
                name = meta.name || '';
              } else {
                id   = item.id;
                code = item.code ?? id;
                name = item.name ?? '';
              }
              return (
                <div
                  key={id}
                  className="course-card"
                  onClick={() => onSelectCourse(id)}
                >
                  {code}: {name}
                </div>
              );
            })}
          </div>
        );
      })}
    </div>
  );
}
