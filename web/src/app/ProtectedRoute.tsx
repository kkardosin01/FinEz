import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { useMe } from "@/features/auth/hooks";

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { data: me, isLoading } = useMe();

  if (isLoading) {
    return <div className="flex min-h-screen items-center justify-center text-fg-secondary">carregando...</div>;
  }
  if (!me) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}
