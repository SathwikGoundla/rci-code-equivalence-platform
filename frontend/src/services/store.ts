import { create } from 'zustand';

interface Project {
  id: string;
  name: string;
  description: string;
}

interface AppStore {
  activeProject: Project | null;
  setActiveProject: (project: Project | null) => void;
}

export const useAppStore = create<AppStore>((set) => ({
  activeProject: null,
  setActiveProject: (project) => set({ activeProject: project }),
}));
