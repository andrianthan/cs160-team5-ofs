import { useCallback, useEffect, useState } from "react";

import { listOrders, prepareOrder, setOrderStatus, type Order, type OrderStatus } from "../api/orders";

import { useAuth } from "@ofs/shared/auth";
import { cancelOrderOverride } from "../api/orderOverride";

const money = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });

const REFRESH_MS = 30_000; // new orders from the storefront show up without reloading the page

const TABS: { status: OrderStatus; label: string; empty: string }[] = [
    { status: "placed", label: "To prepare", empty: "Queue is empty. Orders placed on the Storefront show up here." },
    { status: "planned", label: "Prepared", empty: "No prepared orders waiting for Dispatch." },
    { status: "manual_review", label: "Manual Review", empty: "No orders need attention." },
];

// "5 min ago" style, so the oldest (first to prepare) order stands out.
function ago(iso: string): string {
    const minutes = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 60_000));
    if (minutes < 1) return "just now";
    if (minutes < 60) return `${minutes} min ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours} h ago`;
    return `${Math.floor(hours / 24)} d ago`;
}

export default function OrderQueuePage() {
    const { user } = useAuth();
    const isManager = user?.role === "manager";

    const [cancelOrder, setCancelOrder] = useState<Order | null>(null);
    const [cancelReason, setCancelReason] = useState("");

    const [tab, setTab] = useState<OrderStatus>("placed");

    const [orders, setOrders] = useState<Order[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [notice, setNotice] = useState<string | null>(null);
    const [busyId, setBusyId] = useState<number | null>(null);

    const refresh = useCallback(async () => {
        const result = await listOrders(tab);
        if (result.ok) {
            // oldest first: Delivery Planning works through the oldest Order first
            setOrders([...result.data.orders].sort((a, b) => a.createdAt.localeCompare(b.createdAt)));
            setError(null);
        } else {
            setError(result.data.message);
        }
        setLoading(false);
    }, [tab]);

    // first load and every REFRESH_MS (a zero-delay timer, the same way useProducts does its first load)
    useEffect(() => {
        const first = window.setTimeout(() => void refresh(), 0);
        const timer = window.setInterval(() => void refresh(), REFRESH_MS);
        return () => {
            window.clearTimeout(first);
            window.clearInterval(timer);
        };
    }, [refresh]);

    const switchTab = (status: OrderStatus) => {
        setTab(status);
        setLoading(true);
        setNotice(null);
    };

    // Every action moves the order to another tab, so drop it from this list and reload to stay in sync.
    const act = async (id: number, action: () => Promise<{ ok: boolean; message: string }>) => {
        setBusyId(id);
        setNotice(null);
        setError(null);
        const result = await action();
        if (result.ok) setNotice(result.message);
        else setError(result.message);
        setBusyId(null);
        await refresh();
    };

    const markPrepared = (order: Order) =>
        act(order.id, async () => {
            const r = await prepareOrder(order.id);
            return r.ok
                ? { ok: true, message: `Order #${order.id} prepared and added to Trip #${r.data.trip.id} (${r.data.trip.orderCount} of 10 orders).` }
                : { ok: false, message: r.data.message };
        });

    const moveTo = (order: Order, status: OrderStatus, done: string) =>
        act(order.id, async () => {
            const r = await setOrderStatus(order.id, status);
            return r.ok ? { ok: true, message: `Order #${order.id} ${done}.` } : { ok: false, message: r.data.message };
        });



    const confirmCancellation = async () => {
        if (!cancelOrder || !isManager || busyId !== null) return;

        const reason = cancelReason.trim();

        if (!reason) {
            setError("A cancellation reason is required.");
            return;
        }

        const orderId = cancelOrder.id;

        setBusyId(orderId);
        setError(null);
        setNotice(null);

        try {
            const result = await cancelOrderOverride(orderId, reason);

            if (!result.ok) {
                setError(result.data.message);
                return;
            }

            setNotice(`Order #${orderId} canceled successfully.`);
            setCancelOrder(null);
            setCancelReason("");
            await refresh();
        } catch {
            setError("Unable to cancel the order. Please try again.");
        } finally {
            setBusyId(null);
        }
    };

    const current = TABS.find((t) => t.status === tab)!;
    const button = "px-3 py-1.5 rounded-full text-sm font-medium cursor-pointer disabled:opacity-50 transition-colors duration-200";

    return (
        <main className="max-w-5xl mx-auto px-4 py-6">
            <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
                <h1 className="font-display text-2xl font-bold">Preparation Queue</h1>
                <button
                    type="button"
                    onClick={() => void refresh()}
                    className={`${button} bg-brand-50 text-brand-700 hover:bg-brand-100`}
                >
                    Refresh
                </button>
            </div>

            <div className="flex flex-wrap gap-2 mb-4" role="tablist">
                {TABS.map((t) => (
                    <button
                        key={t.status}
                        type="button"
                        role="tab"
                        aria-selected={t.status === tab}
                        onClick={() => switchTab(t.status)}
                        className={`${button} ${t.status === tab ? "bg-brand-600 text-white" : "bg-brand-50 text-brand-700 hover:bg-brand-100"}`}
                    >
                        {t.label}
                        {t.status === tab && !loading && ` (${orders.length})`}
                    </button>
                ))}
            </div>

            {notice && (
                <p role="status" className="mb-3 text-sm bg-brand-50 text-brand-800 border border-brand-200 rounded-xl px-3 py-2.5">
                    {notice}
                </p>
            )}
            {error && (
                <p role="alert" className="mb-3 text-sm bg-red-50 text-red-700 border border-red-200 rounded-xl px-3 py-2.5">
                    {error}
                </p>
            )}

            {loading ? (
                <p className="text-sm text-brand-900/50">Loading orders…</p>
            ) : orders.length === 0 ? (
                <div className="text-brand-900/50 py-12 text-center border border-dashed border-brand-200 rounded-xl">
                    {current.empty}
                </div>
            ) : (
                <ul className="space-y-3">
                    {orders.map((order) => {
                        const busy = busyId === order.id;
                        return (
                            <li key={order.id} className="bg-white border border-brand-100 rounded-2xl p-4">
                                <div className="flex flex-wrap items-start justify-between gap-3">
                                    <div className="min-w-0">
                                        <div className="font-medium">
                                            Order #{order.id}{" "}
                                            <span className="text-brand-900/50 font-normal">· {order.customerName}</span>
                                        </div>
                                        <div className="text-xs text-brand-900/50">
                                            placed {ago(order.createdAt)} · {order.orderWeightLb.toFixed(1)} lb · {money.format(order.total)}
                                            {order.tripId !== null && ` · Trip #${order.tripId}`}
                                        </div>
                                        <div className="text-xs text-brand-900/50 truncate">{order.deliveryAddress}</div>
                                    </div>

                                    <div className="flex flex-wrap gap-2">
                                        {isManager && (
                                            <button
                                                type="button"
                                                disabled={busy}
                                                onClick={() => {
                                                    setCancelOrder(order);
                                                    setCancelReason("");
                                                    setError(null);
                                                }}
                                                className={`${button} bg-red-50 text-red-700 hover:bg-red-100`}
                                            >
                                                Cancel Order
                                            </button>
                                        )}
                                        {order.status === "placed" && (
                                            <>
                                                <button
                                                    type="button"
                                                    disabled={busy}
                                                    onClick={() => void markPrepared(order)}
                                                    className={`${button} bg-brand-600 text-white hover:bg-brand-700`}
                                                >
                                                    Mark Prepared
                                                </button>
                                                <button
                                                    type="button"
                                                    disabled={busy}
                                                    onClick={() => void moveTo(order, "manual_review", "moved to Manual Review")}
                                                    className={`${button} bg-gold-100 text-gold-800 hover:bg-gold-200`}
                                                >
                                                    Manual Review
                                                </button>
                                            </>
                                        )}
                                        {order.status === "planned" && (
                                            <button
                                                type="button"
                                                disabled={busy}
                                                onClick={() => void moveTo(order, "placed", "taken off its trip and back in the queue")}
                                                className={`${button} bg-brand-50 text-brand-700 hover:bg-brand-100`}
                                            >
                                                Undo prepare
                                            </button>
                                        )}
                                        {order.status === "manual_review" && (
                                            <button
                                                type="button"
                                                disabled={busy}
                                                onClick={() => void moveTo(order, "placed", "back in the queue")}
                                                className={`${button} bg-brand-50 text-brand-700 hover:bg-brand-100`}
                                            >
                                                Back to queue
                                            </button>
                                        )}
                                    </div>
                                </div>

                                {/* the pick list: what to gather from the shelves */}
                                <ul className="mt-3 border-t border-brand-100 pt-3 grid sm:grid-cols-2 gap-x-6 gap-y-1">
                                    {order.lines.map((line) => (
                                        <li key={line.productId} className="flex justify-between gap-3 text-sm">
                                            <span className="min-w-0 truncate">{line.name}</span>
                                            <span className="font-medium">× {line.quantity}</span>
                                        </li>
                                    ))}
                                </ul>
                            </li>
                        );
                    })}
                </ul>
            )}

            {cancelOrder && isManager && (
                <div
                    className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
                    role="presentation"
                >
                    <div
                        role="dialog"
                        aria-modal="true"
                        aria-labelledby="cancel-order-title"
                        className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl space-y-4"
                    >
                        <h2
                            id="cancel-order-title"
                            className="text-xl font-semibold"
                        >
                            Cancel Order #{cancelOrder.id}
                        </h2>

                        <p className="text-sm text-brand-900/70">
                            This action will cancel the order and record the
                            manager's reason in the audit log.
                        </p>

                        <div>
                            <label
                                htmlFor="cancel-reason"
                                className="block text-sm font-medium mb-2"
                            >
                                Cancellation reason
                            </label>

                            <textarea
                                id="cancel-reason"
                                value={cancelReason}
                                onChange={(e) => setCancelReason(e.target.value)}
                                rows={3}
                                maxLength={500}
                                placeholder="Enter the reason for cancellation"
                                className="w-full rounded-xl border border-brand-200 px-3 py-2 text-sm"
                            />
                        </div>

                        {error && (
                            <p role="alert" className="text-sm text-red-600">
                                {error}
                            </p>
                        )}

                        <div className="flex justify-end gap-3">
                            <button
                                type="button"
                                disabled={busyId !== null}
                                onClick={() => {
                                    setCancelOrder(null);
                                    setCancelReason("");
                                }}
                                className="rounded-xl border border-brand-200 px-4 py-2 text-sm"
                            >
                                Go Back
                            </button>

                            <button
                                type="button"
                                disabled={!cancelReason.trim() || busyId !== null}
                                onClick={() => void confirmCancellation()}
                                className="rounded-xl bg-red-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
                            >
                                {busyId !== null ? "Canceling..." : "Confirm Cancellation"}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </main>
    );
}
