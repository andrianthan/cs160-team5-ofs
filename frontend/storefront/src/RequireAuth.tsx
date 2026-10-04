import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "./AuthContext";

// Wrap any page that needs an account. Signed-out visitors go to /login and are
// sent back here after signing in.
export default function RequireAuth({ children }: { children: ReactNode }) {
    const { user } = useAuth();
    const location = useLocation();
    if (user === undefined) return null; // still checking /api/auth/me
    if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
    return (
        <>{children}</>
    );
}