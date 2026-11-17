import { useCallback, useEffect, useMemo, useState } from "react";

import { dispatchTrip, listRobots, listTrips, type DispatchTrip, type Robot, type RobotStatus } from "../api/dispatch";

const FAST_MS = 3_000; // a Robot is out: show it moving
const SLOW_MS = 15_000;

const ROBOT_LABEL: Record<RobotStatus, string> = {
    available: "Available",
    reserved: "Reserve",
    loading: "Loading",
    out_for_delivery: "Out for delivery",
    returning: "Returning",
    offline: "Offline",
};
const ROBOT_STYLE: Record<RobotStatus, string> = {
    available: "bg-brand-100 text-brand-800",
    reserved: "bg-brand-50 text-brand-700",
    loading: "bg-gold-100 text-gold-800",
    out_for_delivery: "bg-gold-200 text-gold-900",
    returning: "bg-gold-100 text-gold-800",
    offline: "bg-red-50 text-red-700",
};

const TRIP_LABEL = { ready: "Ready to dispatch", open: "Taking orders", dispatched: "Out for delivery", completed: "Completed" } as const;

function clock(iso: string | null): string {
    return iso ? new Date(iso).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" }) : "—";
}

// ---- schematic map: no tiles, just the stops, routes and Robots scaled to fit ----
const W = 640, H = 360, PAD = 28;

function RouteMap({ trips, robots }: { trips: DispatchTrip[]; robots: Robot[] }) {
    const points = useMemo(() => {
        const pts: [number, number][] = []; // [lng, lat]
        for (const t of trips) {
            t.orders.forEach((o) => pts.push([o.deliveryLng, o.deliveryLat]));
            t.routeGeometry?.coordinates.forEach((c) => pts.push(c));
        }
        robots.forEach((r) => r.lat !== null && r.lng !== null && pts.push([r.lng, r.lat]));
        return pts;
    }, [trips, robots]);

    if (points.length === 0) return null;

    const lats = points.map((p) => p[1]);
    const lngs = points.map((p) => p[0]);
    const midLat = (Math.min(...lats) + Math.max(...lats)) / 2;
    const kx = Math.cos((midLat * Math.PI) / 180); // longitude degrees are shorter away from the equator
    const spanX = Math.max((Math.max(...lngs) - Math.min(...lngs)) * kx, 1e-4);
    const spanY = Math.max(Math.max(...lats) - Math.min(...lats), 1e-4);
    const scale = Math.min((W - 2 * PAD) / spanX, (H - 2 * PAD) / spanY);
    const offX = (W - spanX * scale) / 2;
    const offY = (H - spanY * scale) / 2;
    const x = (lng: number) => offX + (lng - Math.min(...lngs)) * kx * scale;
    const y = (lat: number) => H - offY - (lat - Math.min(...lats)) * scale;

    return (
        <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Map of delivery stops and Robots" className="w-full bg-white border border-brand-100 rounded-2xl">
            {trips.map((t) => (
                <g key={t.id}>
                    {t.status === "dispatched" && t.routeGeometry && (
                        <polyline
                            fill="none"
                            stroke="var(--color-brand-400)"
                            strokeWidth="2"
                            strokeDasharray="5 4"
                            points={t.routeGeometry.coordinates.map(([lng, lat]) => `${x(lng)},${y(lat)}`).join(" ")}
                        />
                    )}
                    {t.status === "dispatched"
                        ? t.stops.map((s) => (
                              <g key={s.orderId}>
                                  <circle cx={x(s.lng)} cy={y(s.lat)} r="9" fill={s.status === "delivered" ? "var(--color-brand-600)" : "var(--color-gold-300)"} />
                                  <text x={x(s.lng)} y={y(s.lat) + 4} textAnchor="middle" fontSize="11" fontWeight="600" fill={s.status === "delivered" ? "white" : "var(--color-gold-900)"}>
                                      {s.number}
                                  </text>
                              </g>
                          ))
                        : t.orders.map((o) => (
                              <circle key={o.id} cx={x(o.deliveryLng)} cy={y(o.deliveryLat)} r="5" fill="var(--color-gold-200)" stroke="var(--color-gold-500)" />
                          ))}
                </g>
            ))}
            {robots.map(
                (r) =>
                    r.lat !== null &&
                    r.lng !== null && (
                        <g key={r.id}>
                            <rect x={x(r.lng) - 7} y={y(r.lat) - 7} width="14" height="14" rx="3" fill={r.status === "offline" ? "#B91C1C" : "var(--color-brand-900)"} />
                            <text x={x(r.lng) + 11} y={y(r.lat) - 9} fontSize="11" fill="var(--color-brand-900)">
                                {r.code}
                            </text>
                        </g>
                    ),
            )}
        </svg>
    );
}

