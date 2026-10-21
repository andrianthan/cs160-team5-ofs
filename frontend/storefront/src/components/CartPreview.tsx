import { Link } from "react-router-dom";
import { useAuth } from "../AuthContext";
import { useCart } from "../CartContext";

type CartPreviewProps = {
    busy: boolean;
    message: string | null;
    onChange: (productId: number, quantity: number) => Promise<unknown>;
    onClear: () => Promise<unknown>;
};

const money = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
});

export default function CartPreview({
    busy,
    message,
    onChange,
    onClear,
}: CartPreviewProps) {
    const { user } = useAuth();
    const { cart, count, loading, error, refresh } = useCart();
    const disabled = busy || loading || error !== null;

    return (
        <div
            aria-labelledby="cart-preview-title"
            className="rounded-3xl border border-brand-100 bg-white p-5 shadow-sm shadow-brand-900/5 lg:sticky lg:top-24"
        >
            <div className="mb-4 flex items-center justify-between gap-2">
                <h2
                    id="cart-preview-title"
                    className="font-display text-lg font-bold"
                >
                    Your cart
                </h2>
                {user && (
                    <span className="rounded-full bg-brand-50 px-2.5 py-1 text-xs font-medium text-brand-700">
                        {count} item{count === 1 ? "" : "s"}
                    </span>
                )}
            </div>

            {user === undefined ? (
                <p className="text-sm text-brand-900/50">
                    Checking your session…
                </p>
            ) : !user ? (
                <p className="text-sm leading-relaxed text-brand-900/60">
                    <Link
                        to="/login"
                        state={{ from: "/browse" }}
                        className="font-medium text-brand-700 underline"
                    >
                        Sign in
                    </Link>{" "}
                    to save products and preview your cart here.
                </p>
            ) : loading ? (
                <p role="status" className="text-sm text-brand-900/50">
                    Loading your cart…
                </p>
            ) : error ? (
                <div role="alert" className="space-y-2 text-sm text-red-600">
                    <p>{error}</p>
                    <button
                        type="button"
                        onClick={() => void refresh()}
                        className="font-medium underline"
                    >
                        Retry loading cart
                    </button>
                </div>
            ) : cart.lines.length === 0 ? (
                <p className="rounded-2xl border border-dashed border-brand-200 px-3 py-6 text-center text-sm text-brand-900/50">
                    Your cart is empty. Add a product to get started.
                </p>
            ) : (
                <>
                    <ul className="max-h-80 space-y-4 overflow-y-auto pr-1">
                        {cart.lines.map((line) => (
                            <li
                                key={line.productId}
                                className="border-b border-brand-100 pb-4 last:border-0"
                            >
                                <div className="flex items-start justify-between gap-3">
                                    <h3 className="text-sm font-medium leading-snug">
                                        {line.name}
                                    </h3>
                                    <span className="shrink-0 text-sm font-medium">
                                        {line.unavailable
                                            ? "—"
                                            : money.format(line.lineTotal ?? 0)}
                                    </span>
                                </div>
                                <p className="mt-1 text-xs text-brand-900/50">
                                    {money.format(line.price)} · {line.weightLb}{" "}
                                    lb each
                                </p>
                                {line.unavailable ? (
                                    <p className="mt-2 text-xs text-red-600">
                                        Unavailable — excluded from totals
                                    </p>
                                ) : (
                                    <div className="mt-2 flex items-center gap-2">
                                        <button
                                            type="button"
                                            aria-label={`Decrease ${line.name}`}
                                            disabled={disabled}
                                            onClick={() =>
                                                void onChange(
                                                    line.productId,
                                                    line.quantity - 1,
                                                )
                                            }
                                            className="h-8 w-8 rounded-lg border border-brand-200 hover:bg-brand-50 disabled:opacity-40"
                                        >
                                            −
                                        </button>
                                        <span className="w-6 text-center text-sm">
                                            {line.quantity}
                                        </span>
                                        <button
                                            type="button"
                                            aria-label={`Increase ${line.name}`}
                                            disabled={
                                                disabled || line.quantity >= 999
                                            }
                                            onClick={() =>
                                                void onChange(
                                                    line.productId,
                                                    line.quantity + 1,
                                                )
                                            }
                                            className="h-8 w-8 rounded-lg border border-brand-200 hover:bg-brand-50 disabled:opacity-40"
                                        >
                                            +
                                        </button>
                                        <button
                                            type="button"
                                            disabled={disabled}
                                            aria-label={`Remove ${line.name}`}
                                            onClick={() =>
                                                void onChange(line.productId, 0)
                                            }
                                            className="ml-auto text-xs text-brand-900/50 hover:text-red-600 disabled:opacity-40"
                                        >
                                            Remove
                                        </button>
                                    </div>
                                )}
                            </li>
                        ))}
                    </ul>

                    <dl className="mt-4 space-y-2 text-sm">
                        <div className="flex justify-between">
                            <dt>Subtotal</dt>
                            <dd>{money.format(cart.subtotal)}</dd>
                        </div>
                    </dl>
                    <Link
                        to="/cart"
                        className="mt-4 block rounded-full bg-brand-600 px-4 py-2.5 text-center text-sm font-medium text-white hover:bg-brand-700"
                    >
                        View full cart
                    </Link>
                    <button
                        type="button"
                        disabled={disabled}
                        onClick={() => void onClear()}
                        className="mt-3 w-full text-center text-xs text-brand-900/50 hover:text-red-600 disabled:opacity-40"
                    >
                        Empty cart
                    </button>
                </>
            )}
            {message && (
                <p role="alert" className="mt-3 text-sm text-red-600">
                    {message}
                </p>
            )}
        </div>
    );
}
