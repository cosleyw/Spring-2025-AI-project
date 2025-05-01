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
        //  Semester title (I already set sem.name in the generator)
        const title = sem.name;
        //  Term + year
        const term = sem.term;
        const year = sem.year;
        //  List of course objects (you built them in generator)
        const courses = sem.courses || [];

        // Sum up credits
        const totalCredits = courses.reduce(
          (sum, c) => sum + (c.credits || 0),
          0
        );

        return (
          <div key={sIdx} className="semester-box">
            <h4>
              {term} {year} — {title}{' '}
              <small className="credit-badge">({totalCredits} cr)</small>
            </h4>

            {courses.map(c => (
              <div
                key={c.id}
                className="course-card"
                onClick={() => onSelectCourse(c.id)}
              >
                {c.code}: {c.name}
              </div>
            ))}
          </div>
        );
      })}
    </div>
  );
}
