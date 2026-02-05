import { useMutation, useQuery } from "@tanstack/react-query";
import { apiGet, apiPost } from "../services/api";

export function useCompliance() {
  const checkCompliance = useMutation({
    mutationFn: (payload: Record<string, unknown>) => apiPost("/api/v1/compliance/check", payload),
  });

  const reports = useQuery({
    queryKey: ["compliance-reports"],
    queryFn: () => apiGet("/api/v1/reports"),
  });

  return { checkCompliance, reports };
}
