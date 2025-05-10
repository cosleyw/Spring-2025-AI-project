// src/App.jsx
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import './App.css';
import Home from './components/Home';
import Layout from './components/Layout';
import ScheduleGenerator from './components/ScheduleGenerator';
import { GeneratorConfigProvider } from './context/GeneratorConfigContext';
import { ScheduleProvider } from './context/ScheduleContext';

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
      <GeneratorConfigProvider>
        <BrowserRouter>
          <Layout>
            <AppRoutes />
          </Layout>
        </BrowserRouter>
      </GeneratorConfigProvider>
    </ScheduleProvider>
  );
}
