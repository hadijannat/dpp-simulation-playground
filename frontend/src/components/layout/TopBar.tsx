import RoleSelector from "../common/RoleSelector";
import { useAuth } from "../../hooks/useAuth";

export default function TopBar() {
  const { initialized, authenticated, login, logout } = useAuth();

  return (
    <header className="topbar">
      <div className="topbar-title">Simulation Playground</div>
      <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
        <RoleSelector />
        {!initialized ? (
          <span className="pill">Auth...</span>
        ) : authenticated ? (
          <button className="btn btn-secondary" onClick={logout}>Logout</button>
        ) : (
          <button className="btn btn-primary" onClick={login}>Login</button>
        )}
      </div>
    </header>
  );
}
