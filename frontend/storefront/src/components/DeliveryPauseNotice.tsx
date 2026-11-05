
import { useEffect, useState } from "react";
import { apiRequest } from "@ofs/shared/api";

export default function DeliveryPauseNotice() {
    const [paused, setPaused] = useState(false);

    useEffect(() => {
        let active = true;

        async function checkStatus() {
            try {
                const result = await apiRequest<{ paused: boolean }>(
                    "/api/settings/delivery-pause"
                );

                if (active && result.ok) {
                    setPaused(result.data.paused);
                }
            } catch {
                // The backend still enforces delivery pause.
            }
        }

        void checkStatus();

        const timer = window.setInterval(
            () => void checkStatus(),
            30000
        );

        return () => {
            active = false;
            window.clearInterval(timer);
        };
    }, []);

    if (!paused) return null;

    return (
        <div
            role="status"
            className="bg-amber-50 border-b border-amber-200 px-4 py-3 text-center"
        >
            <p className="text-sm font-semibold text-amber-900">
                Deliveries are temporarily paused
            </p>

            <p className="text-sm text-amber-800">
                We are not accepting new delivery orders right now.
                Please check back later.
            </p>
        </div>
    );
}
