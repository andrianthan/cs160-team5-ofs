import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../AuthContext";

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

    const [ search, setSearch ] = useState<string>(""); // searchbar val
    const [ category, setCategory ] = useState<string>("All"); // current category
    // create categories dynamically
    const categories = ["All", ...new Set(products.map((p) => p.category))];
    // filter by category and search
    const q = search.trim().toLowerCase();
    const visible = products.filter(
        (p) => p.name.toLowerCase().includes(q) && (category === "All" || p.category === category)
    );

    // passed to ProductTile
    // handle when user clicks on the add button
    const handleAdd = (productId: number) => {
        // if not logged in:
        // -- redirect to login page
        if (!user) {
            return navigate("/login", {
                state: { from: "/browse" }
            });
        }

        // TODO: handle add to cart
        console.log("add to cart:", productId); // temp
    };

    return(
        <div className="max-w-5xl mx-auto px-4 py-6">
            {/**banner if user isnt signed in  */}
            {!user && (<RegisterBanner/>)}

            {/** hi user!!! */}
            {user && (
                <p className="mb-1 text-sm text-brand-900/60">Hi {user.name}!</p>
            )}

            <h1 className="font-display text-2xl font-bold mb-4">Browse Products</h1>

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
                            className={`px-3 py-1.5 rounded-full text-sm font-medium cursor-pointer ${
                                c === category ? "bg-brand-600 text-white" : "bg-brand-50 text-brand-700 hover:bg-brand-100"
                            }`}
                        >
                            {c}
                        </button>
                    ))}
                </div>
            )}

            {loading && <p className="text-brand-900/60">Loading…</p>}
            {error && <p role="alert" className="text-sm text-red-600">{error}</p>}
            {!loading && !error && products.length === 0 && (
                <p className="text-brand-900/60">No products available.</p>
            )}
            {!loading && !error && products.length > 0 && visible.length === 0 && (
                <p className="text-brand-900/60">No products match your search.</p>
            )}

            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
                {visible.map((p) => (
                    <ProductTile key={p.id} product={p} onAdd={handleAdd} />
                ))}
            </div>
        </div>
    );
}


// show banner if user isn't logged in
function RegisterBanner() {
    return(
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
    product : Product;
    quantityInCart?: number;
    onAdd: (productId: number) => void;
};

const money = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });

function ProductTile({ product, quantityInCart = 0, onAdd }: ProductTileProps) {
    const outOfStock : boolean = product.stock <= 0;

    return(
        <div className="bg-white border border-brand-100 rounded-3xl p-4 flex flex-col gap-2 hover:shadow-md hover:shadow-brand-900/5 transition-shadow duration-200">
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

            <div className="font-medium text-sm leading-snug">{product.name}</div>

            <div className="text-xs text-brand-900/50">
                {product.weightLb} lb · {product.category}
            </div>

            <div className="flex items-center justify-between mt-1">
                <span className="font-semibold">{money.format(product.price)}</span>
                {outOfStock ? (
                    <span className="text-xs text-red-600 font-medium">Out of stock</span>
                ) : (
                    <button
                        onClick={() => onAdd(product.id)}
                        className="text-xs font-medium bg-brand-600 hover:bg-brand-700 text-white rounded-full px-3 py-1.5 transition-colors duration-200 cursor-pointer"
                    >
                        {quantityInCart > 0 ? `In cart (${quantityInCart})` : "Add"}
                    </button>
                )}
            </div>
        </div>
    )
}