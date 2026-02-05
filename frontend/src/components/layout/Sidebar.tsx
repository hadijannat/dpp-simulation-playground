import { NavLink } from "react-router-dom";
import { useHasRole } from "../../hooks/useRoles";

export default function Sidebar() {
  const canCompliance = useHasRole(["manufacturer", "regulator", "developer", "admin"]);
  const canComplianceReports = useHasRole(["regulator", "developer", "admin"]);
  const canEdc = useHasRole(["developer", "manufacturer", "admin"]);
  const canGamification = useHasRole(["developer", "admin", "manufacturer", "consumer", "regulator", "recycler"]);

  return (
    <aside className="sidebar">
      <div className="sidebar-title">DPP Playground</div>
      <nav className="nav-group">
        <NavLink to="/" className="nav-link">Home</NavLink>
        <NavLink to="/journey" className="nav-link">Manufacturer Journey</NavLink>
        <NavLink to="/simulation" className="nav-link">Simulation</NavLink>
        <NavLink to="/simulation/sessions" className="nav-link">Sessions</NavLink>
        <NavLink to="/playground" className="nav-link">API Playground</NavLink>
        {canCompliance && <NavLink to="/compliance" className="nav-link">Compliance</NavLink>}
        {canComplianceReports && <NavLink to="/compliance/reports" className="nav-link">Compliance Reports</NavLink>}
        {canEdc && <NavLink to="/edc" className="nav-link">EDC</NavLink>}
      </nav>
      <nav className="nav-group">
        <NavLink to="/dashboard" className="nav-link">Dashboard</NavLink>
        {canGamification && <NavLink to="/gamification" className="nav-link">Gamification</NavLink>}
        <NavLink to="/achievements" className="nav-link">Achievements</NavLink>
        <NavLink to="/leaderboard" className="nav-link">Leaderboard</NavLink>
      </nav>
    </aside>
  );
}
