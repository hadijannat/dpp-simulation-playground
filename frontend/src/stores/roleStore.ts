import { create } from "zustand";

interface RoleState {
  role: string;
  setRole: (role: string) => void;
}

export const useRoleStore = create<RoleState>((set) => ({
  role: "manufacturer",
  setRole: (role) => set({ role }),
}));
