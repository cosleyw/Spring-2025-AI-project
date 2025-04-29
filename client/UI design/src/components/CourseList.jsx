// src/components/CourseList.jsx
import React, { useState, useMemo } from 'react';
import { Droppable, Draggable }      from 'react-beautiful-dnd';
import { Link }                      from 'react-router-dom';
import './CourseList.css';

export default function CourseList({ courses }) {
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
    <div className="left-panel">
      <input
        className="course-search"
        type="text"
        placeholder="Search courses…"
        value={search}
        onChange={e => setSearch(e.target.value)}
      />

      <Droppable
        droppableId="courses"
        isDropDisabled={true}     // only prop we need here
      >
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
                  >
                    <Link to={`/courses/${encodeURIComponent(c.id)}`} className="course-link">
                      <h4>{c.code}: {c.name}</h4>
                    </Link>
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
  );
}
