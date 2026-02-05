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
          <span>Auth...</span>
        ) : authenticated ? (
          <button onClick={logout}>Logout</button>
        ) : (
          <button onClick={login}>Login</button>
        )}
      </div>
    </header>
  );
}
