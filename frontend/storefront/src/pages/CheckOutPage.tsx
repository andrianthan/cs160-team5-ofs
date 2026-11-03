import { useState, useRef } from "react";
import { AddressAutofill } from "@mapbox/search-js-react";
import { apiRequest, jsonRequest } from "@ofs/shared/api";


export default function CheckOutPage() {

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


    return (
        <div className="max-w-sm mx-auto mt-8">
            <form onSubmit={(e) => e.preventDefault()}>
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
        </div>
    );

}