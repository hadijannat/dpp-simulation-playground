import { useState } from "react";
import { API_BASE } from "../../config/endpoints";

export default function NegotiationFlow() {
  const [state, setState] = useState<string>("");

  async function start() {
    const res = await fetch(`${API_BASE}/api/v1/edc/negotiations`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        consumer_id: "BPNL000000000001",
        provider_id: "BPNL000000000002",
        asset_id: "asset-001",
        policy: { "@type": "odrl:Offer" },
      }),
    });
    const data = await res.json();
    setState(JSON.stringify(data, null, 2));
  }

  return (
    <div>
      <button onClick={start}>Start Negotiation</button>
      <pre>{state}</pre>
    </div>
  );
}
