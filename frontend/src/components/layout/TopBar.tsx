import RoleSelector from "../common/RoleSelector";

export default function TopBar() {
  return (
    <header className="topbar">
      <div className="topbar-title">Simulation Playground</div>
      <RoleSelector />
    </header>
  );
}
