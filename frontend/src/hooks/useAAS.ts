import { useMutation, useQuery } from "@tanstack/react-query";
import { apiGet, apiPost } from "../services/api";
import type {
  AasShellCreateResponse,
  AasShellListResponse,
  AasSubmodelCreateResponse,
  AasxUploadResponse,
} from "../types/api.types";

export function useAAS() {
  const shells = useQuery({
    queryKey: ["aas-shells"],
    queryFn: () => apiGet<AasShellListResponse>("/api/v2/aas/shells"),
  });

  const createShell = useMutation({
    mutationFn: (payload: Record<string, unknown>) =>
      apiPost<AasShellCreateResponse>("/api/v2/aas/shells", payload),
  });

  const createSubmodel = useMutation({
    mutationFn: (payload: Record<string, unknown>) =>
      apiPost<AasSubmodelCreateResponse>("/api/v2/aas/submodels", payload),
  });

  const uploadAasx = useMutation({
    mutationFn: (payload: Record<string, unknown>) => apiPost<AasxUploadResponse>("/api/v2/aasx/upload", payload),
  });

  return { shells, createShell, createSubmodel, uploadAasx };
}
