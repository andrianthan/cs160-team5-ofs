import { Link } from "react-router-dom";

export default function NotFoundPage({ homeTo, homeLabel }: { homeTo: string; homeLabel: string }) {
    return (
        <main className="mx-auto max-w-xl px-4 py-16 text-center">
            <p className="text-sm font-medium text-brand-900/50">404</p>
            <h1 className="mb-2 font-display text-2xl font-bold text-brand-900">Page not found</h1>
            <p className="mb-6 text-sm text-brand-900/60">That page doesn't exist. Check the address, or head back.</p>
            <Link
                to={homeTo}
                className="inline-block rounded-full bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
            >
                {homeLabel}
            </Link>
        </main>
    );
}
