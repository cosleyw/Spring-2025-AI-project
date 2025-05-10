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

  const handleSetSchedule = (raw, start_year, start_term, courses) => {
    const onlyIds = raw.slice(1, raw.length);

    //  enrich & label each semester
    const termOrder = ['Fall', 'Spring'];
    let term = start_term;
    let year = start_year;

    const enriched = onlyIds.map((ids, idx) => {
      if (idx > 0) {
        let next = termOrder.indexOf(term) + 1;
        if (next >= termOrder.length) {
          next = 0;
          year++;
        }
        term = termOrder[next];
      }

      console.log('Courses');
      console.log(courses);
      console.log('Ids');
      console.log(ids);

      const semesterCourses = ids.map((id) => {
        console.log('Id: ' + id);
        let found = courses.find((c) => c.id === id);
        console.log(found);
        return found || {};
      });

      console.log('Semester courses');
      console.log(semesterCourses);

      return {
        name: `Semester ${idx + 1}`,
        term,
        year,
        courses: semesterCourses,
      };
    });

    //  stash it & go back Home
    setSchedule(enriched);
  };

  return (
    <ScheduleContext.Provider value={{ schedule, handleSetSchedule, setSchedule }}>{children}</ScheduleContext.Provider>
  );
}

export function useSchedule() {
  const ctx = useContext(ScheduleContext);
  if (!ctx) throw new Error('useSchedule must be inside ScheduleProvider');
  return ctx;
}
