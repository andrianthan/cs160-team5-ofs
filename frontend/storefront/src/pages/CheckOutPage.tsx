import { useState, useRef } from "react";
import { AddressAutofill } from "@mapbox/search-js-react";
import { Link } from "react-router-dom";
import { apiRequest, jsonRequest } from "@ofs/shared/api";
import { useCart } from "../CartContext";

const money = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
});

export default function CheckOutPage() {
    const { cart, loading, error } = useCart();

    // address handling
    const [address, setAddress] = useState<string>(""); // address input from user
    const [checked, setChecked] = useState<{ address: string } | null>(null); // final address input
    const [addressError, setAddressError] = useState("");

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
            setChecked({ address: res.data.address }); // standarize address
        } else {
            setAddressError(res.data.message);
        }
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

            <div className="grid md:grid-cols-3 gap-6">
                <form className="md:col-span-2 bg-white border border-brand-100 rounded-3xl p-5 h-fit" onSubmit={(e) => e.preventDefault()}>
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
                </form>

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
        </div>
    );

}