import { create } from "zustand";
import type { EDCNegotiation, EDCTransfer } from "../types/api.types";

type EDCState = {
  lastNegotiation?: EDCNegotiation;
  lastTransfer?: EDCTransfer;
  setLastNegotiation: (negotiation: EDCNegotiation) => void;
  setLastTransfer: (transfer: EDCTransfer) => void;
};

export const useEdcStore = create<EDCState>((set) => ({
  lastNegotiation: undefined,
  lastTransfer: undefined,
  setLastNegotiation: (negotiation) => set({ lastNegotiation: negotiation }),
  setLastTransfer: (transfer) => set({ lastTransfer: transfer }),
}));
