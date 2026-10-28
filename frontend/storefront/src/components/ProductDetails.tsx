import { useEffect, useRef, useState } from "react";
import type { CartResult } from "../CartContext";
import type { Product } from "@ofs/shared/products";

type ProductDetailsProps = {
    product: Product;
    quantityInCart: number;
    busy: boolean;
    signedIn: boolean;
    sessionLoading: boolean;
    cartLoading: boolean;
    cartError: string | null;
    onSave: (productId: number, quantity: number) => Promise<CartResult>;
    onClose: () => void;
};

const money = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
});

export default function ProductDetails({
    product,
    quantityInCart,
    busy,
    signedIn,
    sessionLoading,
    cartLoading,
    cartError,
    onSave,
    onClose,
}: ProductDetailsProps) {
    const dialogRef = useRef<HTMLDialogElement>(null);
    const initialQuantity = quantityInCart || (product.stock > 0 ? 1 : 0);
    // This is an editable draft. Nothing is sent to Flask until the form is saved.
    const [quantity, setQuantity] = useState(String(initialQuantity));
    const [message, setMessage] = useState<string | null>(null);
    const [saved, setSaved] = useState(false);
    const maximum = Math.min(product.stock, 999); // Same quantity limit as cart.py.
    const number = Number(quantity);
    const wholeNumber =
        quantity.trim() !== "" && Number.isInteger(number) && number >= 0;
    const valid = wholeNumber && (number === 0 || number <= maximum);
    const waiting = busy || sessionLoading || (signedIn && cartLoading);
    const blocked = waiting || (signedIn && cartError !== null);
    const canRemove = valid && quantityInCart > 0 && number === 0;

    // A native dialog supplies focus trapping, Escape, and background isolation.
    useEffect(() => {
        const dialog = dialogRef.current;
        const previousFocus = document.activeElement;
        const previousOverflow = document.body.style.overflow;
        dialog?.showModal();
        document.body.style.overflow = "hidden";

        return () => {
            dialog?.close();
            document.body.style.overflow = previousOverflow;
            if (previousFocus instanceof HTMLElement) previousFocus.focus();
        };
    }, []);

    // If the cart finishes loading or another cart control changes this product,
    // keep the editor in sync with the server-confirmed quantity.
    useEffect(() => {
        setQuantity(String(initialQuantity));
    }, [initialQuantity]);

    function editQuantity(value: string) {
        setQuantity(value);
        setMessage(null);
        setSaved(false);
    }

    async function save() {
        if (blocked) return;
        if (!valid) {
            setMessage(`Enter a whole number from 0 to ${maximum}.`);
            return;
        }
        setMessage(null);
        setSaved(false);
        const result = await onSave(product.id, number);
        if (result.ok) setSaved(true);
        else setMessage(result.message);
    }

    return (
        <dialog
            ref={dialogRef}
            aria-labelledby="product-details-title"
            aria-describedby="product-details-description"
            onCancel={onClose}
            onClick={(event) => {
                if (event.target !== event.currentTarget) return;
                const bounds = event.currentTarget.getBoundingClientRect();
                if (
                    event.clientX < bounds.left ||
                    event.clientX > bounds.right ||
                    event.clientY < bounds.top ||
                    event.clientY > bounds.bottom
                )
                    onClose();
            }}
            className="fixed inset-0 m-auto max-h-[90dvh] w-[calc(100%_-_2rem)] max-w-2xl overflow-y-auto rounded-3xl border border-brand-100 bg-white p-0 text-brand-900 shadow-2xl backdrop:bg-brand-900/40 backdrop:backdrop-blur-sm"
        >
            <div className="flex items-center justify-between border-b border-brand-100 px-5 py-3">
                <span className="text-xs font-medium text-brand-900/50">
                    Product details
                </span>
                <button
                    type="button"
                    autoFocus
                    onClick={onClose}
                    aria-label="Close product details"
                    className="flex h-9 w-9 items-center justify-center rounded-full text-xl hover:bg-brand-50 focus-visible:outline-2 focus-visible:outline-brand-600"
                >
                    <span aria-hidden="true">×</span>
                </button>
            </div>

            <div className="grid gap-6 p-5 sm:grid-cols-2 sm:p-6">
                {product.imageUrl ? (
                    <img
                        src={product.imageUrl}
                        alt={product.name}
                        className="aspect-square w-full rounded-2xl bg-brand-50 object-cover"
                    />
                ) : (
                    <div
                        aria-hidden="true"
                        className="flex aspect-square items-center justify-center rounded-2xl bg-brand-50 font-display text-7xl font-bold text-brand-700"
                    >
                        {product.name.charAt(0)}
                    </div>
                )}

                <div className="flex flex-col gap-3">
                    <p className="text-xs font-medium text-brand-700">
                        {product.category}
                    </p>
                    <h2
                        id="product-details-title"
                        className="font-display text-2xl font-bold leading-tight"
                    >
                        {product.name}
                    </h2>
                    <p className="text-xl font-semibold">
                        {money.format(product.price)}
                    </p>
                    <p className="text-xs text-brand-900/50">
                        {product.weightLb} lb each
                    </p>
                    <p
                        id="product-details-description"
                        className="whitespace-pre-line text-sm leading-relaxed text-brand-900/70"
                    >
                        {product.description?.trim() ||
                            "No description available yet."}
                    </p>
                    <p
                        className={`text-sm font-medium ${product.stock > 0 ? "text-brand-700" : "text-red-600"}`}
                    >
                        {product.stock > 0
                            ? `${product.stock} available`
                            : "Out of stock"}
                    </p>

                    <form
                        className="mt-2 space-y-3"
                        onSubmit={(event) => {
                            event.preventDefault();
                            void save();
                        }}
                    >
                        <div className="flex items-center gap-2">
                            <button
                                type="button"
                                aria-label="Decrease quantity"
                                disabled={
                                    blocked || !wholeNumber || number <= 0
                                }
                                onClick={() => editQuantity(String(number - 1))}
                                className="h-10 w-10 shrink-0 rounded-xl border border-brand-200 hover:bg-brand-50 disabled:cursor-not-allowed disabled:opacity-40"
                            >
                                −
                            </button>
                            <input
                                id="product-quantity"
                                type="number"
                                inputMode="numeric"
                                min="0"
                                max={maximum}
                                step="1"
                                value={quantity}
                                disabled={blocked}
                                onChange={(event) =>
                                    editQuantity(event.target.value)
                                }
                                aria-invalid={!valid}
                                aria-describedby="product-quantity-help"
                                className="h-10 min-w-0 w-20 rounded-xl border border-brand-200 text-center text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500"
                            />
                            <button
                                type="button"
                                aria-label="Increase quantity"
                                disabled={
                                    blocked || !valid || number >= maximum
                                }
                                onClick={() => editQuantity(String(number + 1))}
                                className="h-10 w-10 shrink-0 rounded-xl border border-brand-200 hover:bg-brand-50 disabled:cursor-not-allowed disabled:opacity-40"
                            >
                                +
                            </button>
                        </div>
                        {!valid && (
                            <p className="text-xs text-red-600">
                                Enter a whole number from 0 to {maximum}.
                            </p>
                        )}
                        <p className="text-xs text-brand-900/50">
                            Currently in cart: {signedIn ? quantityInCart : 0}
                        </p>
                        {message && (
                            <p role="alert" className="text-sm text-red-600">
                                {message}
                            </p>
                        )}
                        {signedIn && cartError && (
                            <p role="alert" className="text-sm text-red-600">
                                {cartError}
                            </p>
                        )}
                        {saved && (
                            <p role="status" className="text-sm text-brand-700">
                                Cart updated.
                            </p>
                        )}
                        <button
                            type="submit"
                            disabled={
                                blocked ||
                                !valid ||
                                (product.stock <= 0 && !canRemove) ||
                                (number === 0 && quantityInCart === 0)
                            }
                            className="w-full rounded-full bg-brand-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-brand-700 disabled:cursor-not-allowed disabled:bg-brand-900/20"
                        >
                            {waiting
                                ? "Please wait…"
                                : !signedIn
                                    ? "Sign in to add to cart"
                                    : canRemove
                                        ? "Remove from cart"
                                        : quantityInCart > 0
                                            ? "Update cart"
                                            : "Add to cart"}
                        </button>
                    </form>
                </div>
            </div>
        </dialog>
    );
}
