
import { MapContainer, Marker, Popup, TileLayer, useMap } from "react-leaflet";
import { useEffect } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

type RobotMapProps = {
    robotLatitude: number;
    robotLongitude: number;
    deliveryLatitude: number | null;
    deliveryLongitude: number | null;
    robotCode: string;
};

const robotIcon = L.divIcon({
    className: "",
    html: '<div style="background:#2563eb;color:white;border:3px solid white;border-radius:50%;width:34px;height:34px;' +
        'display:flex;align-items:center;justify-content:center;box-shadow:0 2px 8px #0004;font-size:18px"></div>',
    iconSize: [34, 34],
    iconAnchor: [17, 17],
});

const destinationIcon = L.divIcon({
    className: "",
    html: '<div style="background:#16a34a;color:white;border:3px solid white;border-radius:50%;width:34px;height:34px;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 8px #0004;font-size:18px">🏠</div>',
    iconSize: [34, 34],
    iconAnchor: [17, 17],
});

function UpdateMapPosition({
                               latitude,
                               longitude,
                           }: {
    latitude: number;
    longitude: number;
}) {
    const map = useMap();

    useEffect(() => {
        map.panTo([latitude, longitude]);
    }, [map, latitude, longitude]);

    return null;
}

export default function RobotMap({
                                     robotLatitude,
                                     robotLongitude,
                                     deliveryLatitude,
                                     deliveryLongitude,
                                     robotCode,
                                 }: RobotMapProps) {
    const hasDestination =
        deliveryLatitude !== null &&
        deliveryLongitude !== null;

    return (
        <div className="w-full h-80 rounded-xl overflow-hidden border border-gray-200">
            <MapContainer
                center={[robotLatitude, robotLongitude]}
                zoom={15}
                scrollWheelZoom={false}
                style={{ height: "100%", width: "100%" }}
            >
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />

                <Marker
                    position={[robotLatitude, robotLongitude]}
                    icon={robotIcon}
                >
                    <Popup>
                        <strong>Robot: {robotCode}</strong>
                        <p>Current reported location</p>
                    </Popup>
                </Marker>

                {hasDestination && (
                    <Marker
                        position={[deliveryLatitude, deliveryLongitude]}
                        icon={destinationIcon}
                    >
                        <Popup>Delivery destination</Popup>
                    </Marker>
                )}

                <UpdateMapPosition
                    latitude={robotLatitude}
                    longitude={robotLongitude}
                />
            </MapContainer>
        </div>
    );
}
