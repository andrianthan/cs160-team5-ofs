import type { ApiResult } from "../api/client";

export type UserRole = "customer" | "employee" | "manager";
export type Portal = "customer" | "staff";

export type User = {
    id: number;
    email: string;
    name: string;
    role: UserRole;
};

export type AuthResult = ApiResult<User>;

export type AuthContextValue = {
    user: User | null | undefined;
    login: (email: string, password: string) => Promise<AuthResult>;
    register: (
        name: string,
        email: string,
        password: string,
    ) => Promise<AuthResult>;
    logout: () => Promise<void>;
    refresh: () => Promise<void>;
};
