// src/components/Home.jsx
import React, { useState } from 'react';
import { DragDropContext }    from '@hello-pangea/dnd';
import { useNavigate }        from 'react-router-dom';
import { useCourses }         from '../hooks/useCourses';
import { useSchedule }        from '../context/ScheduleContext';
import CourseList             from './CourseList';
import ScheduleViewer         from './ScheduleViewer';
import CourseDetailPanel      from './CourseDetailPanel';
import './Home.css';

export default function Home() {
  const navigate = useNavigate();
  const { courses }            = useCourses();
  const { schedule, setSchedule } = useSchedule();
  const [selectedCourse, setSelectedCourse] = useState(null);

  const onDragEnd = result => {
    const { source, destination, draggableId } = result;
    if (!destination) return;

    // dragging from left panel into semester
    if (source.droppableId === 'courses' && destination.droppableId.startsWith('sem-')) {
      const semIdx = Number(destination.droppableId.split('-')[1]);
      setSchedule(sch =>
        sch.map((sem, i) =>
          i === semIdx
            ? { ...sem, courses: [...sem.courses, courses.find(c => c.id === draggableId)] }
            : sem
        )
      );
      return;
    }

    // dragging out of a semester
    if (source.droppableId.startsWith('sem-')) {
      const fromIdx = Number(source.droppableId.split('-')[1]);
      setSchedule(sch =>
        sch.map((sem, i) =>
          i === fromIdx
            ? { ...sem, courses: sem.courses.filter(c => c.id !== draggableId) }
            : sem
        )
      );

      // if dropped into another semester
      if (destination.droppableId.startsWith('sem-')) {
        const toIdx = Number(destination.droppableId.split('-')[1]);
        setSchedule(sch =>
          sch.map((sem, i) =>
            i === toIdx
              ? { ...sem, courses: [...sem.courses, courses.find(c => c.id === draggableId)] }
              : sem
          )
        );
      }
    }
  };

  // Regenerate From Here 
  const handleRegenerate = () => {
    
    navigate('/schedule/generate');
  };

  return (
    <DragDropContext onDragEnd={onDragEnd}>
      <div className="home-layout">
        {/* — Left Panel — */}
        <CourseList
          courses={courses}
          onRegenerate={handleRegenerate}
          onSelectCourse={setSelectedCourse}
        />

        {/* — Middle Panel — */}
        <ScheduleViewer
          schedule={schedule}
          setSchedule={setSchedule}
          onSelectCourse={setSelectedCourse}
        />

        {/* — Right Panel (Course Details) — */}
        {selectedCourse && (
          <CourseDetailPanel
            courseId={selectedCourse}
            onClose={() => setSelectedCourse(null)}
          />
        )}
      </div>
    </DragDropContext>
  );
}
