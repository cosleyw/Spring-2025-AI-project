// src/components/Home.jsx
import { DragDropContext } from '@hello-pangea/dnd';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSchedule } from '../context/ScheduleContext';
import { useCourses } from '../hooks/useCourses';
import CourseDetailPanel from './CourseDetailPanel';
import CourseList from './CourseList';
import './Home.css';
import ScheduleViewer from './ScheduleViewer';

export default function Home() {
  const navigate = useNavigate();
  const { courses } = useCourses();
  const { schedule, setSchedule } = useSchedule();
  const [selectedCourse, setSelectedCourse] = useState(null);

  const insertAtIndex = (lst, item, index) => {
    return lst.toSpliced(index, 0, item);
  };

  const onDragEnd = (result) => {
    const { source, destination, draggableId } = result;
    if (!destination) return;

    // dragging from left panel into semester
    if (source.droppableId === 'courses' && destination.droppableId.startsWith('sem-')) {
      const semIdx = Number(destination.droppableId.split('-')[1]);
      setSchedule((sch) =>
        sch.map((sem, i) =>
          i === semIdx
            ? {
                ...sem,
                courses: insertAtIndex(
                  sem.courses,
                  { ...courses.find((c) => c.id === draggableId), desired: true },
                  destination.index
                ),
              }
            : sem
        )
      );
      return;
    }

    // dragging out of a semester
    if (source.droppableId.startsWith('sem-')) {
      const fromIdx = Number(source.droppableId.split('-')[1]);
      setSchedule((sch) =>
        sch.map((sem, i) =>
          i === fromIdx ? { ...sem, courses: sem.courses.filter((c) => c.id !== draggableId) } : sem
        )
      );

      // if dropped into another semester
      if (destination.droppableId.startsWith('sem-')) {
        const toIdx = Number(destination.droppableId.split('-')[1]);
        setSchedule((sch) =>
          sch.map((sem, i) =>
            i === toIdx
              ? {
                  ...sem,
                  courses: insertAtIndex(
                    sem.courses,
                    { ...courses.find((c) => c.id === draggableId), desired: true },
                    destination.index
                  ),
                }
              : sem
          )
        );
      }
    }
  };

  return (
    <DragDropContext onDragEnd={onDragEnd}>
      <div className="home-layout">
        {/* — Left Panel — */}
        <CourseList courses={courses} onSelectCourse={setSelectedCourse} />

        {/* — Middle Panel — */}
        <ScheduleViewer schedule={schedule} setSchedule={setSchedule} onSelectCourse={setSelectedCourse} />

        {/* — Right Panel (Course Details) — */}
        {selectedCourse && <CourseDetailPanel courseId={selectedCourse} onClose={() => setSelectedCourse(null)} />}
      </div>
    </DragDropContext>
  );
}
