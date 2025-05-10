// src/hooks/useCourses.js
import { useEffect, useState } from 'react';
import { get_courses } from '../api';

export function useCourses() {
  const [courses, setCourses]   = useState([]);

  // load master list
  useEffect(() => {
    get_courses().then(setCourses).catch(console.error);
  }, []);

  return { courses };
}
