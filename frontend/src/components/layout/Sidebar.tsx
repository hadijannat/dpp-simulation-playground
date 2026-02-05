import { NavLink } from "react-router-dom";

const links = [
  { to: "/", label: "Home" },
  { to: "/simulation", label: "Simulation" },
  { to: "/playground", label: "API Playground" },
  { to: "/compliance", label: "Compliance" },
  { to: "/edc", label: "EDC" },
  { to: "/dashboard", label: "Dashboard" },
  { to: "/achievements", label: "Achievements" },
  { to: "/leaderboard", label: "Leaderboard" },
];

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-title">DPP Playground</div>
      <nav>
        {links.map((link) => (
          <NavLink key={link.to} to={link.to} className="nav-link">
            {link.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
