import React, { useState, useMemo } from 'react';
import { Droppable, Draggable } from '@hello-pangea/dnd';
import './CourseList.css';
import CourseDisplayList from './CourseDisplayList';

export default function CourseList({
  courses,
  onRegenerate, // ← new
  onSelectCourse,
}) {
  const [search, setSearch] = useState('');

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return courses;
    return courses.filter((c) => c.code.toLowerCase().includes(q) || c.name.toLowerCase().includes(q));
  }, [search, courses]);

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
        <Droppable droppableId="courses" isDropDisabled={true}>
          {(provided) => (
            <div className="course-list" ref={provided.innerRef} key={filtered} {...provided.droppableProps}>
              <CourseDisplayList courses={filtered} page_size={50} onClick={onSelectCourse} />
              {provided.placeholder}
            </div>
          )}
        </Droppable>
      </div>
    </div>
  );
}
