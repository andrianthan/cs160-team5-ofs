import { useEffect, useRef, useState, type FormEvent } from "react";
import { AddressAutofill } from "@mapbox/search-js-react";
import { loadStripe, type Appearance } from "@stripe/stripe-js";
import { Elements, PaymentElement, useElements, useStripe } from "@stripe/react-stripe-js";
import { Link, useSearchParams } from "react-router-dom";
import { apiRequest, jsonRequest } from "@ofs/shared/api";
import { useCart } from "../CartContext";

const money = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
});

// created once, outside the component, so Stripe.js isn't reloaded on every render
const stripePromise = loadStripe(import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY);

// GET/POST /api/payments response (backend payments._view)
type Payment = {
    paymentId: number;
    status: "pending" | "succeeded" | "failed" | "canceled" | "refunded";
    amountCents: number;
    failureReason: string | null;
    orderId: number | null;
    clientSecret?: string; // only on the first POST for an idempotency key
};

const POLL_MS = 1000;
const POLL_LIMIT = 30; // ~30s for Stripe's webhook to reach the backend and place the order

// match the storefront's brand colors and rounded inputs
const appearance: Appearance = {
    theme: "stripe",
    variables: {
        colorPrimary: "#16A34A", // brand-600
        borderRadius: "12px",
    },
};

export default function CheckOutPage() {
    const { cart, loading, error } = useCart();
    // set once the card is confirmed; ?paymentId= is where Stripe sends redirect-based payment methods back
    const [searchParams] = useSearchParams();
    const [paidId, setPaidId] = useState<number | null>(() => Number(searchParams.get("paymentId")) || null);

    // checked before the empty-cart state: a placed order empties the cart
    if (paidId !== null) {
        return <OrderResult paymentId={paidId} />;
    }

    // only these lines get charged; the backend skips unavailable products too
    const lines = cart.lines.filter((line) => !line.unavailable);

    if (loading) {
        return <div className="max-w-5xl mx-auto px-4 py-6 text-sm text-brand-900/50">Loading your cart…</div>;
    }

    if (error) {
        return (
            <div className="max-w-5xl mx-auto px-4 py-6">
                <div className="text-sm bg-red-50 text-red-700 border border-red-200 rounded-xl px-3 py-2.5" role="alert">
                    {error}
                </div>
            </div>
        );
    }

    if (lines.length === 0) {
        return (
            <div className="max-w-5xl mx-auto px-4 py-6">
                <div className="text-brand-900/50 py-16 text-center border-2 border-dashed border-brand-200 rounded-3xl">
                    Your cart is empty.{" "}
                    <Link to="/browse" className="text-brand-700 font-medium hover:underline">
                        Go Browse
                    </Link>
                </div>
            </div>
        );
    }

    return (
        <div className="max-w-5xl mx-auto px-4 py-6">
            <h1 className="text-2xl font-display font-bold mb-5">Checkout</h1>

            {/* Deferred intent: the card form shows now; the PaymentIntent is only created when Pay is clicked (step 4).
                amount is display-only here; the backend always charges its own cart total. */}
            <Elements
                stripe={stripePromise}
                options={{ mode: "payment", amount: Math.round(cart.total * 100), currency: "usd", appearance }}
            >
                <div className="grid md:grid-cols-3 gap-6">
                    <CheckoutForm overweight={cart.overweight} onPaid={setPaidId} />

                    <aside className="bg-white border border-brand-100 rounded-3xl p-5 h-fit space-y-3 shadow-sm shadow-brand-900/5">
                        <h2 className="font-semibold">Order Summary</h2>

                        <ul className="space-y-2">
                            {lines.map((line) => (
                                <li key={line.productId} className="flex justify-between gap-3 text-sm">
                                    <span className="min-w-0 truncate">
                                        {line.name} <span className="text-brand-900/50">× {line.quantity}</span>
                                    </span>
                                    <span>{money.format(line.lineTotal ?? line.price * line.quantity)}</span>
                                </li>
                            ))}
                        </ul>

                        {lines.length < cart.lines.length && (
                            <p className="text-xs text-brand-900/50">
                                Unavailable items in your cart won't be charged or delivered.
                            </p>
                        )}

                        <div className="border-t border-brand-100 pt-3 space-y-2">
                            <div className="flex justify-between text-sm">
                                <span>Subtotal</span>
                                <span>{money.format(cart.subtotal)}</span>
                            </div>
                            <div className="flex justify-between text-sm">
                                <span>Order Weight</span>
                                <span>{cart.orderWeightLb.toFixed(1)} lb</span>
                            </div>
                            <div className="flex justify-between text-sm">
                                <span>Delivery Fee</span>
                                <span>{money.format(cart.deliveryFee)}</span>
                            </div>
                        </div>

                        <div className="border-t border-brand-100 pt-3 flex justify-between font-semibold">
                            <span>Total</span>
                            <span>{money.format(cart.total)}</span>
                        </div>

                        {cart.overweight && (
                            <div className="text-sm bg-red-50 text-red-700 border border-red-200 rounded-xl px-3 py-2.5" role="alert">
                                Order exceeds 200 lb.{" "}
                                <Link to="/cart" className="font-medium underline">Remove items</Link> before checkout.
                            </div>
                        )}
                    </aside>
                </div>
            </Elements>
        </div>
    );

}

