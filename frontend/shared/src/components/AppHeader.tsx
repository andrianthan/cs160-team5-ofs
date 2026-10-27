import type { ReactNode } from "react";

export default function AppHeader({
    brand,
    children,
    width = "max-w-6xl",
}: {
    brand: ReactNode;
    children: ReactNode;
    width?: string;
}) {
    return (
        <header className="sticky top-0 z-40 border-b border-brand-100 bg-white/90 backdrop-blur">
            <div
                className={`${width} relative mx-auto flex flex-wrap items-center justify-between gap-y-2 px-4 py-3`}
            >
                <div className="font-display text-lg font-bold text-brand-700">
                    {brand}
                </div>
                <nav
                    className="flex flex-wrap items-center gap-1"
                    aria-label="Main navigation"
                >
                    {children}
                </nav>
            </div>
        </header>
    );
}
