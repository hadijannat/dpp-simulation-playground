import { useAuth } from "./useAuth";
import { useRoleStore } from "../stores/roleStore";

export function useRoles() {
  const { user } = useAuth();
  const { role } = useRoleStore();
  if (!user) {
    return [role];
  }
  const roles = (user as any)?.realm_access?.roles || [];
  return roles as string[];
}

export function useHasRole(allowed: string[]) {
  const roles = useRoles();
  return roles.some((r) => allowed.includes(r));
}
