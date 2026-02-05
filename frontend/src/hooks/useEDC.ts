import { useMutation, useQuery } from "@tanstack/react-query";
import { apiGet, apiPost } from "../services/api";

export function useEDC() {
  const catalog = useQuery({
    queryKey: ["edc-catalog"],
    queryFn: () => apiGet("/api/v1/edc/catalog"),
  });

  const participants = useQuery({
    queryKey: ["edc-participants"],
    queryFn: () => apiGet("/api/v1/edc/participants"),
  });

  const assets = useQuery({
    queryKey: ["edc-assets"],
    queryFn: () => apiGet("/api/v1/edc/assets"),
  });

  const createNegotiation = useMutation({
    mutationFn: (payload: Record<string, unknown>) => apiPost("/api/v1/edc/negotiations", payload),
  });

  const advanceNegotiation = useMutation({
    mutationFn: (payload: { id: string; action: string }) =>
      apiPost(`/api/v1/edc/negotiations/${payload.id}/${payload.action}`, {}),
  });

  const createTransfer = useMutation({
    mutationFn: (payload: Record<string, unknown>) => apiPost("/api/v1/edc/transfers", payload),
  });

  const advanceTransfer = useMutation({
    mutationFn: (payload: { id: string; action: string }) =>
      apiPost(`/api/v1/edc/transfers/${payload.id}/${payload.action}`, {}),
  });

  return {
    catalog,
    participants,
    assets,
    createNegotiation,
    advanceNegotiation,
    createTransfer,
    advanceTransfer,
  };
}
