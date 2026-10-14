import {
    createContext,
    useContext,
    useEffect,
    useState,
    type ReactNode,
} from "react";

import { useAuth } from "./AuthContext";

export type CartLine = {
    productId: number;
    name: string;
    price: number;
    weightLb: number;
    quantity: number;
    unavailable: boolean;
    lineTotal?: number;
    lineWeightLb?: number;
};

export type Cart = {
    lines: CartLine[];
    orderWeightLb: number;
    subtotal: number;
    deliveryFee: number;
    total: number;
    overweight: boolean;
};

type CartResult =
    | { ok: true }
    | { ok: false; message: string };

type CartContextValue = {
    cart: Cart;
    count: number;
    quantityOf: (productId: number) => number;
    changeBy: (
        productId: number,
        amount: number
    ) => Promise<CartResult>;
    setQuantity: (
        productId: number,
        quantity: number
    ) => Promise<CartResult>;
    clear: () => Promise<CartResult>;
    refresh: () => Promise<void>;
};

const EMPTY_CART: Cart = {
    lines: [],
    orderWeightLb: 0,
    subtotal: 0,
    deliveryFee: 0,
    total: 0,
    overweight: false,
};

const CartContext = createContext<CartContextValue | null>(null);

type ServerResponse = { ok: true; cart: Cart } | { ok: false; message: string };

async function requestCart(url: string, options?: RequestInit): Promise<ServerResponse> {
    try {
        const response = await fetch(url, {
            ...options,
            credentials: "include",
        });

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            return {
                ok: false,
                message:
                    data.message ||
                    data.error ||
                    "Something went wrong.",
            };
        }

        return {
            ok: true,
            cart: data,
        };
    } catch {
        return {
            ok: false,
            message: "Could not connect to the server.",
        };
    }
}

export function CartProvider({ children }: { children: ReactNode; }) {
    const { user } = useAuth();

    const [cart, setCart] = useState<Cart>(EMPTY_CART);

    // Load the cart when the user logs in
    useEffect(() => {
        if (!user) {
            setCart(EMPTY_CART);
            return;
        }

        let cancelled = false;

        requestCart("/api/cart").then((result) => {
            if (cancelled) return;

            if (result.ok) {
                setCart(result.cart);
            }
        });

        return () => {
            cancelled = true;
        };
    }, [user?.id]);

    // set the quantity of a product
    const setQuantity = async (productId: number, quantity: number): Promise<CartResult> => {
        if (!user) {
            return {
                ok: false,
                message: "Please log in first.",
            };
        }

        const safeQuantity = Math.max(0, quantity);

        const result = await requestCart(
            `/api/cart/items/${productId}`,
            {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    quantity: safeQuantity,
                }),
            }
        );

        if (!result.ok) {
            return result;
        }

        setCart(result.cart);

        return { ok: true };
    }

    // update a product quantity by an amount
    const changeBy = async (productId: number, amount: number): Promise<CartResult> => {
        const currentQuantity =
            cart.lines.find(
                (line) => line.productId === productId
            )?.quantity ?? 0;

        return setQuantity(
            productId,
            currentQuantity + amount
        );
    }

    // clear the cart
    const clear = async (): Promise<CartResult> => {
        if (!user) {
            return {
                ok: false,
                message: "Please log in first.",
            };
        }

        const result = await requestCart("/api/cart", {
            method: "DELETE",
        });

        if (!result.ok) {
            return result;
        }

        setCart(result.cart);

        return { ok: true };
    }

    // refetch the cart
    const refresh = async (): Promise<void> => {
        const result = await requestCart("/api/cart");

        if (result.ok) {
            setCart(result.cart);
        }
    }

    const count = cart.lines
        .filter((line) => !line.unavailable)
        .reduce(
            (total, line) => total + line.quantity,
            0
        );

    // get the quantity of a product
    const quantityOf = (productId: number): number => {
        return (
            cart.lines.find(
                (line) => line.productId === productId
            )?.quantity ?? 0
        );
    }

    const value: CartContextValue = {
        cart,
        count,
        quantityOf,
        changeBy,
        setQuantity,
        clear,
        refresh,
    };

    return (
        <CartContext.Provider value={value}>
            {children}
        </CartContext.Provider>
    );
}

export function useCart(): CartContextValue {
    const context = useContext(CartContext);

    if (!context) {
        throw new Error(
            "useCart must be used inside CartProvider"
        );
    }

    return context;
}