import { create } from 'zustand';

interface UnitState {
  unitSystem: 'field' | 'metric';
  toggleUnitSystem: () => void;
  setUnitSystem: (system: 'field' | 'metric') => void;
}

export const useUnitStore = create<UnitState>((set) => ({
  unitSystem: 'field',
  toggleUnitSystem: () => set((state) => ({
    unitSystem: state.unitSystem === 'field' ? 'metric' : 'field'
  })),
  setUnitSystem: (system) => set({ unitSystem: system }),
}));
