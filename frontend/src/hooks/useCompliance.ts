import { useMutation, useQuery } from "@tanstack/react-query";
import { checkCompliance, listReports } from "../services/complianceService";
import { useComplianceStore } from "../stores/complianceStore";

export function useCompliance() {
  const setReports = useComplianceStore((state) => state.setReports);

  const checkCompliance = useMutation({
    mutationFn: (payload: Record<string, unknown>) => checkCompliance(payload),
  });

  const reports = useQuery({
    queryKey: ["compliance-reports"],
    queryFn: () => listReports(),
    onSuccess: (data) => {
      if (data?.reports) {
        setReports(data.reports);
      }
    },
  });

  return { checkCompliance, reports };
}
