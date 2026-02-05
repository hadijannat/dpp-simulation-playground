import { create } from "zustand";
import type { ComplianceReportSummary } from "../types/api.types";

type ComplianceState = {
  reports: ComplianceReportSummary[];
  setReports: (reports: ComplianceReportSummary[]) => void;
};

export const useComplianceStore = create<ComplianceState>((set) => ({
  reports: [],
  setReports: (reports) => set({ reports }),
}));
