import { Draggable } from '@hello-pangea/dnd';
import ConditionalButton from './ConditionalButton';
import './CourseDisplayList.css';

function CourseDisplayList({ courses, page_size, onClick, page, setPage, saveSchedule }) {
  const decrement = () => setPage((p) => p - 1);
  const increment = () => setPage((p) => p + 1);

  return (
    <>
      <div className="course-display-list">
        <ConditionalButton condition={page > 0} onClick={decrement} className="previous-button">
          Previous
        </ConditionalButton>
        <button onClick={saveSchedule} className="save-button">
          Save
        </button>
        <ConditionalButton
          condition={courses.length > (page + 1) * page_size - 1}
          onClick={increment}
          className="next-button"
        >
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
                {c.code}: {c.name} <span className="course-semester">({c.semester})</span>
              </h4>
            </div>
          )}
        </Draggable>
      ))}

      <div className="course-display-list">
        <ConditionalButton condition={page > 0} onClick={decrement} className="previous-button">
          Previous
        </ConditionalButton>
        <ConditionalButton
          condition={courses.length > (page + 1) * page_size - 1}
          onClick={increment}
          className="next-button"
        >
          Next
        </ConditionalButton>
      </div>
    </>
  );
}

export default CourseDisplayList;
