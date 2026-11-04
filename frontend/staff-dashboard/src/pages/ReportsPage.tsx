import { useEffect, useState } from "react";

import {
    getDeliveryReport,
    getInventoryReport,
    getSalesReport,
    type DeliveryReport,
    type InventoryReport,
    type SalesReport,
} from "../api/reports";

const money = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });
const pct = (v: number | null) => (v === null ? "n/a" : `${(v * 100).toFixed(1)}%`);

function Stat({ label, value }: { label: string; value: string | number }) {
    return (
        <div className="rounded-xl border border-brand-200 bg-white px-4 py-3">
            <div className="text-xs text-gray-500">{label}</div>
            <div className="text-xl font-bold">{value}</div>
        </div>
    );
}

export default function ReportsPage() {
    const [from, setFrom] = useState("");
    const [to, setTo] = useState("");
    const [sales, setSales] = useState<SalesReport | null>(null);
    const [inventory, setInventory] = useState<InventoryReport | null>(null);
    const [delivery, setDelivery] = useState<DeliveryReport | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        let cancelled = false;
        const timer = window.setTimeout(async () => {
            setLoading(true);
            const [s, i, d] = await Promise.all([getSalesReport(from, to), getInventoryReport(), getDeliveryReport(from, to)]);
            if (cancelled) return;
            const failed = [s, i, d].find((r) => !r.ok);
            setError(failed && !failed.ok ? failed.data.message : null);
            if (s.ok) setSales(s.data);
            if (i.ok) setInventory(i.data);
            if (d.ok) setDelivery(d.data);
            setLoading(false);
        }, 0);
        return () => {
            cancelled = true;
            window.clearTimeout(timer);
        };
    }, [from, to]);

    const input = "border border-brand-200 rounded-full px-3 py-1.5 text-sm focus:ring-2 focus:ring-brand-500 outline-none";

    return (
        <main className="max-w-5xl mx-auto px-4 py-6 space-y-8">
            <div className="flex flex-wrap items-center justify-between gap-3">
                <h1 className="font-display text-2xl font-bold">Reports</h1>
                <div className="flex items-center gap-2 text-sm">
                    <label>From <input type="date" className={input} value={from} onChange={(e) => setFrom(e.target.value)} /></label>
                    <label>To <input type="date" className={input} value={to} onChange={(e) => setTo(e.target.value)} /></label>
                </div>
            </div>

            {error && <p role="alert" className="text-red-700">{error}</p>}
            {loading && !sales && <p>Loading…</p>}

            {sales && (
                <section>
                    <h2 className="font-semibold mb-1">Sales</h2>
                    <p className="text-xs text-gray-500 mb-3">{sales.from} to {sales.to}, cancelled orders excluded</p>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
                        <Stat label="Orders" value={sales.orderCount} />
                        <Stat label="Revenue" value={money.format(sales.revenue)} />
                        <Stat label="Delivery fees" value={money.format(sales.deliveryFees)} />
                        <Stat label="Avg order" value={money.format(sales.averageOrderValue)} />
                    </div>
                    <div className="grid sm:grid-cols-2 gap-6">
                        <table className="w-full text-sm">
                            <thead><tr className="text-left border-b"><th>Day</th><th>Orders</th><th className="text-right">Revenue</th></tr></thead>
                            <tbody>
                                {sales.byDay.map((d) => (
                                    <tr key={d.date}><td>{d.date}</td><td>{d.orders}</td><td className="text-right">{money.format(d.revenue)}</td></tr>
                                ))}
                                {sales.byDay.length === 0 && <tr><td colSpan={3} className="text-gray-500 py-2">No orders in this period.</td></tr>}
                            </tbody>
                        </table>
                        <table className="w-full text-sm">
                            <thead><tr className="text-left border-b"><th>Product demand</th><th>Units</th><th className="text-right">Revenue</th></tr></thead>
                            <tbody>
                                {sales.productDemand.map((p) => (
                                    <tr key={p.productId}><td>{p.name}</td><td>{p.units}</td><td className="text-right">{money.format(p.revenue)}</td></tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </section>
            )}

            {inventory && (
                <section>
                    <h2 className="font-semibold mb-3">Inventory</h2>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
                        <Stat label="Products" value={inventory.totalProducts} />
                        <Stat label="Units in stock" value={inventory.totalUnits} />
                        <Stat label="Low stock" value={inventory.lowStock} />
                        <Stat label="Out of stock" value={inventory.outOfStock} />
                    </div>
                    {inventory.attention.length > 0 && (
                        <table className="w-full text-sm">
                            <thead><tr className="text-left border-b"><th>Needs attention</th><th>Category</th><th className="text-right">Stock</th></tr></thead>
                            <tbody>
                                {inventory.attention.map((p) => (
                                    <tr key={p.id}><td>{p.name}</td><td>{p.category}</td>
                                        <td className={`text-right ${p.stock === 0 ? "text-red-700 font-semibold" : ""}`}>{p.stock} / {p.lowStockThreshold}</td></tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </section>
            )}

            {delivery && (
                <section>
                    <h2 className="font-semibold mb-3">Delivery performance</h2>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                        <Stat label="Delivered" value={delivery.delivered} />
                        <Stat label="Delivery failed" value={delivery.failed} />
                        <Stat label="Success rate" value={pct(delivery.deliverySuccessRate)} />
                        <Stat label="On-time rate" value={pct(delivery.onTimeRate)} />
                    </div>
                    <p className="text-xs text-gray-500 mt-2">On-time rate needs trip ETAs from delivery planning (T13/T15).</p>
                </section>
            )}
        </main>
    );
}
