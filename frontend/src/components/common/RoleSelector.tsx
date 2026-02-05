import { useRoleStore } from "../../stores/roleStore";

const roles = ["manufacturer", "regulator", "consumer", "recycler", "developer", "admin"];

export default function RoleSelector() {
  const { role, setRole } = useRoleStore();
  return (
    <select value={role} onChange={(e) => setRole(e.target.value)} className="input" style={{ maxWidth: 180 }} aria-label="Select role">
      {roles.map((r) => (
        <option key={r} value={r}>
          {r}
        </option>
      ))}
    </select>
  );
}