export default function DispatchPage() {
    const [trips, setTrips] = useState<DispatchTrip[]>([]);
    const [robots, setRobots] = useState<Robot[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [notice, setNotice] = useState<string | null>(null);
    const [busyId, setBusyId] = useState<number | null>(null);

    const refresh = useCallback(async () => {
        const [t, r] = await Promise.all([listTrips(), listRobots()]);
        if (t.ok && r.ok) {
            setTrips(t.data.trips);
            setRobots(r.data.robots);
            setError(null);
        } else {
            setError(!t.ok ? t.data.message : !r.ok ? r.data.message : null);
        }
        setLoading(false);
    }, []);

    const anyOut = trips.some((t) => t.status === "dispatched") || robots.some((r) => r.status === "out_for_delivery" || r.status === "returning");

    useEffect(() => {
        const first = window.setTimeout(() => void refresh(), 0);
        const timer = window.setInterval(() => void refresh(), anyOut ? FAST_MS : SLOW_MS);
        return () => {
            window.clearTimeout(first);
            window.clearInterval(timer);
        };
    }, [refresh, anyOut]);

    const dispatch = async (trip: DispatchTrip) => {
        setBusyId(trip.id);
        setNotice(null);
        setError(null);
        const result = await dispatchTrip(trip.id);
        if (result.ok) setNotice(`Trip #${trip.id} dispatched with ${trip.orderCount} order${trip.orderCount === 1 ? "" : "s"}.`);
        else setError(result.data.message);
        setBusyId(null);
        await refresh();
    };

    const free = robots.filter((r) => r.status === "available" || r.status === "reserved").length;
    const button = "px-3 py-1.5 rounded-full text-sm font-medium cursor-pointer disabled:opacity-50 transition-colors duration-200";

    return (
        <main className="max-w-5xl mx-auto px-4 py-6 space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-3">
                <h1 className="font-display text-2xl font-bold">Dispatch</h1>
                <button type="button" onClick={() => void refresh()} className={`${button} bg-brand-50 text-brand-700 hover:bg-brand-100`}>
                    Refresh
                </button>
            </div>

            {notice && (
                <p role="status" className="text-sm bg-brand-50 text-brand-800 border border-brand-200 rounded-xl px-3 py-2.5">
                    {notice}
                </p>
            )}
            {error && (
                <p role="alert" className="text-sm bg-red-50 text-red-700 border border-red-200 rounded-xl px-3 py-2.5">
                    {error}
                </p>
            )}

            {loading ? (
                <p className="text-sm text-brand-900/50">Loading…</p>
            ) : (
                <>
                    <section aria-labelledby="fleet">
                        <h2 id="fleet" className="font-display text-lg font-semibold mb-2">
                            Robot fleet <span className="text-sm font-normal text-brand-900/50">· {free} of {robots.length} in the depot</span>
                        </h2>
                        {robots.length === 0 ? (
                            <p className="text-sm text-brand-900/50 border border-dashed border-brand-200 rounded-xl py-6 text-center">No Robots registered.</p>
                        ) : (
                            <ul className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
                                {robots.map((r) => (
                                    <li key={r.id} className="bg-white border border-brand-100 rounded-2xl p-3">
                                        <div className="flex items-center justify-between gap-2">
                                            <span className="font-medium">{r.code}</span>
                                            <span className={`text-xs font-medium rounded-full px-2.5 py-1 ${ROBOT_STYLE[r.status]}`}>{ROBOT_LABEL[r.status]}</span>
                                        </div>
                                        <div className="text-xs text-brand-900/50 mt-1">
                                            {r.lat !== null && r.lng !== null ? `${r.lat.toFixed(4)}, ${r.lng.toFixed(4)}` : "no position"} · updated {clock(r.updatedAt)}
                                        </div>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </section>

                    <section aria-labelledby="map">
                        <h2 id="map" className="font-display text-lg font-semibold mb-2">Live map</h2>
                        {trips.length === 0 && robots.every((r) => r.lat === null) ? (
                            <p className="text-sm text-brand-900/50 border border-dashed border-brand-200 rounded-xl py-6 text-center">Nothing to show yet.</p>
                        ) : (
                            <>
                                <RouteMap trips={trips} robots={robots} />
                                <p className="text-xs text-brand-900/50 mt-1">Squares are Robots, numbered circles are stops on a dispatched Trip (green = delivered), small dots are prepared orders waiting.</p>
                            </>
                        )}
                    </section>

                    <section aria-labelledby="trips">
                        <h2 id="trips" className="font-display text-lg font-semibold mb-2">Trips</h2>
                        {trips.length === 0 ? (
                            <div className="text-brand-900/50 py-10 text-center border border-dashed border-brand-200 rounded-xl">
                                No active Trips. Prepared orders from the Prep Queue are grouped into Trips here.
                            </div>
                        ) : (
                            <ul className="space-y-3">
                                {trips.map((trip) => {
                                    const robot = robots.find((r) => r.id === trip.robotId);
                                    const done = trip.stops.filter((s) => s.status === "delivered").length;
                                    const canDispatch = trip.status === "ready" || trip.status === "open";
                                    return (
                                        <li key={trip.id} className="bg-white border border-brand-100 rounded-2xl p-4">
                                            <div className="flex flex-wrap items-start justify-between gap-3">
                                                <div className="min-w-0">
                                                    <div className="font-medium">
                                                        Trip #{trip.id} <span className="text-brand-900/50 font-normal">· {TRIP_LABEL[trip.status]}</span>
                                                        {trip.overdue && <span className="ml-2 text-xs font-medium text-red-700 bg-red-50 rounded-full px-2 py-0.5">past 30-min deadline</span>}
                                                    </div>
                                                    <div className="text-xs text-brand-900/50">
                                                        {trip.orderCount} order{trip.orderCount === 1 ? "" : "s"} · {trip.weightLb.toFixed(1)} lb
                                                        {canDispatch && trip.deadline && ` · dispatch by ${clock(trip.deadline)}`}
                                                        {trip.status === "ready" && trip.readyReason === "full" && " · full"}
                                                        {trip.status === "dispatched" && ` · ${robot?.code ?? "robot"} · ${done} of ${trip.stops.length} delivered`}
                                                        {trip.status === "dispatched" && trip.estimatedDurationMinutes !== null && ` · ~${trip.estimatedDurationMinutes} min round trip`}
                                                    </div>
                                                </div>
                                                {canDispatch && (
                                                    <button
                                                        type="button"
                                                        disabled={busyId === trip.id || free === 0}
                                                        title={free === 0 ? "No Robot is free right now" : undefined}
                                                        onClick={() => void dispatch(trip)}
                                                        className={`${button} bg-brand-600 text-white hover:bg-brand-700`}
                                                    >
                                                        Dispatch
                                                    </button>
                                                )}
                                            </div>

                                            <ul className="mt-3 border-t border-brand-100 pt-3 space-y-1">
                                                {(trip.status === "dispatched" && trip.stops.length > 0
                                                    ? trip.stops.map((s) => ({ key: s.orderId, order: trip.orders.find((o) => o.id === s.orderId), stop: s }))
                                                    : trip.orders.map((o) => ({ key: o.id, order: o, stop: undefined }))
                                                ).map(({ key, order, stop }) => (
                                                    <li key={key} className="flex flex-wrap justify-between gap-x-3 text-sm">
                                                        <span className="min-w-0 truncate">
                                                            {stop && <span className="text-brand-900/50">{stop.number}. </span>}
                                                            Order #{order?.id ?? key} · {order?.customerName} · <span className="text-brand-900/50">{order?.deliveryAddress}</span>
                                                        </span>
                                                        <span className="text-xs text-brand-900/60 whitespace-nowrap">
                                                            {stop ? (stop.status === "delivered" ? `delivered ${clock(stop.arrivedAt)}` : `ETA ${clock(stop.estimatedArrival)}`) : `${order?.weightLb.toFixed(1)} lb`}
                                                        </span>
                                                    </li>
                                                ))}
                                            </ul>
                                        </li>
                                    );
                                })}
                            </ul>
                        )}
                    </section>
                </>
            )}
        </main>
    );
}
