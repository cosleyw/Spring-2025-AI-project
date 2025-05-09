// src/hooks/useCourses.js
import { useState, useEffect } from 'react';
import { get_courses } from '../api';

export function useCourses() {
  const [courses, setCourses]   = useState([]);
  const [schedule, setSchedule] = useState([]);

  // load master list
  useEffect(() => {
    get_courses().then(setCourses).catch(console.error);
  }, []);

  // init 8 empty semesters
  useEffect(() => {
    setSchedule(
      Array.from({ length: 8 }, (_, i) => ({
        id:      `sem-${i + 1}`,
        name:    `Semester ${i + 1}`,
        courses: []
      }))
    );
  }, []);

  // handle drag + drop
  function onDragEnd(result) {
    console.log('📦 onDragEnd:', result);
    const { source, destination, draggableId } = result;
    if (!destination) return;
    if (
      source.droppableId === destination.droppableId &&
      source.index       === destination.index
    ) return;

    setSchedule(prev => {
      // deep clone semesters
      const next = prev.map(s => ({ ...s, courses: [...s.courses] }));

      // grab the full course object
      const moved = courses.find(c => c.id === draggableId);

      // remove from old (if not from master list)
      if (source.droppableId !== 'courses') {
        const src = next.find(s => s.id === source.droppableId);
        src.courses.splice(source.index, 1);
      }

      // insert into new semester
      const dst = next.find(s => s.id === destination.droppableId);
      dst.courses.splice(destination.index, 0, moved);

      return next;
    });
  }

  return { courses, schedule };
}
