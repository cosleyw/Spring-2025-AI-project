import { Draggable } from '@hello-pangea/dnd';
import { useState } from 'react';
import './CourseDisplayList.css';
import ConditionalButton from './ConditionalButton';

function CourseDisplayList({ courses, page_size, onClick }) {
  const [page, setPage] = useState(0);

  const decrement = () => setPage((p) => p - 1);
  const increment = () => setPage((p) => p + 1);

  return (
    <div>
      <div className="course-display-list">
        <ConditionalButton condition={page > 0} onClick={decrement}>
          Previous
        </ConditionalButton>
        <ConditionalButton condition={courses.length > (page + 1) * page_size - 1} onClick={increment}>
          Next
        </ConditionalButton>
      </div>
      {courses.slice(page * page_size, (page + 1) * page_size).map((c, idx) => (
        <Draggable key={c.id} draggableId={c.id} index={idx}>
          {(prov) => (
            <div
              className="course-card"
              ref={prov.innerRef}
              {...prov.draggableProps}
              {...prov.dragHandleProps}
              onClick={() => onClick(c.id)}
            >
              <h4>
                {c.code}: {c.name}
              </h4>
              <button>⭐</button>
            </div>
          )}
        </Draggable>
      ))}

      <div className="course-display-list">
        <ConditionalButton condition={page > 0} onClick={decrement}>
          Previous
        </ConditionalButton>
        <ConditionalButton condition={courses.length > (page + 1) * page_size - 1} onClick={increment}>
          Next
        </ConditionalButton>
      </div>
    </div>
  );
}

export default CourseDisplayList;
