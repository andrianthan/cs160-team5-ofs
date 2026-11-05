// Basil: the brand mark (a leaf with a gold delivery pin) and wordmark, used in both apps.
export function BasilLogo({ className = "h-8 w-8" }: { className?: string }) {
    return (
        <svg viewBox="0 0 32 32" className={className} role="img" aria-label="Basil" fill="none">
            <rect width="32" height="32" rx="9" className="fill-brand-600" />
            <path d="M9 23c0-8.5 5-13.5 14.5-14.5C23.5 17.5 18.5 23 9 23Z" fill="#fff" />
            <path d="M9.500 22.500 18.5 13.500" strokeWidth="1.6" strokeLinecap="round" className="stroke-brand-600" />
            <circle cx="24.5" cy="24.5" r="3" className="fill-gold-300 stroke-brand-600" strokeWidth="1.5" />
        </svg>
    );
}

export default function BrandMark({
    suffix,
    byline = true,
}: {
    suffix?: string;
    byline?: boolean;
}) {
    return (
        <span className="inline-flex items-center gap-2">
            <BasilLogo />
            <span className="flex items-baseline gap-1.5 leading-none">
                <span className="font-display text-xl font-bold tracking-tight text-brand-800">
                    Basil
                </span>
                {suffix && (
                    <span className="font-display text-sm font-medium text-brand-700/70">
                        {suffix}
                    </span>
                )}
                {byline && !suffix && (
                    <span className="hidden text-xs font-medium text-brand-900/45 sm:inline">
                        by OFS
                    </span>
                )}
            </span>
        </span>
    );
}