// Lives inside <Elements> because useStripe() and useElements() only work there.
function CheckoutForm({ overweight, onPaid }: { overweight: boolean; onPaid: (paymentId: number) => void }) {
    const stripe = useStripe();
    const elements = useElements();

    // address handling
    const [address, setAddress] = useState<string>(""); // address input from user
    const [checked, setChecked] = useState<{ address: string } | null>(null); // final address input
    const [addressError, setAddressError] = useState("");

    // payment form handling
    const [paymentReady, setPaymentReady] = useState(false);
    const [paymentError, setPaymentError] = useState("");
    const [submitting, setSubmitting] = useState(false);

    // one key per payment attempt, so a double click or retry never charges twice
    const [idempotencyKey, setIdempotencyKey] = useState(() => crypto.randomUUID());
    // the payment created for this attempt; reused after a declined card (re-POSTing the key returns no clientSecret)
    const created = useRef<{ payment: Payment; address: string } | null>(null);

    const latest = useRef("");
    const validateAddress = async (rawAddress: string) => {
        latest.current = rawAddress;
        setChecked(null);
        setAddressError("");

        const res = await apiRequest<{ address: string }>(
            "/api/addresses/validate", jsonRequest("POST", { address: rawAddress }),
        );
        if (latest.current !== rawAddress) return;  // a newer request has started, so drop this one

        if (res.ok) {
            setChecked({ address: res.data.address }); // address as standardized by the backend
        } else {
            setAddressError(res.data.message);
        }
    }

    const canPay = Boolean(stripe && elements && paymentReady && checked && !overweight && !submitting);

    const pay = async (e: FormEvent) => {
        e.preventDefault();
        if (!stripe || !elements || !checked || !canPay) return;
        setSubmitting(true);
        setPaymentError("");

        try {
            // 1. validate the card fields before creating anything
            const { error: submitError } = await elements.submit();
            if (submitError) {
                setPaymentError(submitError.message ?? "Check your payment details.");
                return;
            }

            // 2. the address changed since the last attempt: drop that payment and start a new one
            if (created.current && created.current.address !== checked.address) {
                await apiRequest(`/api/payments/${created.current.payment.paymentId}/cancel`, jsonRequest("POST"));
                created.current = null;
                const freshKey = crypto.randomUUID();
                setIdempotencyKey(freshKey);
                return await payWith(freshKey);
            }
            return await payWith(idempotencyKey);
        } finally {
            setSubmitting(false);
        }
    };

    const payWith = async (key: string) => {
        if (!stripe || !elements || !checked) return;

        // 3. create the payment on the backend (it re-checks the cart and address and sets the amount)
        if (!created.current) {
            const res = await apiRequest<Payment>("/api/payments", jsonRequest("POST", { idempotencyKey: key, address: checked.address }));
            if (!res.ok) {
                setPaymentError(res.data.message);
                return;
            }
            if (!res.data.clientSecret) {
                // key was already used (e.g. a previous tab); don't guess, let the backend's state show
                onPaid(res.data.paymentId);
                return;
            }
            created.current = { payment: res.data, address: checked.address };
        }
        const { payment } = created.current;

        // 4. charge the card. Cards finish here; redirect methods come back to ?paymentId=
        const { error: confirmError } = await stripe.confirmPayment({
            elements,
            clientSecret: payment.clientSecret!,
            confirmParams: { return_url: `${window.location.origin}/checkout?paymentId=${payment.paymentId}` },
            redirect: "if_required",
        });
        if (confirmError) {
            // e.g. card declined: the same payment can be retried with another card
            setPaymentError(confirmError.message ?? "Payment failed. Try another card.");
            return;
        }
        onPaid(payment.paymentId);
    };

    return (
        <form className="md:col-span-2 bg-white border border-brand-100 rounded-3xl p-5 h-fit space-y-5" onSubmit={pay}>
            <div>
                <label htmlFor="address" className="text-sm font-medium text-brand-900/80">
                    Delivery address
                </label>
                <AddressAutofill
                    accessToken={import.meta.env.VITE_MAPBOX_TOKEN}
                    options={{ country: "us" }}
                    onRetrieve={(res) => {
                        const picked = res.features[0]?.properties.full_address;
                        if (picked) { setAddress(picked); validateAddress(picked); }
                    }}
                >
                    <input
                        id="address"
                        name="address"
                        autoComplete="address-line1"
                        placeholder="Start typing your address"
                        className="mt-1 w-full rounded-xl border border-brand-200 px-3 py-2.5 text-sm outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-500"
                        value={address}
                        onChange={(e) => { setAddress(e.target.value); setChecked(null); }}
                        onBlur={() => address.trim() && validateAddress(address)}
                    />
                </AddressAutofill>

                {addressError && <p role="alert" className="mt-2 text-sm text-red-600">{addressError}</p>}
                {checked && <p className="mt-2 text-sm text-brand-700">Deliver to: {checked.address}</p>}
            </div>

            <div>
                <h2 className="text-sm font-medium text-brand-900/80 mb-2">Payment</h2>
                <PaymentElement
                    onReady={() => setPaymentReady(true)}
                    onLoadError={(e) => setPaymentError(e.error.message ?? "The payment form couldn't load. Refresh and try again.")}
                />
            </div>

            {paymentError && (
                <div className="text-sm bg-red-50 text-red-700 border border-red-200 rounded-xl px-3 py-2.5" role="alert">
                    {paymentError}
                </div>
            )}

            <button
                type="submit"
                disabled={!canPay}
                className="w-full bg-brand-600 hover:bg-brand-700 disabled:bg-brand-900/20 disabled:cursor-not-allowed text-white font-medium rounded-xl py-2.5 text-sm transition-colors duration-200 cursor-pointer"
            >
                {submitting ? "Processing…" : "Pay"}
            </button>
            {!checked && !overweight && (
                <p className="text-xs text-brand-900/50 text-center">Enter a delivery address in the Downtown San Jose zone to continue.</p>
            )}
        </form>
    );
}

