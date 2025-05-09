function CourseCard({ provided, course, onClick, children }) {
  return (
    <div
      className="course-card"
      ref={provided.innerRef}
      {...provided.draggableProps}
      {...provided.dragHandleProps}
      onClick={onClick}
      style={{ height: '200px' }}
    >
      <h4>
        {course.code}: {course.name} {children}
      </h4>
      <button>⭐</button>
    </div>
  );
}

export default CourseCard;
