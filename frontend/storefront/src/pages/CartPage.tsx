import { useState, useEffect } from 'react';

import { Link, Navigate, useNavigate, useLocation } from "react-router-dom";

import { useAuth } from "../AuthContext";
import { useCart } from '../CartContext';

const money = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
});

export default function CartPage() {
    const { user } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();
    const {
        cart,
        count,
        changeBy,
        setQuantity,
        clear,
    } = useCart();

    const [message, setMessage] = useState("");
    const [busyProductId, setBusyProductId] = useState<number | null>(null);

    // check login
    if (!user) {
        const from = (location.state as { from?: string } | null)?.from ?? "/browse";
        return <Navigate to={from} replace />;
    }

    const changeQuantity = async (productId: number, amount: number) => {
        setMessage("");
        setBusyProductId(productId);

        const result = await changeBy(productId, amount);

        if (!result.ok) {
            setMessage(result.message);
        }

        setBusyProductId(null);
    }

    const removeProduct = async (productId: number) => {
        setMessage("");
        setBusyProductId(productId);

        const result = await setQuantity(productId, 0);

        if (!result.ok) {
            setMessage(result.message);
        }

        setBusyProductId(null);
    }

    const emptyCart = async () => {
        setMessage("");


        const result = await clear();

        if (!result.ok) {
            setMessage(result.message);
        }
    }

    const isEmpty = cart.lines.length === 0;

    return (
        <div className="max-w-5xl mx-auto px-4 py-6">
            <div className="flex items-center justify-between mb-5">
                <h1 className="text-2xl font-display font-bold">
                    Your Cart
                </h1>
                {!isEmpty && (
                    <span className="text-sm text-brand-900/50">
                        {count} item{count === 1 ? "" : "s"}
                    </span>
                )}
            </div>

            {message && (
                <div
                    className="mb-4 text-sm bg-red-50 text-red-700 border border-red-200 rounded-xl px-3 py-2.5"
                    role="alert"
                >
                    {message}
                </div>
            )}

            {isEmpty ? (
                <div className="text-brand-900/50 py-16 text-center border-2 border-dashed border-brand-200 rounded-3xl">
                    Your cart is empty.{" "}
                    <Link
                        to="/browse"
                        className="text-brand-700 font-medium hover:underline"
                    >
                        Go Browse
                    </Link>
                </div>
            ) : (
                <div className="grid md:grid-cols-3 gap-6">
                    <section className="md:col-span-2 space-y-3">
                        {cart.lines.map((line) => {
                            const busy = busyProductId === line.productId;

                            return (
                                <article
                                    key={line.productId}
                                    className="bg-white border border-brand-100 rounded-2xl p-4 flex items-center gap-4"
                                >
                                    <div
                                        className="w-9 h-9 rounded-xl bg-brand-50 text-brand-700 flex items-center justify-center text-lg shrink-0"
                                        aria-hidden="true"
                                    >
                                        {line.name.charAt(0)}
                                    </div>

                                    <div className="flex-1 min-w-0">
                                        <div className="font-medium text-sm truncate">
                                            {line.name}
                                        </div>
                                        <div className="text-xs text-brand-900/50">
                                            {money.format(line.price)} · {line.weightLb} lb each
                                        </div>
                                        {line.unavailable && (
                                            <div className="text-xs text-red-600 mt-1">
                                                Currently unavailable
                                            </div>
                                        )}
                                    </div>

                                    {!line.unavailable && (
                                        <div className="flex items-center gap-2">
                                            <button
                                                type="button"
                                                aria-label={"Decrease " + line.name}
                                                disabled={busy}
                                                onClick={() => changeQuantity(line.productId, -1)}
                                                className="w-8 h-8 rounded-lg border border-brand-200 text-sm hover:bg-brand-50 disabled:opacity-50 cursor-pointer transition-colors duration-200"
                                            >
                                                –
                                            </button>
                                            <span className="w-6 text-center text-sm">
                                                {line.quantity}
                                            </span>
                                            <button
                                                type="button"
                                                aria-label={"Increase " + line.name}
                                                disabled={busy}
                                                onClick={() => changeQuantity(line.productId, 1)}
                                                className="w-8 h-8 rounded-lg border border-brand-200 text-sm hover:bg-brand-50 disabled:opacity-50 cursor-pointer transition-colors duration-200"
                                            >
                                                +
                                            </button>
                                        </div>
                                    )}

                                    <button
                                        type="button"
                                        aria-label={"Remove " + line.name}
                                        disabled={busy}
                                        onClick={() => removeProduct(line.productId)}
                                        className="text-brand-900/40 hover:text-red-600 disabled:opacity-50 text-sm cursor-pointer transition-colors duration-200"
                                    >
                                        🗑
                                    </button>
                                </article>
                            );
                        })}

                        <button
                            type="button"
                            onClick={emptyCart}
                            className="text-sm text-brand-900/50 hover:text-red-600 transition-colors"
                        >
                            Empty cart
                        </button>
                    </section>

                    <aside className="bg-white border border-brand-100 rounded-3xl p-5 h-fit space-y-3 shadow-sm shadow-brand-900/5">
                        <div className="flex justify-between text-sm">
                            <span>Subtotal</span>
                            <span>{money.format(cart.subtotal)}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                            <span>Order Weight</span>
                            <span>{cart.orderWeightLb.toFixed(1)} lb</span>
                        </div>
                        <div className="flex justify-between text-sm">
                            <span>Delivery Fee</span>
                            <span>{money.format(cart.deliveryFee)}</span>
                        </div>

                        <div className="border-t border-brand-100 pt-3 flex justify-between font-semibold">
                            <span>Total</span>
                            <span>{money.format(cart.total)}</span>
                        </div>

                        <p className="text-xs text-brand-900/50">
                            {cart.deliveryFee > 0
                                ? "Order is 20 lb or more: $10 Delivery Fee applies."
                                : "Under 20 lb: free delivery."}
                        </p>

                        {cart.overweight && (
                            <div
                                className="text-sm bg-red-50 text-red-700 border border-red-200 rounded-xl px-3 py-2.5"
                                role="alert"
                            >
                                Order exceeds 200 lb — remove items before checkout. (BR-3)
                            </div>
                        )}

                        <button
                            type="button"
                            disabled={cart.overweight}
                            onClick={() => navigate("/checkout")}
                            className="w-full bg-brand-600 hover:bg-brand-700 disabled:bg-brand-900/20 disabled:cursor-not-allowed text-white font-medium rounded-xl py-2.5 text-sm transition-colors duration-200 cursor-pointer"
                        >
                            Checkout
                        </button>
                    </aside>
                </div>
            )}
        </div>
    );
}