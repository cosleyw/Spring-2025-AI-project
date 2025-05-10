// src/context/GeneratorConfigContext.jsx
import { createContext, useContext, useState } from 'react';

const ConfigContext = createContext();

export function GeneratorConfigProvider({ children }) {
  const [form, setForm] = useState({
    desired_degree_ids: [],
    semester_count: 8,
    start_term: 'Fall',
    start_year: new Date().getFullYear(),
    min_credit_per_semester: 12,
    max_credit_per_semester: 18,
    transfer_ids: [],
    block_ids: [],
    soph_semester: 3,
    jr_semester: 5,
    sr_semester: 7,
    desired_ids: [],
  });
  return <ConfigContext.Provider value={{ form, setForm }}>{children}</ConfigContext.Provider>;
}

export const useConfig = () => useContext(ConfigContext);
