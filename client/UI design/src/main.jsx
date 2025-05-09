// src/main.jsx (or index.jsx)

import { StrictMode }    from 'react'
import { createRoot }    from 'react-dom/client'
import './index.css'
import App               from './App.jsx'
import { ScheduleProvider } from './context/ScheduleContext'  // ← import your provider

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ScheduleProvider>       {/* ← wrap here */}
      <App />
    </ScheduleProvider>
  </StrictMode>,
)
