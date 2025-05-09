// src/context/GeneratorConfigContext.jsx
import { createContext, useContext, useState } from 'react';

const ConfigContext       = createContext();
const SetConfigContext    = createContext();

export function GeneratorConfigProvider({ children }) {
  const [config, setConfig] = useState(null);
  return (
    <ConfigContext.Provider value={config}>
      <SetConfigContext.Provider value={setConfig}>
        {children}
      </SetConfigContext.Provider>
    </ConfigContext.Provider>
  );
}

export function useGeneratorConfig() {
  return useContext(ConfigContext);
}

export function useSetGeneratorConfig() {
  return useContext(SetConfigContext);
}
