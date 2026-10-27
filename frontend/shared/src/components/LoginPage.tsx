import { useState, type ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../auth/useAuth";
import FormError from "./FormError";
import FormField from "./FormField";

export default function LoginPage({
    title,
    subtitle,
    defaultRedirect,
    footer,
}: {
    title: string;
    subtitle?: string;
    defaultRedirect: string;
    footer?: ReactNode;
}) {
    const { user, login } = useAuth();
    const location = useLocation();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState<string | null>(null);

    if (user === undefined) return null;
    if (user) {
        const destination =
            (location.state as { from?: string } | null)?.from ??
            defaultRedirect;
        return <Navigate to={destination} replace />;
    }

    const submit = async (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        setBusy(true);
        setError(null);
        const result = await login(email, password);
        if (!result.ok) setError(result.data.message);
        setBusy(false);
    };

    return (
        <main className="mx-auto mt-8 max-w-sm px-4">
            <div className="mb-6 text-center">
                <h1 className="font-display text-2xl font-bold">{title}</h1>
                {subtitle && (
                    <p className="mt-1 text-sm text-brand-900/60">
                        {subtitle}
                    </p>
                )}
            </div>
            <form
                className="space-y-4 rounded-3xl border border-brand-100 bg-white p-6 shadow-sm shadow-brand-900/5"
                onSubmit={submit}
            >
                <FormField
                    id="login-email"
                    label="Email"
                    name="email"
                    type="email"
                    required
                    autoComplete="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                />
                <FormField
                    id="login-password"
                    label="Password"
                    name="password"
                    type="password"
                    required
                    autoComplete="current-password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                />
                <FormError message={error} />
                <button
                    disabled={busy}
                    className="w-full rounded-xl bg-brand-600 py-2.5 text-sm font-medium text-white transition-colors hover:bg-brand-700 disabled:opacity-60"
                >
                    {busy ? "Signing in…" : "Sign in"}
                </button>
                {footer}
            </form>
        </main>
    );
}
