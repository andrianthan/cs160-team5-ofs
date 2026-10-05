import { useState } from 'react';
import { Link, Navigate, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../AuthContext";

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
                <div>
                    <label htmlFor="reg-name" className="text-sm font-medium text-brand-900/80">Full name</label>
                    <input
                        id="reg-name" name="name" type="text" required autoComplete="name"
                        className="mt-1 w-full border border-brand-200 rounded-xl px-3 py-2.5 text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none transition" 
                        onChange={(e) => {setName(e.target.value)}}
                    />
                </div>

                <div>
                    <label htmlFor="reg-email" className="text-sm font-medium text-brand-900/80">Email</label>
                    <input 
                        id="reg-email" name="email" type="email" required autoComplete="email"
                        className="mt-1 w-full border border-brand-200 rounded-xl px-3 py-2.5 text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none transition"
                        onChange={(e) => {setEmail(e.target.value)}}
                    />
                </div>

                <div>
                    <label htmlFor="reg-password" className="text-sm font-medium text-brand-900/80">Password</label>
                    <input 
                        id="reg-password" name="password" type="password" required
                        autoComplete="new-password" className="mt-1 w-full border border-brand-200 rounded-xl px-3 py-2.5 text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none transition"
                        onChange={(e) => {setPassword(e.target.value)}}
                    />
                </div>

                {error && (
                    <p id="login-error" className="text-sm text-red-600 flex items-center gap-1.5" role="alert">
                        <i className="ph ph-warning-circle" aria-hidden="true"></i>
                        <span>{error}</span>
                    </p>
                )}

                <button className="w-full bg-brand-600 hover:bg-brand-700 text-white font-medium rounded-xl py-2.5 text-sm transition-colors duration-200 cursor-pointer">
                    Create account
                </button>
               
                <p className="text-center text-sm text-brand-900/60">
                    Already have one? <span> </span>
                    <a href="#/login" className="text-brand-700 font-medium hover:underline">
                        Log in
                    </a>
                </p>
            </form>
        </div>
    );
}