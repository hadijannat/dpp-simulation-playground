import { useRoleStore } from "../../stores/roleStore";

const roles = ["manufacturer", "regulator", "consumer", "recycler", "developer"];

export default function RoleSelector() {
  const { role, setRole } = useRoleStore();
  return (
    <select value={role} onChange={(e) => setRole(e.target.value)}>
      {roles.map((r) => (
        <option key={r} value={r}>
          {r}
        </option>
      ))}
    </select>
  );
}
