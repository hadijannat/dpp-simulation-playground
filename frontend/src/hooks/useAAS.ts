import { useMutation, useQuery } from "@tanstack/react-query";
import { apiGet, apiPost } from "../services/api";

export function useAAS() {
  const shells = useQuery({
    queryKey: ["aas-shells"],
    queryFn: () => apiGet("/api/v1/aas/shells"),
  });

  const createShell = useMutation({
    mutationFn: (payload: Record<string, unknown>) => apiPost("/api/v1/aas/shells", payload),
  });

  const createSubmodel = useMutation({
    mutationFn: (payload: Record<string, unknown>) => apiPost("/api/v1/aas/submodels", payload),
  });

  const uploadAasx = useMutation({
    mutationFn: (payload: Record<string, unknown>) => apiPost("/api/v1/aasx/upload", payload),
  });

  return { shells, createShell, createSubmodel, uploadAasx };
}
