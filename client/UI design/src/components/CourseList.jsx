import React, { useState, useMemo, useEffect } from 'react';
import { Droppable, Draggable } from '@hello-pangea/dnd';
import './CourseList.css';
import CourseDisplayList from './CourseDisplayList';
import { useSchedule } from '../context/ScheduleContext';

export default function CourseList({
  courses,
  onRegenerate, // ← new
  onSelectCourse,
}) {
  const [search, setSearch] = useState('');
  const { schedule } = useSchedule();
  const [page, setPage] = useState(0);

  // If search changes, reset page number
  useEffect(() => setPage(0), [search]);

  const filtered = useMemo(() => {
    const q = search.toLowerCase();
    let unscheduledCourses = courses.filter(
      (c) =>
        !schedule
          .map((sem) => sem['courses'])
          .flat()
          .map((schedule_course) => schedule_course['id'])
          .includes(c.id)
    );
    if (!q) return unscheduledCourses;
    return unscheduledCourses.filter((c) => c.code.toLowerCase().includes(q) || c.name.toLowerCase().includes(q));
  }, [search, courses, schedule]);

  return (
    <div className="left-panel course-list-container">
      {/* — fixed header — */}
      <div className="course-list-header">
        <button className="regenerate-button" onClick={onRegenerate}>
          Regenerate From Here
        </button>
        <input
          className="course-search"
          type="text"
          placeholder="Search courses…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {/* — only this area scrolls — */}
      <div className="course-list-scroller">
        <Droppable droppableId="courses" isDropDisabled={false}>
          {(provided) => (
            <div className="course-list" ref={provided.innerRef} key={filtered} {...provided.droppableProps}>
              <CourseDisplayList
                courses={filtered}
                page_size={50}
                onClick={onSelectCourse}
                page={page}
                setPage={setPage}
              />
              {provided.placeholder}
            </div>
          )}
        </Droppable>
      </div>
    </div>
  );
}
