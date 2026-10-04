import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

export type User = {
    id: number;
    email: string;
    name: string;
    role: "customer" | "employee" | "manager";
};

type CallResult<T> =
    | { ok: true; status: number; data: T }
    | { ok: false; status: number; data: { message?: string; error?: string } };

type AuthContextValue = {
    user: User | null | undefined; // undefined = still checking, null = signed out
    login: (email: string, password: string) => Promise<CallResult<User>>;
    register: (name: string, email: string, password: string) => Promise<CallResult<User>>;
    logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

async function call<T>(path : string, method: string, body?: Record<string, unknown>): Promise<CallResult<T>>  {
    try {
        const res = await fetch(`/api/auth/${path}`, {
            method,
            headers: body ? {"Content-Type": "application/json"} : undefined,
            body: body ? JSON.stringify(body) : undefined,
        })
        
        if ([502, 503, 504].includes(res.status)) {
            return { ok: false, status: res.status, data: { message: "Cannot reach the server." } };
        }

        const data = await res.json().catch(() => ({}));

        if (res.ok) {
            return {
                ok: true,
                status: res.status,
                data: data as T,
            }
        }

        return {
            ok: false,
            status: res.status,
            data: {
                ...data,
                message: data.message ?? (res.status >= 500 ? "Something went wrong on the server. Try again." : "Request failed."),
            }
        }
    } catch {
        return {
            ok: false,
            status: 0,
            data: {message: "Cannot reach the server."},
        }
    }
}

type AuthProviderProps = {
    portal: "customer" | "staff";
    children: ReactNode;
};

export function AuthProvider({portal, children}: AuthProviderProps) {
    const [user, setUser] = useState<User | undefined | null>(undefined);

    useEffect(() => {

        // check if logged in (call /api/me/)
        const refresh = () => {
            call<User>("me", "GET").then((r) => {
                if (r.ok) {
                    setUser(r.data);
                } else if (r.status == 401) {
                    setUser(null);
                } else {
                    setUser((u) => (u === undefined ? null : u));
                }
            });
        };

        const onVisible = () => {
            if (document.visibilityState === "visible") {
                refresh();
            } 
        };

        const onExpired = () => {
            setUser(null);
        };

        refresh();

        document.addEventListener("visibilitychange", onVisible);
        window.addEventListener("auth:expired", onExpired);

        return () => {
            document.removeEventListener("visibilitychange", onVisible);
            window.removeEventListener("auth:expired", onExpired);
        };
    }, []);

    const signIn = async (path: string, body: Record<string, unknown>) => {
        const r = await call<User>(path, "POST", body);
        if (r.ok) setUser(r.data);
        return r;
    };

    const value: AuthContextValue = {
        user,
        login: (email, password) => signIn("login", { email, password, portal }),
        register: (name, email, password) => signIn("register", { name, email, password }),
        logout: async () => {
            await call<unknown>("logout", "POST");
            setUser(null);
        },
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}


export function useAuth(): AuthContextValue {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
    return ctx;
}
