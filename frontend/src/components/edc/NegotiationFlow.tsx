import { useState } from "react";
import { apiPost } from "../../services/api";

const negActions = ["request", "requested", "offer", "accept", "agree", "verify", "finalize", "terminate"] as const;
const transferActions = ["provision", "provisioned", "request", "requested", "start", "complete", "terminate"] as const;

export default function NegotiationFlow() {
  const [state, setState] = useState<string>("");
  const [negotiationId, setNegotiationId] = useState<string>("");
  const [transferId, setTransferId] = useState<string>("");

  async function startNegotiation() {
    const data = await apiPost("/api/v1/edc/negotiations", {
      consumer_id: "BPNL000000000001",
      provider_id: "BPNL000000000002",
      asset_id: "asset-001",
      policy: { "@type": "odrl:Offer" },
    });
    setNegotiationId(data.id);
    setState(JSON.stringify(data, null, 2));
  }

  async function advanceNegotiation(action: string) {
    if (!negotiationId) return;
    const data = await apiPost(`/api/v1/edc/negotiations/${negotiationId}/${action}`, {});
    setState(JSON.stringify(data, null, 2));
  }

  async function startTransfer() {
    const data = await apiPost("/api/v1/edc/transfers", { asset_id: "asset-001" });
    setTransferId(data.id);
    setState(JSON.stringify(data, null, 2));
  }

  async function advanceTransfer(action: string) {
    if (!transferId) return;
    const data = await apiPost(`/api/v1/edc/transfers/${transferId}/${action}`, {});
    setState(JSON.stringify(data, null, 2));
  }

  return (
    <div>
      <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
        <button onClick={startNegotiation}>Start Negotiation</button>
        <button onClick={startTransfer}>Start Transfer</button>
      </div>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 12 }}>
        {negActions.map((action) => (
          <button key={action} onClick={() => advanceNegotiation(action)}>
            {action}
          </button>
        ))}
      </div>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 12 }}>
        {transferActions.map((action) => (
          <button key={action} onClick={() => advanceTransfer(action)}>
            {action}
          </button>
        ))}
      </div>
      <pre>{state}</pre>
    </div>
  );
}
