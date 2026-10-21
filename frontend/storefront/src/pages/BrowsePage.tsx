import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";

import CartPreview from "../components/CartPreview";
import ProductDetails from "../components/ProductDetails";

import { useAuth } from "../AuthContext";
import { useCart, type CartResult } from "../CartContext";

// what GET /api/products gives u for each product
export type Product = {
    id: number;
    name: string;
    category: string;
    description: string | null;
    price: number;
    weightLb: number;
    stock: number;
    imageUrl: string | null;
};

// load products
function useProducts() {

    const [products, setProducts] = useState<Product[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetch("/api/products")
            .then((res) => (res.ok ? (res.json() as Promise<Product[]>) : Promise.reject()))
            .then(setProducts)
            .catch(() => setError("Could not load products. Check that the backend is running."))
            .finally(() => setLoading(false));
    }, []);

    return { products, loading, error };
}

export default function BrowsePage() {
    const { user } = useAuth();
    const navigate = useNavigate();
    const { products, loading, error } = useProducts();
    const {
        quantityOf,
        setQuantity,
        clear,
        count,
        cart,
        loading: cartLoading,
        error: cartLoadError,
    } = useCart();

    const [cartError, setCartError] = useState<string | null>(null);
    const [busy, setBusy] = useState(false);
    const [selectedProduct, setSelectedProduct] = useState<Product | null>(
        null,
    );
    const [previewOpen, setPreviewOpen] = useState(false);
    const [notice, setNotice] = useState<string | null>(null);

    const [search, setSearch] = useState<string>(""); // searchbar val
    const [category, setCategory] = useState<string>("All"); // current category
    // create categories dynamically
    const categories = ["All", ...new Set(products.map((p) => p.category))];
    // filter by category and search
    const visible = products.filter((product) => {
        const matchesSearch = product.name
            .toLowerCase()
            .includes(search.trim().toLowerCase());
        const matchesCategory =
            category === "All" || product.category === category;
        return matchesSearch && matchesCategory;
    });

    const cartDisabled = busy || user === undefined || cartLoading || cartLoadError !== null;

    // Scroll after React has made the mobile cart preview visible.
    useEffect(() => {
        if (previewOpen) {
            document.getElementById("browse-cart-preview")?.scrollIntoView({
                behavior: "smooth",
                block: "start",
            });
        }
    }, [previewOpen]);

    // Both the product popup and preview use this one server-confirmed update.
    async function saveQuantity(
        productId: number,
        quantity: number,
    ): Promise<CartResult> {
        if (!user) {
            navigate("/login", { state: { from: "/browse" } });
            return { ok: false, message: "Please sign in to save your cart." };
        }
        if (busy || cartLoading)
            return {
                ok: false,
                message: "Please wait for your cart to finish updating.",
            };
        if (cartLoadError) return { ok: false, message: cartLoadError };
        setBusy(true);
        setCartError(null);
        setNotice(null);
        try {
            const result = await setQuantity(productId, quantity);
            if (!result.ok) setCartError(result.message);
            else setNotice("Cart updated.");
            return result;
        } finally {
            setBusy(false);
        }
    }

    async function handleAdd(productId: number) {
        await saveQuantity(productId, quantityOf(productId) + 1);
    }

    async function emptyCart() {
        if (cartDisabled) return;
        setBusy(true);
        setCartError(null);
        setNotice(null);
        try {
            const result = await clear();
            if (!result.ok) setCartError(result.message);
            else setNotice("Cart emptied.");
        } finally {
            setBusy(false);
        }
    }

    function openProduct(product: Product) {
        setCartError(null);
        setNotice(null);
        setSelectedProduct(product);
    }

    return (
        <div className="max-w-5xl mx-auto px-4 pt-6 pb-24 lg:pb-6">
            {/**banner if user isnt signed in  */}
            {!user && <RegisterBanner />}

            {/** hi user!!! */}
            {user && (
                <p className="mb-1 text-sm text-brand-900/60">
                    Hi {user.name}!
                </p>
            )}

            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                <h1 className="font-display text-2xl font-bold">
                    Browse Products
                </h1>
                <button
                    type="button"
                    aria-expanded={previewOpen}
                    aria-controls="browse-cart-preview"
                    onClick={() => setPreviewOpen(!previewOpen)}
                    className="rounded-full bg-brand-50 px-4 py-2 text-sm font-medium text-brand-700 hover:bg-brand-100 lg:hidden"
                >
                    {previewOpen ? "Hide cart" : "Preview cart"}
                    {user ? ` (${count})` : ""}
                </button>
            </div>

            <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_18rem]">
                <section className="min-w-0" aria-label="Product catalog">
                    <input
                        type="search"
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        placeholder="Search products"
                        aria-label="Search products"
                        className="w-full sm:w-72 mb-4 border border-brand-200 rounded-full px-4 py-2 text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none transition"
                    />

                    {categories.length > 2 && (
                        <div className="flex flex-wrap gap-2 mb-4">
                            {categories.map((c) => (
                                <button
                                    key={c}
                                    onClick={() => setCategory(c)}
                                    aria-pressed={c === category}
                                    className={`px-3 py-1.5 rounded-full text-sm font-medium cursor-pointer ${c === category
                                        ? "bg-brand-600 text-white"
                                        : "bg-brand-50 text-brand-700 hover:bg-brand-100"
                                        }`}
                                >
                                    {c}
                                </button>
                            ))}
                        </div>
                    )}

                    {loading && <p className="text-brand-900/60">Loading…</p>}
                    {error && (
                        <p role="alert" className="text-sm text-red-600">
                            {error}
                        </p>
                    )}
                    {!loading && !error && products.length === 0 && (
                        <p className="text-brand-900/60">
                            No products available.
                        </p>
                    )}
                    {!loading &&
                        !error &&
                        products.length > 0 &&
                        visible.length === 0 && (
                            <p className="text-brand-900/60">
                                No products match your search.
                            </p>
                        )}

                    {cartError && (
                        <p role="alert" className="mb-4 text-sm text-red-600">
                            {cartError}
                        </p>
                    )}
                    {notice && (
                        <p
                            role="status"
                            className="mb-4 text-sm text-brand-700"
                        >
                            {notice}
                        </p>
                    )}

                    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-3 gap-4">
                        {visible.map((p) => (
                            <ProductTile
                                key={p.id}
                                product={p}
                                quantityInCart={quantityOf(p.id)}
                                disabled={cartDisabled}
                                onAdd={handleAdd}
                                onOpen={() => openProduct(p)}
                            />
                        ))}
                    </div>
                </section>
                <div
                    id="browse-cart-preview"
                    className={`${previewOpen ? "block" : "hidden"} order-first lg:order-none lg:block lg:sticky lg:top-24`}
                >
                    <CartPreview
                        busy={busy}
                        message={cartError}
                        onChange={saveQuantity}
                        onClear={emptyCart}
                    />
                </div>
            </div>

            {selectedProduct && (
                <ProductDetails
                    key={selectedProduct.id}
                    product={selectedProduct}
                    quantityInCart={user ? quantityOf(selectedProduct.id) : 0}
                    busy={busy}
                    signedIn={!!user}
                    sessionLoading={user === undefined}
                    cartLoading={cartLoading}
                    cartError={cartLoadError}
                    onSave={saveQuantity}
                    onClose={() => setSelectedProduct(null)}
                />
            )}
            {user && !previewOpen && cart.lines.length > 0 && (
                <button
                    type="button"
                    onClick={() => setPreviewOpen(true)}
                    className="fixed bottom-4 left-1/2 z-20 flex -translate-x-1/2 items-center gap-3 whitespace-nowrap rounded-full bg-brand-800 px-5 py-3 text-sm font-medium text-white shadow-lg shadow-brand-900/20 hover:bg-brand-900 lg:hidden"
                >
                    {count} item{count === 1 ? "" : "s"} ·{" "}
                    {money.format(cart.subtotal)} <span>Preview cart ↑</span>
                </button>
            )}
        </div>
    );
}


