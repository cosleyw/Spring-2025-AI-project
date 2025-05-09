// src/context/ScheduleContext.jsx
import React, { createContext, useContext, useState } from 'react';

const ScheduleContext = createContext();

// Initialize with 8 empty semesters
const makeEmptySchedule = () =>
  Array.from({ length: 8 }, (_, i) => ({
    name:     `Semester ${i + 1}`,
    term:     '',
    year:     '',
    courses:  []
  }));

export function ScheduleProvider({ children }) {
  const [schedule, setSchedule] = useState(makeEmptySchedule());
  return (
    <ScheduleContext.Provider value={{ schedule, setSchedule }}>
      {children}
    </ScheduleContext.Provider>
  );
}

export function useSchedule() {
  const ctx = useContext(ScheduleContext);
  if (!ctx) throw new Error('useSchedule must be inside ScheduleProvider');
  return ctx;
}
