import { apiRequest, jsonRequest } from "../api/client";
import type { Portal, User } from "./types";

const AUTH_URL = "/api/auth";

export const authApi = {
    currentUser: () => apiRequest<User>(`${AUTH_URL}/me`),
    login: (email: string, password: string, portal: Portal) =>
        apiRequest<User>(
            `${AUTH_URL}/login`,
            jsonRequest("POST", { email, password, portal }),
        ),
    register: (name: string, email: string, password: string) =>
        apiRequest<User>(
            `${AUTH_URL}/register`,
            jsonRequest("POST", { name, email, password }),
        ),
    logout: () =>
        apiRequest<unknown>(`${AUTH_URL}/logout`, jsonRequest("POST")),
};
