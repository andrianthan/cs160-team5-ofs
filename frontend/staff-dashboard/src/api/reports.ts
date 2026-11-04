import { apiRequest } from "@ofs/shared/api";

export type SalesReport = {
    from: string;
    to: string;
    orderCount: number;
    subtotal: number;
    deliveryFees: number;
    revenue: number;
    averageOrderValue: number;
    byDay: { date: string; orders: number; revenue: number }[];
    productDemand: { productId: number; name: string; units: number; revenue: number }[];
};

export type InventoryReport = {
    totalProducts: number;
    totalUnits: number;
    outOfStock: number;
    lowStock: number;
    attention: { id: number; name: string; category: string; stock: number; lowStockThreshold: number }[];
    byCategory: { category: string; products: number; units: number }[];
};

export type DeliveryReport = {
    from: string;
    to: string;
    statusCounts: Record<string, number>;
    delivered: number;
    failed: number;
    deliverySuccessRate: number | null;
    onTimeRate: number | null;
};

const query = (from: string, to: string) => {
    const p = new URLSearchParams();
    if (from) p.set("from", from);
    if (to) p.set("to", to);
    const s = p.toString();
    return s ? `?${s}` : "";
};

// Managers only. Dates are YYYY-MM-DD, inclusive; empty means the server default (last 30 days).
export const getSalesReport = (from: string, to: string) =>
    apiRequest<SalesReport>(`/api/reports/sales${query(from, to)}`);
export const getInventoryReport = () => apiRequest<InventoryReport>("/api/reports/inventory");
export const getDeliveryReport = (from: string, to: string) =>
    apiRequest<DeliveryReport>(`/api/reports/delivery${query(from, to)}`);
