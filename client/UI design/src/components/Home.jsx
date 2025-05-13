// src/components/Home.jsx
import { DragDropContext } from '@hello-pangea/dnd';
import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useConfig } from '../context/GeneratorConfigContext';
import { useSchedule } from '../context/ScheduleContext';
import { useCourses } from '../hooks/useCourses';
import CourseDetailPanel from './CourseDetailPanel';
import CourseList from './CourseList';
import './Home.css';
import Layout from './Layout';
import ScheduleViewer from './ScheduleViewer';
import SettingsModal from './SettingsModal';

export default function Home() {
  const { courses } = useCourses();
  const { schedule, setSchedule } = useSchedule();
  const [selectedCourse, setSelectedCourse] = useState(null);
  const { form, setForm } = useConfig();
  const [showSettings, setShowSettings] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    if ((form.desired_degree_ids === null || form.desired_degree_ids.length === 0) && !showSettings) {
      navigate('/');
    }
  }, [form.desired_degree_ids, showSettings, navigate]);

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

      if (destination.droppableId === 'trash') {
        setForm((prev) => {
          return { ...prev, block_ids: [...prev['block_ids'], draggableId] };
        });
      }
    }
  };

  const handleSettingsToggle = (e) => {
    setShowSettings((prev) => !prev);
    e.preventDefault();
    return false;
  };

  const handleReset = (e) => {
    window.location.reload();
  };

  return (
    <Layout
      links={
        <>
          <Link to="/" onClick={handleReset}>
            Reset
          </Link>
          <Link to="settings" onClick={handleSettingsToggle}>
            Settings
          </Link>
        </>
      }
    >
      <SettingsModal isOpen={showSettings} onClose={() => setShowSettings(() => false)} />
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
    </Layout>
  );
}
