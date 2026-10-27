import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { authApi } from "./authApi";
import { AuthContext } from "./AuthContext";
import type { AuthContextValue, Portal, User } from "./types";

function belongsToPortal(user: User, portal: Portal) {
    return portal === "customer"
        ? user.role === "customer"
        : user.role === "employee" || user.role === "manager";
}

export default function AuthProvider({
    portal,
    children,
}: {
    portal: Portal;
    children: ReactNode;
}) {
    const [user, setUser] = useState<User | null | undefined>(undefined);

    const refresh = useCallback(async () => {
        const result = await authApi.currentUser();
        if (result.ok && belongsToPortal(result.data, portal)) {
            setUser(result.data);
        } else {
            setUser((current) =>
                result.ok || result.status === 401 || current === undefined
                    ? null
                    : current,
            );
        }
    }, [portal]);

    useEffect(() => {
        const initialCheck = window.setTimeout(() => void refresh(), 0);
        const onVisible = () => {
            if (document.visibilityState === "visible") void refresh();
        };
        const onExpired = () => setUser(null);

        document.addEventListener("visibilitychange", onVisible);
        window.addEventListener("auth:expired", onExpired);

        return () => {
            window.clearTimeout(initialCheck);
            document.removeEventListener("visibilitychange", onVisible);
            window.removeEventListener("auth:expired", onExpired);
        };
    }, [refresh]);

    const value = useMemo<AuthContextValue>(
        () => ({
            user,
            refresh,
            login: async (email, password) => {
                const result = await authApi.login(email, password, portal);
                if (result.ok) setUser(result.data);
                return result;
            },
            register: async (name, email, password) => {
                const result = await authApi.register(name, email, password);
                if (result.ok) setUser(result.data);
                return result;
            },
            logout: async () => {
                await authApi.logout();
                setUser(null);
            },
        }),
        [portal, refresh, user],
    );

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
