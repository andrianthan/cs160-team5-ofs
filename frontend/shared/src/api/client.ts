export type ApiError = {
    message: string;
    error?: string;
};

export type ApiResult<T> =
    | { ok: true; status: number; data: T }
    | { ok: false; status: number; data: ApiError };

function readError(data: unknown, status: number): ApiError {
    const body =
        typeof data === "object" && data !== null
            ? (data as Record<string, unknown>)
            : {};
    const error = typeof body.error === "string" ? body.error : undefined;
    const message =
        typeof body.message === "string"
            ? body.message
            : error ??
              (status >= 500
                  ? "Something went wrong on the server. Try again."
                  : "Request failed.");

    return { message, error };
}

export async function apiRequest<T>(
    url: string,
    options: RequestInit = {},
): Promise<ApiResult<T>> {
    try {
        const response = await fetch(url, {
            credentials: "include",
            ...options,
        });
        const data: unknown = await response.json().catch(() => ({}));

        if (!response.ok) {
            return {
                ok: false,
                status: response.status,
                data: readError(data, response.status),
            };
        }

        return { ok: true, status: response.status, data: data as T };
    } catch {
        return {
            ok: false,
            status: 0,
            data: { message: "Cannot reach the server." },
        };
    }
}

export function jsonRequest(method: string, body?: unknown): RequestInit {
    return {
        method,
        headers: body === undefined ? undefined : { "Content-Type": "application/json" },
        body: body === undefined ? undefined : JSON.stringify(body),
    };
}
