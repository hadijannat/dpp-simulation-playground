import NegotiationFlow from "../components/edc/NegotiationFlow";
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
      <NegotiationFlow />
    </div>
  );
}
