import { create } from "zustand";

type EDCState = {
  lastNegotiation?: Record<string, unknown>;
  lastTransfer?: Record<string, unknown>;
  setLastNegotiation: (negotiation: Record<string, unknown>) => void;
  setLastTransfer: (transfer: Record<string, unknown>) => void;
};

export const useEdcStore = create<EDCState>((set) => ({
  lastNegotiation: undefined,
  lastTransfer: undefined,
  setLastNegotiation: (negotiation) => set({ lastNegotiation: negotiation }),
  setLastTransfer: (transfer) => set({ lastTransfer: transfer }),
}));
