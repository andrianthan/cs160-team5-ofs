import { apiRequest, jsonRequest, type ApiResult } from "@ofs/shared/api";

export type TripStop = {
    number: number;
    orderId: number;
    status: "pending" | "arrived" | "delivered" | "delivery_failed";
    lat: number;
    lng: number;
    estimatedArrival: string | null;
    arrivedAt: string | null;
};

export type TripOrder = {
    id: number;
    customerName: string;
    status: string;
    weightLb: number;
    deliveryAddress: string;
    deliveryLat: number;
    deliveryLng: number;
    createdAt: string;
};

export type DispatchTrip = {
    id: number;
    status: "open" | "ready" | "dispatched" | "completed";
    readyReason: "full" | "deadline" | null;
    orderCount: number;
    weightLb: number;
    createdAt: string;
    dispatchedAt: string | null;
    deadline: string | null;
    overdue: boolean;
    robotId: number | null;
    estimatedDurationMinutes: number | null;
    routeGeometry: { type: "LineString"; coordinates: [number, number][] } | null; // [lng, lat]
    stops: TripStop[];
    orders: TripOrder[];
};

export type RobotStatus = "available" | "reserved" | "loading" | "out_for_delivery" | "returning" | "offline";

export type Robot = {
    id: number;
    code: string;
    status: RobotStatus;
    lat: number | null;
    lng: number | null;
    updatedAt: string | null;
};

// The server's 401/403 bodies are just "unauthorized"/"forbidden". Say it in words.
function friendly<T>(result: ApiResult<T>): ApiResult<T> {
    if (result.ok) return result;
    if (result.status === 401) return { ...result, data: { ...result.data, message: "Please sign in again." } };
    if (result.status === 403) return { ...result, data: { ...result.data, message: "Only staff can manage dispatch." } };
    return result;
}

export async function listTrips() {
    return friendly(await apiRequest<{ trips: DispatchTrip[] }>("/api/trips"));
}

export async function listRobots() {
    return friendly(await apiRequest<{ robots: Robot[] }>("/api/robots"));
}

// The Employee confirms the Robot is loaded: it picks a Robot, plans the route and sends the Trip out.
export async function dispatchTrip(id: number) {
    return friendly(await apiRequest<DispatchTrip>(`/api/trips/${id}/dispatch`, jsonRequest("POST")));
}
