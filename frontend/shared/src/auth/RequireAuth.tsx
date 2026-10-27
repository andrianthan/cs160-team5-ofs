import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "./useAuth";
import type { UserRole } from "./types";

export default function RequireAuth({
    children,
    roles,
}: {
    children: ReactNode;
    roles?: UserRole[];
}) {
    const { user } = useAuth();
    const location = useLocation();

    if (user === undefined) return null;
    if (!user) {
        return (
            <Navigate
                to="/login"
                replace
                state={{ from: location.pathname }}
            />
        );
    }
    if (roles && !roles.includes(user.role)) {
        return <Navigate to="/login" replace />;
    }

    return <>{children}</>;
}
