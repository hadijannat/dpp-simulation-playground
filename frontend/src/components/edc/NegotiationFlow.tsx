import { useState } from "react";
import { apiPost } from "../../services/api";

export default function NegotiationFlow() {
  const [state, setState] = useState<string>("");

  async function start() {
    const data = await apiPost("/api/v1/edc/negotiations", {
      consumer_id: "BPNL000000000001",
      provider_id: "BPNL000000000002",
      asset_id: "asset-001",
      policy: { "@type": "odrl:Offer" },
    });
    setState(JSON.stringify(data, null, 2));
  }

  return (
    <div>
      <button onClick={start}>Start Negotiation</button>
      <pre>{state}</pre>
    </div>
  );
}
