// T12: Customer order history. Owner: Karnani Shresthkumar.
// GET /api/orders returns only the signed-in Customer's Orders, newest first.
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { apiRequest } from "@ofs/shared/api";

type OrderStatus =
    | "placed"
    | "planned"
    | "out_for_delivery"
    | "delivered"
    | "delivery_failed"
    | "manual_review"
    | "cancelled";

type OrderLine = {
    productId: number;
    name: string;
    price: number;
    weightLb: number;
    quantity: number;
};

type Order = {
    id: number;
    status: OrderStatus;
    lines: OrderLine[];
    subtotal: number;
    deliveryFee: number;
    total: number;
    orderWeightLb: number;
    deliveryAddress: string;
    createdAt: string;
};

const money = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });

const placedAt = new Intl.DateTimeFormat("en-US", { dateStyle: "medium", timeStyle: "short" });

// Same wording as the Track page, so a Customer sees one name per status.
const STATUS: Record<OrderStatus, { label: string; tone: string }> = {
    placed: { label: "Order placed", tone: "bg-brand-50 text-brand-700 border-brand-200" },
    planned: { label: "Preparing delivery", tone: "bg-brand-50 text-brand-700 border-brand-200" },
    out_for_delivery: { label: "Out for delivery", tone: "bg-brand-600 text-white border-brand-600" },
    delivered: { label: "Delivered", tone: "bg-white text-brand-700 border-brand-300" },
    delivery_failed: { label: "Delivery failed", tone: "bg-red-50 text-red-700 border-red-200" },
    manual_review: { label: "Under review", tone: "bg-gold-50 text-gold-800 border-gold-200" },
    cancelled: { label: "Cancelled", tone: "bg-gray-100 text-gray-600 border-gray-200" },
};

export default function OrdersPage() {
    const [orders, setOrders] = useState<Order[] | null>(null);
    const [error, setError] = useState("");

    useEffect(() => {
        let cancelled = false;

        apiRequest<{ orders: Order[] }>("/api/orders").then((result) => {
            if (cancelled) return;
            if (result.ok) {
                setOrders(result.data.orders);
            } else {
                setError(result.status === 401 ? "Please sign in again." : result.data.message);
                setOrders([]);
            }
        });

        return () => {
            cancelled = true;
        };
    }, []);

    return (
        <div className="max-w-5xl mx-auto px-4 py-6">
            <div className="flex items-center justify-between mb-5">
                <h1 className="text-2xl font-display font-bold">Your Orders</h1>
                {orders && orders.length > 0 && (
                    <span className="text-sm text-brand-900/50">
                        {orders.length} order{orders.length === 1 ? "" : "s"}
                    </span>
                )}
            </div>

            {error && (
                <div
                    className="mb-4 text-sm bg-red-50 text-red-700 border border-red-200 rounded-xl px-3 py-2.5"
                    role="alert"
                >
                    {error}
                </div>
            )}

            {orders === null ? (
                <div className="text-brand-900/50 py-16 text-center" aria-live="polite">
                    Loading your orders…
                </div>
            ) : orders.length === 0 ? (
                !error && (
                    <div className="text-brand-900/50 py-16 text-center border-2 border-dashed border-brand-200 rounded-3xl">
                        You haven't placed an order yet.{" "}
                        <Link to="/browse" className="text-brand-700 font-medium hover:underline">
                            Go Browse
                        </Link>
                    </div>
                )
            ) : (
                <ul className="space-y-4">
                    {orders.map((order) => (
                        <li key={order.id}>
                            <OrderCard order={order} />
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
}

function OrderCard({ order }: { order: Order }) {
    const status = STATUS[order.status] ?? { label: order.status, tone: "bg-gray-100 text-gray-600 border-gray-200" };
    const itemCount = order.lines.reduce((sum, line) => sum + line.quantity, 0);

    return (
        <article className="bg-white border border-brand-100 rounded-2xl p-4 sm:p-5">
            <header className="flex flex-wrap items-start justify-between gap-2 mb-3">
                <div>
                    <h2 className="font-semibold">Order #{order.id}</h2>
                    <p className="text-xs text-brand-900/50">
                        {placedAt.format(new Date(order.createdAt))} · {itemCount} item{itemCount === 1 ? "" : "s"} ·{" "}
                        {order.orderWeightLb} lb
                    </p>
                </div>
                <span className={`text-xs font-medium border rounded-full px-2.5 py-1 ${status.tone}`}>
                    {status.label}
                </span>
            </header>

            <ul className="divide-y divide-brand-100 text-sm">
                {order.lines.map((line) => (
                    <li key={line.productId} className="flex justify-between gap-4 py-1.5">
                        <span className="min-w-0 truncate">
                            <span className="text-brand-900/50">{line.quantity} ×</span> {line.name}
                        </span>
                        <span className="shrink-0 tabular-nums">{money.format(line.price * line.quantity)}</span>
                    </li>
                ))}
            </ul>

            <dl className="mt-3 pt-3 border-t border-brand-100 text-sm space-y-1">
                <div className="flex justify-between text-brand-900/60">
                    <dt>Subtotal</dt>
                    <dd className="tabular-nums">{money.format(order.subtotal)}</dd>
                </div>
                <div className="flex justify-between text-brand-900/60">
                    <dt>Delivery fee</dt>
                    <dd className="tabular-nums">{order.deliveryFee === 0 ? "Free" : money.format(order.deliveryFee)}</dd>
                </div>
                <div className="flex justify-between font-semibold">
                    <dt>Total</dt>
                    <dd className="tabular-nums">{money.format(order.total)}</dd>
                </div>
            </dl>

            <footer className="mt-3 flex flex-wrap items-center justify-between gap-2 text-xs text-brand-900/50">
                <span className="min-w-0 truncate">Deliver to {order.deliveryAddress}</span>
                {order.status !== "cancelled" && (
                    <Link
                        to={`/track?orderId=${order.id}`}
                        className="rounded-full border border-brand-200 px-3 py-1.5 text-sm font-medium text-brand-700 hover:bg-brand-50"
                    >
                        Track
                    </Link>
                )}
            </footer>
        </article>
    );
}
