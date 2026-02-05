import { Navigate } from "react-router-dom";
import AccessDenied from "./AccessDenied";
import { useAuth } from "../../hooks/useAuth";
import { useHasRole } from "../../hooks/useRoles";
import { useRoleStore } from "../../stores/roleStore";

interface GuardProps {
  roles?: string[];
  children: React.ReactNode;
}

export default function RouteGuard({ roles, children }: GuardProps) {
  const { initialized, authenticated } = useAuth();
  const allowed = useHasRole(roles ?? []);
  const { role } = useRoleStore();
  const authMode = import.meta.env.VITE_AUTH_MODE || "auto";
  const allowBypass = authMode !== "keycloak";

  if (!initialized) {
    return <div>Loading...</div>;
  }
  if (!authenticated) {
    if (allowBypass) {
      if (roles && !roles.includes(role)) {
        return <AccessDenied />;
      }
      return <>{children}</>;
    }
    return <Navigate to="/login" replace />;
  }
  if (roles && !allowed) {
    return <AccessDenied />;
  }
  return <>{children}</>;
}