// After the card is charged: wait for the webhook to turn the payment into an Order (or a refund).
function OrderResult({ paymentId }: { paymentId: number }) {
    const { refresh } = useCart();
    const [payment, setPayment] = useState<Payment | null>(null);
    const [gaveUp, setGaveUp] = useState(false);

    useEffect(() => {
        let cancelled = false;
        let tries = 0;
        let timer: ReturnType<typeof setTimeout>;

        const poll = async () => {
            const res = await apiRequest<Payment>(`/api/payments/${paymentId}`);
            if (cancelled) return;
            if (res.ok) {
                setPayment(res.data);
                if (res.data.orderId || res.data.status !== "pending") {
                    if (res.data.orderId) refresh(); // the backend emptied the cart
                    return;
                }
            }
            tries += 1;
            if (tries >= POLL_LIMIT) setGaveUp(true);
            else timer = setTimeout(poll, POLL_MS);
        };
        poll();

        return () => {
            cancelled = true;
            clearTimeout(timer);
        };
        // refresh is recreated on every CartProvider render; polling should only restart for a new payment
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [paymentId]);

    const box = "max-w-md mx-auto mt-12 bg-white border border-brand-100 rounded-3xl p-6 text-center space-y-3 shadow-sm shadow-brand-900/5";

    if (payment?.orderId) {
        return (
            <div className={box}>
                <h1 className="text-2xl font-display font-bold">Order #{payment.orderId} placed</h1>
                <p className="text-sm text-brand-900/60">
                    Paid {money.format(payment.amountCents / 100)}. We'll start preparing it for delivery.
                </p>
                <Link to="/browse" className="inline-block text-brand-700 font-medium hover:underline">Keep shopping</Link>
            </div>
        );
    }

    if (payment && payment.status !== "pending" && payment.status !== "succeeded") {
        return (
            <div className={box}>
                <h1 className="text-xl font-semibold">
                    {payment.status === "refunded" ? "Payment refunded" : "Payment not completed"}
                </h1>
                <p className="text-sm text-brand-900/60">{payment.failureReason ?? "No order was placed."}</p>
                <Link to="/cart" className="inline-block text-brand-700 font-medium hover:underline">Back to cart</Link>
            </div>
        );
    }

    return (
        <div className={box} role="status">
            <h1 className="text-xl font-semibold">{gaveUp ? "Still processing" : "Placing your order…"}</h1>
            <p className="text-sm text-brand-900/60">
                {gaveUp
                    ? "Your payment went through, but the order isn't confirmed yet. Check back in a few minutes; you won't be charged twice."
                    : "Payment received. Confirming your order."}
            </p>
        </div>
    );
}
