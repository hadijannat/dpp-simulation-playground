import { Navigate } from "react-router-dom";
import AccessDenied from "./AccessDenied";
import { useAuth } from "../../hooks/useAuth";
import { useHasRole } from "../../hooks/useRoles";

interface GuardProps {
  roles?: string[];
  children: React.ReactNode;
}

export default function RouteGuard({ roles, children }: GuardProps) {
  const { initialized, authenticated } = useAuth();
  const allowed = roles ? useHasRole(roles) : true;

  if (!initialized) {
    return <div>Loading...</div>;
  }
  if (!authenticated) {
    return <Navigate to="/login" replace />;
  }
  if (!allowed) {
    return <AccessDenied />;
  }
  return <>{children}</>;
}
