import ComplianceChecker from "../components/compliance/ComplianceChecker";
import AccessDenied from "../components/common/AccessDenied";
import { useHasRole } from "../hooks/useRoles";

export default function CompliancePage() {
  const allowed = useHasRole(["manufacturer", "regulator", "developer", "admin"]);
  if (!allowed) {
    return <AccessDenied />;
  }
  return (
    <div>
      <h1>Compliance</h1>
      <p>Run regulation checks and review violations in real time.</p>
      <ComplianceChecker />
    </div>
  );
}
