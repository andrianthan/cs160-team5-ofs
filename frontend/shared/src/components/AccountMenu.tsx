import { useState } from "react";
import { useAuth } from "../auth/useAuth";

export default function AccountMenu() {
    const { user, logout } = useAuth();
    const [open, setOpen] = useState(false);

    if (!user) return null;

    return (
        <div className="relative">
            <button
                type="button"
                onClick={() => setOpen((current) => !current)}
                aria-label="Account menu"
                aria-expanded={open}
                className="flex h-9 w-9 items-center justify-center rounded-full bg-brand-100 text-brand-700 hover:bg-brand-200"
            >
                <svg
                    viewBox="0 0 24 24"
                    width="20"
                    height="20"
                    fill="currentColor"
                    aria-hidden="true"
                >
                    <circle cx="12" cy="8" r="4" />
                    <path d="M4 20c0-4 3.6-6 8-6s8 2 8 6z" />
                </svg>
            </button>
            {open && (
                <div className="absolute right-0 mt-2 w-44 rounded-2xl border border-brand-100 bg-white p-1 shadow-lg">
                    <p className="truncate px-3 py-2 text-xs text-brand-900/50">
                        {user.email}
                    </p>
                    <button
                        type="button"
                        onClick={() => void logout()}
                        className="w-full rounded-xl px-3 py-2 text-left text-sm hover:bg-brand-50"
                    >
                        Log out
                    </button>
                </div>
            )}
        </div>
    );
}
