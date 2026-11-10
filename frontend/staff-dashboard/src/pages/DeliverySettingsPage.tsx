
import { useEffect, useState } from "react";
import {
    getDeliveryPause,
    setDeliveryPause,
} from "../api/deliveryPause";

export default function DeliverySettingsPage() {
    const [paused, setPaused] = useState(false);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState("");
    const [notice, setNotice] = useState("");

    useEffect(() => {
        let active = true;

        async function load() {
            const result = await getDeliveryPause();

            if (!active) return;

            if (result.ok) {
                setPaused(result.data.paused);
            } else {
                setError("Could not load delivery status.");
            }

            setLoading(false);
        }

        void load();

        return () => {
            active = false;
        };
    }, []);

    async function togglePause() {
        const nextPaused = !paused;

        setSaving(true);
        setError("");
        setNotice("");

        try {
            const result = await setDeliveryPause(nextPaused);

            if (result.ok) {
                setPaused(result.data.paused);
                setNotice(
                    result.data.paused
                        ? "New deliveries are now paused."
                        : "New deliveries are now available."
                );
            } else {
                setError("Could not update delivery status.");
            }
        } catch {
            setError("Unable to connect to the server.");
        } finally {
            setSaving(false);
        }
    }

    return (
        <main className="max-w-3xl mx-auto px-4 py-6">
            <h1 className="font-display text-2xl font-bold mb-5">
                Delivery Settings
            </h1>

            <section className="bg-white border border-brand-100 rounded-2xl p-6 space-y-4">
                <h2 className="text-lg font-semibold">
                    Delivery Availability
                </h2>

                {loading ? (
                    <p>Loading delivery status...</p>
                ) : (
                    <>
                        <p className="text-sm">
                            Current status:{" "}
                            <strong>
                                {paused ? "Deliveries Paused" : "Deliveries Active"}
                            </strong>
                        </p>

                        <p className="text-sm text-brand-900/60">
                            Pausing deliveries prevents customers from starting
                            new delivery payments. Existing orders are unaffected.
                        </p>

                        <button
                            type="button"
                            disabled={saving}
                            onClick={() => void togglePause()}
                            className="px-4 py-2 rounded-xl bg-brand-600 text-white font-medium hover:bg-brand-700 disabled:opacity-50"
                        >
                            {saving
                                ? "Updating..."
                                : paused
                                    ? "Resume Deliveries"
                                    : "Pause Deliveries"}
                        </button>
                    </>
                )}

                {notice && (
                    <p role="status" className="text-sm text-green-700">
                        {notice}
                    </p>
                )}

                {error && (
                    <p role="alert" className="text-sm text-red-600">
                        {error}
                    </p>
                )}
            </section>
        </main>
    );
}
