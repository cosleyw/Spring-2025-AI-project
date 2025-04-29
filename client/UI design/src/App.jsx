// src/App.jsx
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

function AppContent() {
  const { courses, schedule, onDragEnd } = useCourses();

  const masterLayout = rightPanel => (
    <div className="app-layout">
      <CourseList courses={courses} />
      <ScheduleViewer schedule={schedule} />
      {rightPanel}
    </div>
  );

  return (
    <DragDropContext onDragEnd={onDragEnd}>
      <Layout>
        <Routes>
          <Route
            path="/"
            element={masterLayout(<div className="right-panel"><h3>Select a course…</h3></div>)}
          />
          <Route
            path="/courses/:id"
            element={masterLayout(<CourseDetails />)}
          />
          <Route path="/schedule/generate" element={<ScheduleGenerator />} />
          <Route path="/degrees"             element={<DegreeBrowser   />} />
        </Routes>
      </Layout>
    </DragDropContext>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}
