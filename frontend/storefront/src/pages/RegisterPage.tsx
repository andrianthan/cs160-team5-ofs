import { useState } from 'react';
import { Link, Navigate, useLocation } from "react-router-dom";
import { useAuth } from "@ofs/shared/auth";
import { FormError, FormField } from "@ofs/shared/components";

export default function RegisterPage() {
    const { user, register } = useAuth();
    const location = useLocation();

    const [ name, setName ] = useState<string>("");
    const [ email, setEmail ] = useState<string>("");
    const [ password, setPassword ] = useState<string>("");

    const [busy, setBusy] = useState<boolean>(false);
    const [error, setError] = useState<null | string>();

    // send user back to original page if signed in
    if (user) {
        const from = (location.state as { from?: string } | null)?.from ?? "/browse";
        return <Navigate to={from} replace />;
    } 

    const handleRegister = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setBusy(true); 
        setError(null);
        
        const res = await register(name, email, password);

        if (!res.ok) {
            setError(res.data.message ?? "Registration failed. Try again.");
        }
        
        setBusy(false);
    };

    return (
        <div data-route="register" className="max-w-sm mx-auto mt-8">
            <div className="text-center mb-6">
                <h1 className="text-2xl font-display font-bold">Create your account</h1>
            </div>

            <form
                id="register-form"
                className="bg-white border border-brand-100 rounded-3xl p-6 space-y-4 shadow-sm shadow-brand-900/5"
                onSubmit={handleRegister}
            >
                <FormField
                    id="reg-name"
                    label="Full name"
                    name="name"
                    type="text"
                    required
                    autoComplete="name"
                    value={name}
                    onChange={(event) => setName(event.target.value)}
                />

                <FormField
                    id="reg-email"
                    label="Email"
                    name="email"
                    type="email"
                    required
                    autoComplete="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                />

                <FormField
                    id="reg-password"
                    label="Password"
                    name="password"
                    type="password"
                    required
                    autoComplete="new-password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                />

                <FormError message={error} />

                <button
                    disabled={busy}
                    className="w-full bg-brand-600 hover:bg-brand-700 disabled:opacity-60 text-white font-medium rounded-xl py-2.5 text-sm transition-colors duration-200 cursor-pointer"
                >
                    {busy ? "Creating account…" : "Create account"}
                </button>
               
                <p className="text-center text-sm text-brand-900/60">
                    Already have one? <span> </span>
                    <Link to="/login" className="text-brand-700 font-medium hover:underline">
                        Log in
                    </Link>
                </p>
            </form>
        </div>
    );
}
