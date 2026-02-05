import { useState } from "react";
import { useEDC } from "../../hooks/useEDC";

const negActions = ["request", "requested", "offer", "accept", "agree", "verify", "finalize", "terminate"] as const;
const transferActions = ["provision", "provisioned", "request", "requested", "start", "complete", "terminate"] as const;

export default function NegotiationFlow() {
  const {
    createNegotiation,
    advanceNegotiation: advanceNegotiationMutation,
    createTransfer,
    advanceTransfer: advanceTransferMutation,
  } = useEDC();
  const [state, setState] = useState<string>("");
  const [negotiationId, setNegotiationId] = useState<string>("");
  const [transferId, setTransferId] = useState<string>("");

  async function startNegotiation() {
    const data = await createNegotiation.mutateAsync({
      consumer_id: "BPNL000000000001",
      provider_id: "BPNL000000000002",
      asset_id: "asset-001",
      policy: { permission: [{ constraint: { leftOperand: "purpose", rightOperand: "dpp:simulation" } }] },
      purpose: "dpp:simulation",
    });
    setNegotiationId(data.id);
    setState(JSON.stringify(data, null, 2));
  }

  async function handleAdvanceNegotiation(action: string) {
    if (!negotiationId) return;
    const data = await advanceNegotiationMutation.mutateAsync({ id: negotiationId, action });
    setState(JSON.stringify(data, null, 2));
  }

  async function startTransfer() {
    const data = await createTransfer.mutateAsync({ asset_id: "asset-001" });
    setTransferId(data.id);
    setState(JSON.stringify(data, null, 2));
  }

  async function handleAdvanceTransfer(action: string) {
    if (!transferId) return;
    const data = await advanceTransferMutation.mutateAsync({ id: transferId, action });
    setState(JSON.stringify(data, null, 2));
  }

  return (
    <div>
      <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
        <button className="btn btn-primary" onClick={startNegotiation}>Start Negotiation</button>
        <button className="btn btn-secondary" onClick={startTransfer}>Start Transfer</button>
      </div>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 12 }}>
        {negActions.map((action) => (
          <button className="btn btn-secondary" key={action} onClick={() => handleAdvanceNegotiation(action)}>
            {action}
          </button>
        ))}
      </div>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 12 }}>
        {transferActions.map((action) => (
          <button className="btn btn-secondary" key={action} onClick={() => handleAdvanceTransfer(action)}>
            {action}
          </button>
        ))}
      </div>
      <pre className="mono-panel">{state}</pre>
    </div>
  );
}
