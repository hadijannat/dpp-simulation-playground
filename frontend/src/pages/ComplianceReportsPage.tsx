import { useCompliance } from "../hooks/useCompliance";
import { useComplianceStore } from "../stores/complianceStore";

export default function ComplianceReportsPage() {
  const { data, error, isLoading } = useCompliance().reports;
  const storedReports = useComplianceStore((state) => state.reports);
  const items = data?.reports ?? storedReports;

  return (
    <div className="page">
      <h2>Compliance Reports</h2>
      {isLoading && <div>Loading reports...</div>}
      {error && <div className="error">Failed to load reports.</div>}
      {!isLoading && items.length === 0 && <div>No reports available.</div>}
      {items.length > 0 && (
        <table className="table">
          <thead>
            <tr>
              <th>Report ID</th>
              <th>Status</th>
              <th>Story</th>
              <th>Regulations</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {items.map((report) => (
              <tr key={report.id}>
                <td>{report.id}</td>
                <td>{report.status}</td>
                <td>{report.story_code ?? "-"}</td>
                <td>{report.regulations?.join(", ") ?? "-"}</td>
                <td>{report.created_at ?? "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
