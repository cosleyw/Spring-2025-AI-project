// src/components/ScheduleViewer.jsx
import React from 'react';
import { Link } from 'react-router-dom';
import './ScheduleViewer.css';

export default function ScheduleViewer({ schedule, allCourses }) {
  if (!Array.isArray(schedule)) {
    return <div className="middle-panel">No schedule to display</div>;
  }

  return (
    <div className="middle-panel">
      {schedule.map((sem, sIdx) => {
        // title + list of course-IDs or course-objects
        const title = sem.name || `Semester ${sIdx + 1}`;
        const items = Array.isArray(sem.courses)
          ? sem.courses
          : Array.isArray(sem)
          ? sem
          : [];

        return (
          <div key={sem.id ?? sIdx} className="semester-box">
            <h4>{title}</h4>

            {items.map((item, idx) => {
              // unify string-ID vs. object
              let id, code, name;
              if (typeof item === 'string') {
                id   = item;
                const meta = allCourses.find(c => c.id === item) || {};
                code = meta.code || item;
                name = meta.name || '';
              } else {
                // object
                id   = item.id;
                code = item.code ?? id;
                name = item.name ?? '';
              }

              return (
                <div key={id} className="course-card">
                  <Link to={`/courses/${encodeURIComponent(id)}`}>
                    {code}: {name}
                  </Link>
                </div>
              );
            })}
          </div>
        );
      })}
    </div>
  );
}
