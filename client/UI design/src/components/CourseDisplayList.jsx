import { Draggable } from '@hello-pangea/dnd';
import ConditionalButton from './ConditionalButton';
import './CourseDisplayList.css';

function CourseDisplayList({ courses, page_size, onClick, page, setPage }) {
  const decrement = () => setPage((p) => p - 1);
  const increment = () => setPage((p) => p + 1);

  return (
    <>
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
    </>
  );
}

export default CourseDisplayList;
