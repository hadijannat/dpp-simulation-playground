import { useMutation, useQuery } from "@tanstack/react-query";
import { useEffect } from "react";
import {
  checkCompliance as checkComplianceRequest,
  listReports,
} from "../services/complianceService";
import { useComplianceStore } from "../stores/complianceStore";

export function useCompliance() {
  const setReports = useComplianceStore((state) => state.setReports);

  const checkCompliance = useMutation({
    mutationFn: (payload: Record<string, unknown>) => checkComplianceRequest(payload),
  });

  const reports = useQuery({
    queryKey: ["compliance-reports"],
    queryFn: () => listReports(),
  });

  useEffect(() => {
    if (reports.data?.reports) {
      setReports(reports.data.reports);
    }
  }, [reports.data, setReports]);

  return { checkCompliance, reports };
}
