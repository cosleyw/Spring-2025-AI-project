import React, { useState, useMemo } from 'react';
import { Droppable, Draggable }     from '@hello-pangea/dnd';
import './CourseList.css';

export default function CourseList({
  courses,
  onRegenerate,     // ← new
  onSelectCourse,
}) {
  const [search, setSearch] = useState('');

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return courses;
    return courses.filter(c =>
      c.code.toLowerCase().includes(q) ||
      c.name.toLowerCase().includes(q)
    );
  }, [search, courses]);

  return (
    <div className="left-panel course-list-container">
      {/* — fixed header — */}
      <div className="course-list-header">
        <button
          className="regenerate-button"
          onClick={onRegenerate}
        >
         Regenerate From Here
        </button>
        <input
          className="course-search"
          type="text"
          placeholder="Search courses…"
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
      </div>

      {/* — only this area scrolls — */}
      <div className="course-list-scroller">
        <Droppable droppableId="courses" isDropDisabled={true}>
          {provided => (
            <div
              className="course-list"
              ref={provided.innerRef}
              {...provided.droppableProps}
            >
              {filtered.map((c, idx) => (
                <Draggable
                  key={c.id}
                  draggableId={c.id}
                  index={idx}
                >
                  {prov => (
                    <div
                      className="course-card"
                      ref={prov.innerRef}
                      {...prov.draggableProps}
                      {...prov.dragHandleProps}
                      onClick={() => onSelectCourse(c.id)}
                    >
                      <h4>{c.code}: {c.name}</h4>
                      <button>⭐</button>
                    </div>
                  )}
                </Draggable>
              ))}
              {provided.placeholder}
            </div>
          )}
        </Droppable>
      </div>
    </div>
  );
}
