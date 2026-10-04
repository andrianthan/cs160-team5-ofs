import {useState} from 'react';
import { Link, Navigate, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../AuthContext";

export default function LoginPage() {
    const { user, login } = useAuth();
            const location = useLocation();
    const navigate = useNavigate();

    const [email, setEmail] = useState<string>("");
    const [password, setPassword] = useState<string>("");

    const [busy, setBusy] = useState(false);

    const [error, setError] = useState<null | string>();

    // check if user is signed in
    if (user === undefined) {
        return null;
    }
    if (user) {
        const from = (location.state as { from?: string } | null)?.from ?? "/browse";
        return <Navigate to={from} replace />;
    } 

    const handleLogin = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setBusy(true); 
        setError(null);
        
        const res = await login(email, password);

        if (!res.ok) {
            setError(res.data.message ?? "Sign in failed. Try again.");
        }
        
        setBusy(false);
    };

    return(
        <div className="max-w-sm mx-auto mt-8">

            <div className="text-center mb-6">
                <div className="w-12 h-12 rounded-2xl bg-brand-600 text-white flex items-center justify-center mx-auto mb-3">
                    <i className="ph ph-leaf text-2xl" aria-hidden="true"></i>
                </div>
                <h1 className="text-2xl font-display font-bold">Welcome to OFS</h1>
                <p className="text-brand-900/60 text-sm mt-1">Organic groceries, delivered by robot.</p>
            </div>

            <form
                id="login-form"
                className="bg-white border border-brand-100 rounded-3xl p-6 space-y-4 shadow-sm shadow-brand-900/5"
                onSubmit={handleLogin}
            >
                <div>
                    <label htmlFor="login-email" className="text-sm font-medium text-brand-900/80">Email</label>
                    <input id="login-email" name="email" type="email" required
                        autoComplete="email"
                        className="mt-1 w-full border border-brand-200 rounded-xl px-3 py-2.5 text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none transition"
                        onChange={(e) => setEmail(e.target.value)}
                    />
                </div>

                <div>
                    <label htmlFor="login-password" className="text-sm font-medium text-brand-900/80">Password</label>
                    <input id="login-password" name="password" type="password" required
                        autoComplete="current-password"
                        className="mt-1 w-full border border-brand-200 rounded-xl px-3 py-2.5 text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none transition"
                        onChange={(e) => setPassword(e.target.value)}
                    />
                </div>

                {error && (
                    <p id="login-error" className="text-sm text-red-600 flex items-center gap-1.5" role="alert">
                        <i className="ph ph-warning-circle" aria-hidden="true"></i>
                        <span>{error}</span>
                    </p>
                )}
                
                <button
                    className="w-full bg-brand-600 hover:bg-brand-700 disabled:opacity-60 text-white font-medium rounded-xl py-2.5 text-sm transition-colors duration-200 cursor-pointer"
                    disabled={busy}
                >
                    {busy ? "Logging in…" : "Log in"}
                </button>

                <p className="text-center text-sm text-brand-900/60">
                    No account? <span> </span>
                    <Link to="/register" className="text-brand-700 font-medium hover:underline">
                        Register
                    </Link>
                </p>
            </form>
        </div>
    );
}