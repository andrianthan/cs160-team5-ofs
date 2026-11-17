import { apiRequest, jsonRequest, type ApiResult } from "@ofs/shared/api";

export type OrderStatus =
    | "placed"
    | "planned"
    | "out_for_delivery"
    | "delivered"
    | "delivery_failed"
    | "manual_review"
    | "cancelled";

export type OrderLine = {
    productId: number;
    name: string;
    price: number;
    weightLb: number;
    quantity: number;
};

export type Order = {
    id: number;
    userId: number;
    customerName: string;
    tripId: number | null;
    status: OrderStatus;
    lines: OrderLine[];
    subtotal: number;
    deliveryFee: number;
    total: number;
    orderWeightLb: number;
    deliveryAddress: string;
    deliveryLat: number;
    deliveryLng: number;
    createdAt: string;
};

export type Trip = {
    id: number;
    status: "open" | "ready" | "dispatched" | "completed";
    readyReason: "full" | "deadline" | null; // why a "ready" Trip stopped taking orders
    orderIds: number[];
    orderCount: number;
    weightLb: number;
    createdAt: string;
    dispatchedAt: string | null;
};

// The server's 401 and 403 bodies are just "unauthorized" and "forbidden". Say it in words.
function friendly<T>(result: ApiResult<T>): ApiResult<T> {
    if (result.ok) return result;

    if (result.status === 401) {
        return { ...result, data: { ...result.data, message: "Please sign in again." } };
    }
    if (result.status === 403) {
        return { ...result, data: { ...result.data, message: "Only staff can manage orders." } };
    }
    return result;
}

// Staff see every customer's orders, newest first.
export async function listOrders(status?: OrderStatus) {
    const query = status ? `?status=${status}` : "";
    return friendly(await apiRequest<{ orders: Order[] }>(`/api/orders${query}`));
}

// "Mark Prepared": the order moves to planned and joins an open Trip (or starts one).
export async function prepareOrder(id: number) {
    return friendly(await apiRequest<{ order: Order; trip: Trip }>(`/api/orders/${id}/prepare`, jsonRequest("POST")));
}

// Manual Review and back. Planned and Out for Delivery come from prepare and Dispatch instead.
export async function setOrderStatus(id: number, status: OrderStatus) {
    return friendly(await apiRequest<Order>(`/api/orders/${id}/status`, jsonRequest("PATCH", { status })));
}

//Manager order cancellation
export async function cancelOrder(id: number, reason: string) {
    return friendly(
        await apiRequest<{
            message: string;
            orderId: number;
            action: string;
            previousStatus: string;
            status: OrderStatus;
            managerId: number;
            reason: string;
        }>(
            `/api/orders/${id}/override`,
            jsonRequest("POST", {
                action: "cancel",
                reason,
                confirmed: true,
            })
        )
    );
}