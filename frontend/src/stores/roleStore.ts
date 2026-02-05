import { create } from "zustand";

interface RoleState {
  role: string;
  setRole: (role: string) => void;
}

const STORAGE_KEY = "dpp-role";

export const useRoleStore = create<RoleState>((set) => ({
  role: localStorage.getItem(STORAGE_KEY) || "manufacturer",
  setRole: (role) => {
    localStorage.setItem(STORAGE_KEY, role);
    set({ role });
  },
}));

export function getSelectedRole() {
  return useRoleStore.getState().role;
}
