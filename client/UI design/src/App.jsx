// src/App.jsx
import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ScheduleProvider } from './context/ScheduleContext';
import Layout from './components/Layout';
import ScheduleGenerator from './components/ScheduleGenerator';
import Home from './components/Home';
import './App.css';

function AppRoutes() {
  return (
    <Routes>
      <Route path="/schedule/generate" element={<ScheduleGenerator />} />
      <Route path="/*" element={<Home />} />
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
