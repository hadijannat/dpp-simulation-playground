import NegotiationFlow from "../components/edc/NegotiationFlow";
import CatalogBrowser from "../components/edc/CatalogBrowser";
import PolicyEditor from "../components/edc/PolicyEditor";
import AccessDenied from "../components/common/AccessDenied";
import { useHasRole } from "../hooks/useRoles";

export default function EDCSimulatorPage() {
  const allowed = useHasRole(["developer", "manufacturer", "admin"]);
  if (!allowed) {
    return <AccessDenied />;
  }
  return (
    <div>
      <h1>EDC Simulator</h1>
      <p>Simulate policy negotiation and data transfers with DSP state machines.</p>
      <div className="grid-2">
        <CatalogBrowser />
        <PolicyEditor />
      </div>
      <div style={{ marginTop: 16 }}>
        <NegotiationFlow />
      </div>
    </div>
  );
}
