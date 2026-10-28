import { useState } from "react";
import { useAuth } from "@ofs/shared";

import type { Product } from "@ofs/shared/products";

import type { ProductInput } from "../api/products";
import { useProducts } from "../hooks/useProducts";

const money = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });

export default function InventoryPage() {
    const { user } = useAuth();

    const { products, loading, error, update } = useProducts();

    const [search, setSearch] = useState<string>("");

    const [category, setCategory] = useState<string>("All"); // current category
    const [savingId, setSavingId] = useState<number | null>(null); // product being saved right now
    const [message, setMessage] = useState<string | null>(null);

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

    // only managers can change products (the server enforces this too)
    const isManager = user?.role === "manager";

    // save a change, then show the server's answer. the list updates itself from the reply
    const save = async (product: Product, changes: Partial<ProductInput>) => {
        setMessage(null);
        setSavingId(product.id);

        const result = await update(product.id, changes);
        if (!result.ok) {
            setMessage(`Could not save ${product.name}: ${result.data.message}`);
        }

        setSavingId(null);
    };

    return (
        <main className="max-w-5xl mx-auto px-4 py-6">
            <h1 className="font-display text-2xl font-bold mb-4">Inventory</h1>

            {/** search bar */}
            <input
                type="search"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search products"
                aria-label="Search products"
                className="w-full sm:w-72 mb-4 border border-brand-200 rounded-full px-4 py-2 text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none transition"
            />

            {/** filter by category */}
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

            {user && !isManager && (
                <p className="mb-4 text-sm text-brand-900/60">
                    View only. Managers can change stock and prices.
                </p>
            )}

            {loading && <p className="text-brand-900/60">Loading…</p>}
            {error && (
                <p role="alert" className="text-sm text-red-600">
                    {error}
                </p>
            )}
            {message && (
                <p role="alert" className="mb-3 text-sm text-red-600">
                    {message}
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

            {/** list all products */}
            <div>
                {visible.map((product) => (
                    <ProductRow
                        key={product.id}
                        product={product}
                        managerControls={isManager}
                        saving={savingId === product.id}
                        onSave={save}
                    />
                ))}
            </div>
        </main>
    );
}

type ProductRowProps = {
    product: Product;
    managerControls: boolean;
    saving: boolean;
    onSave: (product: Product, changes: Partial<ProductInput>) => void;
};

function ProductRow({ product, managerControls, saving, onSave }: ProductRowProps) {
    return (
        <div className="flex items-center justify-between gap-4 border-b border-brand-100 py-3">
            <div className="min-w-0">
                <p className="font-medium truncate">{product.name}</p>
                <p className="text-xs text-brand-900/50">{product.category}</p>
            </div>

            {!managerControls && (
                <div className="flex items-center gap-6 text-sm">
                    <span>{money.format(product.price)}</span>
                    <span>{product.stock} in stock</span>
                </div>
            )}

            {managerControls && (
                <div className="flex items-center gap-6 text-sm">
                    <label className="flex items-center gap-1">
                        $
                        <NumberField
                            kind="money"
                            label={`Price of ${product.name}`}
                            value={product.price}
                            disabled={saving}
                            onCommit={(price) => onSave(product, { price })}
                        />
                    </label>

                    <div className="flex items-center gap-2">
                        <button
                            type="button"
                            aria-label={`Decrease stock of ${product.name}`}
                            disabled={saving || product.stock <= 0}
                            onClick={() => onSave(product, { stock: product.stock - 1 })}
                            className="w-8 h-8 rounded-lg border border-brand-200 hover:bg-brand-50 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer transition-colors duration-200"
                        >
                            –
                        </button>
                        <NumberField
                            kind="whole"
                            label={`Stock of ${product.name}`}
                            value={product.stock}
                            disabled={saving}
                            onCommit={(stock) => onSave(product, { stock })}
                        />
                        <button
                            type="button"
                            aria-label={`Increase stock of ${product.name}`}
                            disabled={saving}
                            onClick={() => onSave(product, { stock: product.stock + 1 })}
                            className="w-8 h-8 rounded-lg border border-brand-200 hover:bg-brand-50 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer transition-colors duration-200"
                        >
                            +
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}

type NumberFieldProps = {
    kind: "whole" | "money";
    label: string;
    value: number;
    disabled: boolean;
    onCommit: (value: number) => void;
};

function NumberField({ kind, label, value, disabled, onCommit }: NumberFieldProps) {
    const [draft, setDraft] = useState<string | null>(null);

    const commit = () => {
        const typed = draft === null || draft.trim() === "" ? NaN : Number(draft);
        setDraft(null);
        if (!Number.isNaN(typed) && typed !== value) onCommit(typed);
    };

    return (
        <input
            type="text"
            inputMode={kind === "money" ? "decimal" : "numeric"}
            aria-label={label}
            value={draft ?? (kind === "money" ? value.toFixed(2) : String(value))}
            disabled={disabled}
            // only digits (and one dot for money) can be typed
            onChange={(e) => setDraft(e.target.value.replace(kind === "money" ? /[^\d.]/g : /\D/g, ""))}
            onBlur={commit}
            onKeyDown={(e) => {
                if (e.key === "Enter") e.currentTarget.blur();
            }}
            className="w-20 h-8 text-center text-sm rounded-lg border border-brand-200 focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none disabled:opacity-50"
        />
    );
}