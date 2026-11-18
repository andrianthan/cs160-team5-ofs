import { Fragment, useEffect, useRef } from "react";
import { CircleMarker, MapContainer, Marker, Polyline, TileLayer, Tooltip, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

import type { DispatchTrip, Robot } from "../api/dispatch";

// Same tiles as the storefront's tracking map (react-leaflet + OpenStreetMap): no API key needed.
const DOWNTOWN_SJ: [number, number] = [37.3382, -121.8863];

const pin = (html: string, size: number) =>
    L.divIcon({ className: "", html, iconSize: [size, size], iconAnchor: [size / 2, size / 2] });

const BADGE =
    "display:flex;align-items:center;justify-content:center;border:2px solid white;box-shadow:0 1px 4px #0005;font:600 11px sans-serif;";

function stopIcon(n: number, delivered: boolean) {
    const colors = delivered ? "background:#2f7d4f;color:white" : "background:#fcd34d;color:#713f12";
    return pin(`<div style="${BADGE}${colors};width:24px;height:24px;border-radius:50%">${n}</div>`, 24);
}

function robotIcon(label: string, offline: boolean) {
    return L.divIcon({
        className: "",
        html: `<div style="${BADGE}background:${offline ? "#b91c1c" : "#14392a"};color:white;border-radius:6px;padding:2px 6px;white-space:nowrap;transform:translate(-50%,-50%);display:inline-flex">${label}</div>`,
        iconSize: [0, 0],
        iconAnchor: [0, 0],
    });
}

// Zooms to the data once; later polls leave the user's panning and zooming alone.
function FitOnce({ points }: { points: [number, number][] }) {
    const map = useMap();
    const done = useRef(false);
    useEffect(() => {
        if (done.current || points.length === 0) return;
        map.fitBounds(L.latLngBounds(points), { padding: [40, 40], maxZoom: 16 });
        done.current = true;
    }, [map, points]);
    return null;
}

export default function StreetMap({ trips, robots }: { trips: DispatchTrip[]; robots: Robot[] }) {
    const points: [number, number][] = []; // [lat, lng]
    for (const t of trips) {
        t.orders.forEach((o) => points.push([o.deliveryLat, o.deliveryLng]));
        t.routeGeometry?.coordinates.forEach(([lng, lat]) => points.push([lat, lng]));
    }

    // Robots at the same spot (all parked at the store) share one marker and one label.
    const groups = new Map<string, { key: string; lat: number; lng: number; names: string[]; offline: boolean }>();
    for (const r of robots) {
        if (r.lat === null || r.lng === null) continue;
        const key = `${r.lat.toFixed(4)},${r.lng.toFixed(4)}`;
        const g = groups.get(key) ?? { key, lat: r.lat, lng: r.lng, names: [], offline: true };
        g.names.push(r.code);
        g.offline = g.offline && r.status === "offline";
        groups.set(key, g);
        points.push([r.lat, r.lng]);
    }

    return (
        <div role="img" aria-label="Street map of delivery stops and Robots" className="w-full h-[360px] sm:h-[420px] border border-brand-100 rounded-2xl overflow-hidden">
            <MapContainer center={DOWNTOWN_SJ} zoom={14} scrollWheelZoom={false} style={{ height: "100%", width: "100%" }}>
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                <FitOnce points={points} />

                {trips.map((t) =>
                    t.status === "dispatched" ? (
                        <Fragment key={t.id}>
                            {t.routeGeometry && (
                                <Polyline
                                    positions={t.routeGeometry.coordinates.map(([lng, lat]) => [lat, lng] as [number, number])}
                                    pathOptions={{ color: "#2f7d4f", weight: 4, opacity: 0.85 }}
                                />
                            )}
                            {t.stops.map((s) => (
                                <Marker key={s.orderId} position={[s.lat, s.lng]} icon={stopIcon(s.number, s.status === "delivered")}>
                                    <Tooltip>
                                        Trip {t.id}, stop {s.number}
                                        {s.status === "delivered" ? " (delivered)" : ""}
                                    </Tooltip>
                                </Marker>
                            ))}
                        </Fragment>
                    ) : (
                        t.orders.map((o) => (
                            <CircleMarker
                                key={o.id}
                                center={[o.deliveryLat, o.deliveryLng]}
                                radius={6}
                                pathOptions={{ color: "#d97706", fillColor: "#fde68a", fillOpacity: 1, weight: 2 }}
                            >
                                <Tooltip>Order #{o.id}, waiting (Trip {t.id})</Tooltip>
                            </CircleMarker>
                        ))
                    ),
                )}

                {[...groups.values()].map((g) => (
                    <Marker
                        key={g.key}
                        position={[g.lat, g.lng]}
                        icon={robotIcon(g.names.length > 2 ? `${g.names.length} robots` : g.names.join(", "), g.offline)}
                    >
                        <Tooltip>{g.names.join(", ")}</Tooltip>
                    </Marker>
                ))}
            </MapContainer>
        </div>
    );
}
