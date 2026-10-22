import { useEffect, useState } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { useCart } from "../CartContext";
import CartPreview from "./CartPreview";

export default function CartMenu() {
    const { count, setQuantity, clear, updating } = useCart();
    const [open, setOpen] = useState(false);
    const [message, setMessage] = useState<string | null>(null);

    const { pathname } = useLocation();

    const onCart: boolean = pathname === '/cart';

    // Close when someone clicks or taps outside the cart and its preview.
    useEffect(() => {
        if (!open) return;

        function closeOutside(event: PointerEvent) {
            const menu = document.getElementById("nav-cart-menu");
            if (event.target instanceof Node && !menu?.contains(event.target)) {
                setOpen(false);
            }
        }

        document.addEventListener("pointerdown", closeOutside);
        return () => document.removeEventListener("pointerdown", closeOutside);
    }, [open]);

    async function changeQuantity(productId: number, quantity: number) {
        setMessage(null);
        const result = await setQuantity(productId, quantity);
        if (!result.ok) setMessage(result.message);
    }

    async function emptyCart() {
        setMessage(null);
        const result = await clear();
        if (!result.ok) setMessage(result.message);
    }

    return (
        <div
            id="nav-cart-menu"
            className="-my-3 py-3 sm:relative"
            onPointerEnter={(event) => {
                if (
                    event.pointerType === "mouse" ||
                    event.pointerType === "pen"
                )
                    setOpen(true);
            }}
            onPointerLeave={(event) => {
                // Keyboard users can keep interacting even if the pointer moves away.
                if (!event.currentTarget.contains(document.activeElement))
                    setOpen(false);
            }}
            onFocus={(event) => {
                if (event.target.id !== "nav-cart-toggle") setOpen(true);
            }}
            onBlur={(event) => {
                if (!event.currentTarget.contains(event.relatedTarget))
                    setOpen(false);
            }}
            onKeyDown={(event) => {
                if (event.key === "Escape") {
                    event.preventDefault();
                    document.getElementById("nav-cart-link")?.focus();
                    setOpen(false);
                }
            }}
            onClick={(event) => {
                if (
                    event.target instanceof Element &&
                    event.target.closest("a")
                )
                    setOpen(false);
            }}
        >
            <div className="flex items-center">
                <NavLink
                    id="nav-cart-link"
                    to="/cart"
                    aria-expanded={open}
                    aria-controls="nav-cart-preview"
                    className={({ isActive }) =>
                        `flex items-center gap-1.5 rounded-full px-3 py-2 text-sm font-medium ${isActive ? "bg-brand-50 text-brand-700" : "text-brand-900/60 hover:bg-brand-50"}`
                    }
                >
                    Cart
                    {count > 0 && (
                        <span className="rounded-full bg-brand-100 px-1.5 py-0.5 text-xs text-brand-700">
                            {count}
                        </span>
                    )}
                </NavLink>
                {/* A separate toggle makes the preview usable on touch screens.
                    The Cart link above still opens the full Cart page. */}
                {!onCart && (
                    <button
                        id="nav-cart-toggle"
                        type="button"
                        aria-label="Toggle cart preview"
                        aria-expanded={open}
                        aria-controls="nav-cart-preview"
                        onClick={() => setOpen(!open)}
                        className="flex h-9 w-7 items-center justify-center rounded-full text-brand-900/60 hover:bg-brand-50 focus-visible:outline-2 focus-visible:outline-brand-600"
                    >
                        <svg
                            width="12"
                            height="12"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                            aria-hidden="true"
                        >
                            <path d={open ? "m6 15 6-6 6 6" : "m6 9 6 6 6-6"} />
                        </svg>
                    </button>
                )}
            </div>

            {(open && !onCart) && (
                // Padding bridges the gap so moving from Cart into the panel keeps it open.
                <div className="absolute right-4 top-full z-50 w-[calc(100vw_-_2rem)] pt-2 sm:right-0 sm:w-80">
                    <div
                        id="nav-cart-preview"
                        role="region"
                        aria-label="Cart preview"
                        className="max-h-[calc(100dvh_-_7rem)] overflow-y-auto overscroll-contain rounded-3xl shadow-lg shadow-brand-900/15"
                    >
                        <CartPreview
                            busy={updating}
                            message={message}
                            onChange={changeQuantity}
                            onClear={emptyCart}
                        />
                    </div>
                </div>
            )}
        </div>
    );
}