// show banner if user isn't logged in
function RegisterBanner() {
    return (
        <div className="mb-4 rounded-2xl bg-brand-50 p-4 text-sm text-brand-900/80">
            New here?{" "}
            <Link to="/register" className="font-medium text-brand-700 underline">
                Create an account
            </Link>{" "}
            to add items to your cart.
        </div>
    )
}

type ProductTileProps = {
    product: Product;
    quantityInCart?: number;
    disabled: boolean;
    onAdd: (productId: number) => Promise<void>;
    onOpen: () => void;
};

const money = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });

function ProductTile({ product, quantityInCart = 0, disabled, onAdd, onOpen }: ProductTileProps) {
    const outOfStock: boolean = product.stock <= 0;

    return (
        <div className="bg-white border border-brand-100 rounded-3xl p-4 flex flex-col gap-2 hover:shadow-md hover:shadow-brand-900/5 transition-shadow duration-200">
            <button
                type="button"
                onClick={onOpen}
                aria-label={`View details for ${product.name}`}
                className="flex flex-1 cursor-pointer flex-col gap-2 rounded-2xl text-left focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-brand-600"
            >
                {product.imageUrl ? (
                    <img
                        src={product.imageUrl}
                        alt={product.name}
                        loading="lazy"
                        className="w-full aspect-square rounded-2xl object-cover"
                    />
                ) : (
                    <div
                        className="w-full aspect-square rounded-2xl bg-brand-50 text-brand-700 flex items-center justify-center text-3xl font-display font-bold"
                        aria-hidden="true"
                    >
                        {product.name[0]}
                    </div>
                )}

                <div className="font-medium text-sm leading-snug">
                    {product.name}
                </div>

                <div className="text-xs text-brand-900/50">
                    {product.weightLb} lb · {product.category}
                </div>
                <span className="text-xs font-medium text-brand-700">
                    View details →
                </span>
            </button>

            <div className="flex items-center justify-between mt-1">
                <span className="font-semibold">
                    {money.format(product.price)}
                </span>
                {outOfStock ? (
                    <span className="text-xs text-red-600 font-medium">
                        Out of stock
                    </span>
                ) : (
                    <button
                        type="button"
                        disabled={
                            disabled ||
                            quantityInCart >= product.stock ||
                            quantityInCart >= 999
                        }
                        onClick={() => onAdd(product.id)}
                        className="text-xs font-medium bg-brand-600 hover:bg-brand-700 disabled:bg-gray-400 text-white rounded-full px-3 py-1.5"
                    >
                        {quantityInCart > 0
                            ? `In cart (${quantityInCart})`
                            : "Add"}
                    </button>
                )}
            </div>
        </div>
    );
}
