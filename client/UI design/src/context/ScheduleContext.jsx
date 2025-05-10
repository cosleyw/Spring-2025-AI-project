// src/context/ScheduleContext.jsx
import { createContext, useContext, useState } from 'react';

const ScheduleContext = createContext();

// Initialize with 8 empty semesters
const makeEmptySchedule = () =>
  Array.from({ length: 8 }, (_, i) => ({
    name: `Semester ${i + 1}`,
    term: '',
    year: '',
    courses: [],
  }));

export function ScheduleProvider({ children }) {
  const [schedule, setSchedule] = useState(makeEmptySchedule());

  const toggleDesired = (course) => {
    if (course.hasOwnProperty('desired')) {
      const { desired: _, ...rest } = course;
      return rest;
    } else {
      return { ...course, desired: true };
    }
  };

  const toggleDesiredCourse = (id) => {
    setSchedule((sch) =>
      sch.map((sem) => ({
        ...sem,
        courses: sem['courses'].map((c) => (c.id === id ? toggleDesired(c) : c)),
      }))
    );
  };

  const setNewSchedule = (raw, start_year, start_term, courses) => {
    setSchedule((previousSchedule) => {
      const previouslyDesiredCourses = previousSchedule
        .map((sem) => sem.courses)
        .flat()
        .filter((course) => course.hasOwnProperty('desired'))
        .map((course) => course.id);
      const onlyIds = raw.slice(1, raw.length);

      //  enrich & label each semester
      const termOrder = ['Fall', 'Spring'];
      let term = start_term;
      let year = start_year;

      return onlyIds.map((ids, idx) => {
        if (idx > 0) {
          let next = termOrder.indexOf(term) + 1;
          if (next >= termOrder.length) {
            next = 0;
            year++;
          }
          term = termOrder[next];
        }

        const semesterCourses = ids.map((id) => {
          const foundCourse = courses.find((c) => c.id === id) || {};
          if (previouslyDesiredCourses.includes(id)) {
            return { ...foundCourse, desired: true };
          }
          return foundCourse;
        });

        console.debug('Semster couses');
        console.debug(semesterCourses);

        return {
          name: `Semester ${idx + 1}`,
          term,
          year,
          courses: semesterCourses,
        };
      });
    });
  };

  return (
    <ScheduleContext.Provider value={{ schedule, setNewSchedule, setSchedule, toggleDesiredCourse }}>
      {children}
    </ScheduleContext.Provider>
  );
}

export function useSchedule() {
  const ctx = useContext(ScheduleContext);
  if (!ctx) throw new Error('useSchedule must be inside ScheduleProvider');
  return ctx;
}
