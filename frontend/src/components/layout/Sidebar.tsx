import { NavLink } from "react-router-dom";
import { useHasRole } from "../../hooks/useRoles";

export default function Sidebar() {
  const canCompliance = useHasRole(["manufacturer", "regulator", "developer", "admin"]);
  const canEdc = useHasRole(["developer", "manufacturer", "admin"]);

  return (
    <aside className="sidebar">
      <div className="sidebar-title">DPP Playground</div>
      <nav>
        <NavLink to="/" className="nav-link">Home</NavLink>
        <NavLink to="/simulation" className="nav-link">Simulation</NavLink>
        <NavLink to="/playground" className="nav-link">API Playground</NavLink>
        {canCompliance && <NavLink to="/compliance" className="nav-link">Compliance</NavLink>}
        {canEdc && <NavLink to="/edc" className="nav-link">EDC</NavLink>}
        <NavLink to="/dashboard" className="nav-link">Dashboard</NavLink>
        <NavLink to="/achievements" className="nav-link">Achievements</NavLink>
        <NavLink to="/leaderboard" className="nav-link">Leaderboard</NavLink>
      </nav>
    </aside>
  );
}
