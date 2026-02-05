import { useMutation, useQuery } from "@tanstack/react-query";
import {
  advanceNegotiation as advanceNegotiationRequest,
  advanceTransfer as advanceTransferRequest,
  createNegotiation as createNegotiationRequest,
  createTransfer as createTransferRequest,
  getAssets,
  getCatalog,
  getParticipants,
  type NegotiationCreatePayload,
  type TransferCreatePayload,
} from "../services/edcService";
import { useEdcStore } from "../stores/edcStore";

export function useEDC() {
  const setLastNegotiation = useEdcStore((state) => state.setLastNegotiation);
  const setLastTransfer = useEdcStore((state) => state.setLastTransfer);
  const catalog = useQuery({
    queryKey: ["edc-catalog"],
    queryFn: () => getCatalog(),
  });

  const participants = useQuery({
    queryKey: ["edc-participants"],
    queryFn: () => getParticipants(),
  });

  const assets = useQuery({
    queryKey: ["edc-assets"],
    queryFn: () => getAssets(),
  });

  const createNegotiation = useMutation({
    mutationFn: (payload: NegotiationCreatePayload) => createNegotiationRequest(payload),
    onSuccess: (data) => setLastNegotiation(data),
  });

  const advanceNegotiation = useMutation({
    mutationFn: (payload: { id: string; action: string }) =>
      advanceNegotiationRequest(payload.id, payload.action),
    onSuccess: (data) => setLastNegotiation(data),
  });

  const createTransfer = useMutation({
    mutationFn: (payload: TransferCreatePayload) => createTransferRequest(payload),
    onSuccess: (data) => setLastTransfer(data),
  });

  const advanceTransfer = useMutation({
    mutationFn: (payload: { id: string; action: string }) =>
      advanceTransferRequest(payload.id, payload.action),
    onSuccess: (data) => setLastTransfer(data),
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
