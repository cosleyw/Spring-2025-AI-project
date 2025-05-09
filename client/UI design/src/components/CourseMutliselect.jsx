import { useMemo } from 'react';
import React from 'react';
import { useRef } from 'react';
import { useState } from 'react';
import './CourseMultiselect.css';

function CourseMultiselect({ ids, courses, handleMouseDown, classes, title }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [onlyActive, setOnlyActive] = useState(false);
  const selectionBox = useRef(null);

  const filtered_courses = useMemo(
    () =>
      courses.filter(
        (course) =>
          (course.id.toLowerCase().search(searchTerm.toLowerCase()) !== -1 ||
            course.name.toLowerCase().search(searchTerm.toLowerCase()) !== -1) &&
          (!onlyActive || ids.includes(course.id))
      ),
    [ids, courses, searchTerm, onlyActive]
  );

  return (
    <div className={classes}>
      <label>{title}</label>
      <div className="course-multiselect-options">
        <input
          className="course-multiselect-search"
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        ></input>
        <input
          className="course-multiselect-toggle"
          type="checkbox"
          checked={onlyActive}
          onChange={(e) => setOnlyActive(e.target.checked)}
        ></input>
      </div>
      <select multiple value={ids} ref={selectionBox}>
        {filtered_courses.map((c) => (
          <option key={c.id} value={c.id} onMouseDown={handleMouseDown}>
            {c.code} — {c.name}
          </option>
        ))}
      </select>
    </div>
  );
}

export default CourseMultiselect;
