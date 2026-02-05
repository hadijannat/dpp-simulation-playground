import { useSessionStore } from "../stores/sessionStore";

export default function SimulationSessionsPage() {
  const sessions = useSessionStore((state) => state.sessions);
  const currentSession = useSessionStore((state) => state.currentSession);

  return (
    <div className="page">
      <h2>Simulation Sessions</h2>
      {currentSession && (
        <div className="card">
          <h3>Current Session</h3>
          <div>Session ID: {currentSession.id}</div>
          <div>Role: {currentSession.role}</div>
          <div>Started: {currentSession.created_at ?? "-"}</div>
        </div>
      )}
      <div className="card">
        <h3>Recent Sessions</h3>
        {sessions.length === 0 && <div>No sessions tracked locally yet.</div>}
        {sessions.length > 0 && (
          <table className="table">
            <thead>
              <tr>
                <th>Session ID</th>
                <th>Role</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {sessions.map((session) => (
                <tr key={session.id}>
                  <td>{session.id}</td>
                  <td>{session.role}</td>
                  <td>{session.created_at ?? "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
