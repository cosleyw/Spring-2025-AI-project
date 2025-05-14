// src/hooks/useCourses.js
import { useEffect, useMemo, useState } from 'react';
import { get_courses } from '../api';

export function useCourses() {
  const [courses, setCourses]   = useState([]);
  const courses_dict = useMemo(() => {
    const dict = {}
    for(let i = 0; i < courses.length; i++) {
      const course = courses[i];
      dict[course['id']] = course
    }
    return dict
    }, [courses]
  )

  // load master list
  useEffect(() => {
    get_courses().then(setCourses).catch(console.error);
  }, []);

  return { courses, courses_dict };
}
