const roleDescriptions: Record<string, string> = {
  manufacturer: "Create and maintain DPPs, manage submodels, and publish AASX packages.",
  regulator: "Validate compliance reports, audit data, and review policy conformance.",
  consumer: "Access verified product information and sustainability insights.",
  recycler: "Access end-of-life data and dismantling guidance for recovery.",
  developer: "Exercise APIs, simulate integrations, and validate DPP flows.",
  admin: "Oversee roles, governance, and system health.",
};

export default function RoleOnboarding({ role }: { role: string }) {
  return (
    <div className="card-subtle">
      <div className="section-title">
        <h3>Role Onboarding</h3>
        <span className="pill">{role}</span>
      </div>
      <p>{roleDescriptions[role] || "Select a role to view guidance."}</p>
    </div>
  );
}
