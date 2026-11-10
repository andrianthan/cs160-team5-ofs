
import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { apiRequest } from "@ofs/shared/api";
import RobotMap from "../components/RobotMap";

type Tracking = {
    orderId: number;
    status: string;
    tripId: number | null;
    trip: {
        id: number;
        status: string;
        dispatchedAt: string | null;
        estimatedDurationMinutes: number | null;
    } | null;
    robot: {
        id: number;
        robotCode: string;
        status: string;
        latitude: number | null;
        longitude: number | null;
        updatedAt: string | null;
    } | null;
    deliveryAddress: string;
    deliveryLocation: {
        latitude: number;
        longitude: number;
    };
    createdAt: string;
    updatedAt: string;
};

type OrderSummary = {
    id: number;
    status: string;
};

const POLL_INTERVAL = 10000;

const statusLabels: Record<string, string> = {
    placed: "Order placed",
    planned: "Preparing delivery",
    out_for_delivery: "Out for delivery",
    delivered: "Delivered",
    delivery_failed: "Delivery failed",
    manual_review: "Under review",
    cancelled: "Cancelled",
};

export default function TrackOrdersPage() {
    const [params, setParams] = useSearchParams();
    const selectedId = params.get("orderId");

    const [orders, setOrders] = useState<OrderSummary[]>([]);
    const [tracking, setTracking] = useState<Tracking | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        let cancelled = false;

        async function loadOrders() {
            const result = await apiRequest<{ orders: OrderSummary[] }>(
                "/api/orders"
            );

            if (!cancelled) {
                if (result.ok) {
                    setOrders(result.data.orders);
                } else {
                    setError(result.data.message || "Unable to load orders.");
                }
                setLoading(false);
            }
        }

        loadOrders();

        return () => {
            cancelled = true;
        };
    }, []);

    useEffect(() => {
        if (!selectedId) {
            setTracking(null);
            return;
        }

        let cancelled = false;

        async function loadTracking() {
            const result = await apiRequest<Tracking>(
                `/api/tracking/${encodeURIComponent(selectedId!)}`
            );

            if (cancelled) return;

            if (result.ok) {
                setTracking(result.data);
                setError("");
            } else {
                setTracking(null);
                const data = result.data as {
                    message?: string;
                    error?: string;
                };

                setError(
                    data.message ||
                    (data.error === "order_not_found"
                        ? "Order not found."
                        : data.error === "forbidden"
                            ? "You do not have permission to track this order."
                            : "Unable to track this order.")
                );
            }
        }

        loadTracking();

        const interval = window.setInterval(loadTracking, POLL_INTERVAL);

        return () => {
            cancelled = true;
            window.clearInterval(interval);
        };
    }, [selectedId]);

    const stages = ["placed", "planned", "out_for_delivery", "delivered"];
    const currentStage = tracking ? stages.indexOf(tracking.status) : -1;

    const exceptionalStatuses = [
        "delivery_failed",
        "manual_review",
        "cancelled",
    ];

    const hasDeliveryIssue =
        tracking !== null &&
        exceptionalStatuses.includes(tracking.status);

    return (
        <main className="max-w-5xl mx-auto px-4 py-8 space-y-6">
            <div>
                <h1 className="text-3xl font-display font-bold">Track Orders</h1>
                <p className="text-sm text-brand-900/60 mt-2">
                    View your delivery progress and robot location.
                </p>
            </div>

            {loading && <p>Loading your orders...</p>}

            {error && (
                <div role="alert" className="bg-red-50 text-red-700 p-4 rounded-xl">
                    {error}
                </div>
            )}

            {!loading && !error && orders.length === 0 && (
                <div className="bg-white border rounded-2xl p-6">
                    <p>You haven't placed any orders yet.</p>
                    <Link to="/browse" className="text-brand-700 underline">
                        Start shopping
                    </Link>
                </div>
            )}

            {orders.length > 0 && (
                <div className="bg-white border border-brand-100 rounded-2xl p-5">
                    <label htmlFor="tracking-order" className="block font-medium mb-2">
                        Select an order
                    </label>
                    <select
                        id="tracking-order"
                        className="border rounded-xl px-3 py-2 w-full"
                        value={selectedId ?? ""}
                        onChange={(e) =>
                            setParams(e.target.value ? { orderId: e.target.value } : {})
                        }
                    >
                        <option value="">Choose an order</option>
                        {orders.map((order) => (
                            <option key={order.id} value={order.id}>
                                Order #{order.id} — {statusLabels[order.status] ?? order.status}
                            </option>
                        ))}
                    </select>
                </div>
            )}

            {tracking && (
                <>
                    {hasDeliveryIssue && (
                        <div
                            role="status"
                            className="bg-yellow-50 border border-yellow-200 text-yellow-800 p-4 rounded-xl"
                        >
                            Delivery status:{" "}
                            {statusLabels[tracking.status] ?? tracking.status}
                        </div>
                    )}
                    <section className="bg-white border border-brand-100 rounded-2xl p-6 space-y-4">
                        <div>
                            <h2 className="text-xl font-semibold">
                                Order #{tracking.orderId}
                            </h2>
                            <p className="text-brand-700 font-medium">
                                {statusLabels[tracking.status] ?? tracking.status}
                            </p>
                        </div>

                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                            {stages.map((stage, index) => (
                                <div
                                    key={stage}
                                    className={`rounded-xl p-3 text-center text-sm ${
                                        currentStage >= index
                                            ? "bg-green-100 text-green-800"
                                            : "bg-gray-100 text-gray-500"
                                    }`}
                                >
                                    {statusLabels[stage]}
                                </div>
                            ))}
                        </div>

                        <div>
                            <h3 className="font-semibold">Delivery address</h3>
                            <p>{tracking.deliveryAddress}</p>
                        </div>

                        {tracking.trip && (
                            <div>
                                <h3 className="font-semibold">Delivery trip</h3>
                                <p>Trip #{tracking.trip.id}</p>
                                <p>Status: {tracking.trip.status}</p>
                                <p>
                                    Estimated trip duration:{" "}
                                    {tracking.trip.estimatedDurationMinutes ?? "Not available"}
                                    {tracking.trip.estimatedDurationMinutes !== null && " minutes"}
                                </p>
                            </div>
                        )}
                    </section>

                    <section className="bg-white border border-brand-100 rounded-2xl p-6 space-y-3">
                        <h2 className="text-xl font-semibold">Robot location</h2>

                        {tracking.robot?.latitude != null &&
                        tracking.robot.longitude != null ? (
                            <>
                                <p>
                                    Robot: {tracking.robot.robotCode}
                                </p>
                                <p>
                                    Last reported position:{" "}
                                    {tracking.robot.latitude.toFixed(6)},{" "}
                                    {tracking.robot.longitude.toFixed(6)}
                                </p>
                                <RobotMap
                                    robotLatitude={tracking.robot.latitude}
                                    robotLongitude={tracking.robot.longitude}
                                    deliveryLatitude={tracking.deliveryLocation.latitude ?? null}
                                    deliveryLongitude={tracking.deliveryLocation.longitude ?? null}
                                    robotCode={tracking.robot.robotCode}
                                />

                            </>
                        ) : (
                            <p className="text-brand-900/60">
                                Robot location is not available yet.
                            </p>
                        )}

                        <p className="text-xs text-brand-900/50">
                            Tracking refreshes every 10 seconds while this page is open.
                        </p>
                    </section>
                </>
            )}
        </main>
    );
}
