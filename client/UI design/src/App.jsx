import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { DragDropContext }              from 'react-beautiful-dnd';
import { useCourses }                   from './hooks/useCourses';
import Layout                           from './components/Layout';
import CourseList                       from './components/CourseList';
import ScheduleViewer                   from './components/ScheduleViewer';
import CourseDetails                    from './components/CourseDetails';
import ScheduleGenerator                from './components/ScheduleGenerator';
import DegreeBrowser                    from './components/DegreeBrowser';
import './App.css';

export default function App() {
  const { courses, schedule, onDragEnd } = useCourses();

  const masterLayout = rightPanel => (
    <div className="app-layout">
      <CourseList courses={courses} />
      <ScheduleViewer schedule={schedule} />
      <div className="right-panel">{rightPanel}</div>
    </div>
  );

  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          {/* Stand‐alone generate page (no CourseList/ScheduleViewer) */}
          <Route path="/schedule/generate" element={<ScheduleGenerator />} />

          {/* All the rest live inside a DragDropContext */}
          <Route
            path="/*"
            element={
              <DragDropContext onDragEnd={onDragEnd}>
                <Routes>
                  <Route index element={masterLayout(<h3>Select a course…</h3>)} />
                  <Route path="courses/:id" element={masterLayout(<CourseDetails />)} />
                  <Route path="degrees"     element={masterLayout(<DegreeBrowser />)} />
                </Routes>
              </DragDropContext>
            }
          />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}
