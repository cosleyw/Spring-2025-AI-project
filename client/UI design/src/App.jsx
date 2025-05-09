// src/App.jsx
import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { DragDropContext, Droppable, Draggable } from '@hello-pangea/dnd';
import { ScheduleProvider }             from './context/ScheduleContext';
import { useCourses }                   from './hooks/useCourses';
import Layout                           from './components/Layout';
import ScheduleGenerator                from './components/ScheduleGenerator';
import Home                             from './components/Home';
import './App.css';

function AppRoutes() {
  // keep your existing hook for courses + onDragEnd
  const { onDragEnd } = useCourses();

  return (
    <Routes>
      {/* standalone generator screen */}
      <Route path="/schedule/generate" element={<ScheduleGenerator />} />

      {/* every other route lives inside a DragDropContext + Home */}
      <Route
        path="/*"
        element={
          <DragDropContext onDragEnd={onDragEnd}>
            <Home />
          </DragDropContext>
        }
      />
    </Routes>
  );
}

export default function App() {
  return (
    <ScheduleProvider>
      <BrowserRouter>
        <Layout>
          <AppRoutes />
        </Layout>
      </BrowserRouter>
    </ScheduleProvider>
  );
}
