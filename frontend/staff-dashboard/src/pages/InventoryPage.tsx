import { useEffect, useState } from "react";
import { useAuth } from "@ofs/shared";

import type { Product } from "@ofs/shared/products";

import type { ProductInput } from "../api/products";
import { useProducts } from "../hooks/useProducts";

const money = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });

export default function InventoryPage() {
    const { user } = useAuth();

    const { products, loading, error, update, create, del } = useProducts();

    const [search, setSearch] = useState<string>("");

    const [category, setCategory] = useState<string>("All"); // current category
    const [savingId, setSavingId] = useState<number | null>(null); // product being saved right now
    const [message, setMessage] = useState<string | null>(null);
    const [editingId, setEditingId] = useState<number | null>(null); // product open in the edit dialog
    const [showCreate, setShowCreate] = useState(false); // is the "new product" dialog open
    const [savingNew, setSavingNew] = useState(false);

    // create categories dynamically
    const categories = ["All", ...new Set(products.map((p) => p.category))];
    // filter by category and search
    const visible = products.filter((product) => {
        const matchesSearch = product.name
            .toLowerCase()
            .includes(search.trim().toLowerCase());

        const matchesCategory = category === "All" || product.category === category;

        return matchesSearch && matchesCategory;
    });

    // only managers can change products (the server enforces this too)
    const isManager = user?.role === "manager";

    // The product being edited. Looked up from the list each render, so if the server's answer
    // removes it (deactivated), the dialog disappears on its own.
    const editing = products.find((p) => p.id === editingId);

    // send a change. returns an error message, or null when it worked.
    // the list updates itself from the server's reply
    const send = async (product: Product, changes: Partial<ProductInput>): Promise<string | null> => {
        setSavingId(product.id);
        const result = await update(product.id, changes);
        setSavingId(null);
        return result.ok ? null : `Could not save ${product.name}: ${result.data.message}`;
    };

    // for the inline price / stock controls: errors show at the top of the page
    const save = async (product: Product, changes: Partial<ProductInput>) => {
        setMessage(null);
        setMessage(await send(product, changes));
    };

    // set out of stock items as inactive
    const outOfStock = products.filter((p) => p.active && p.stock <= 0);
    const deactivateOutOfStock = async () => {
        setMessage(null);

        for (const prod of outOfStock) {
            const error = await send(prod, { active: false });
            if (error) {
                return setMessage(error);
            }
        }

    }

    // create a new product. returns an error message, or null when it worked.
    // the hook adds the server's version to the list
    const createNewProduct = async (input: ProductInput): Promise<string | null> => {
        setMessage(null);
        setSavingNew(true);
        const result = await create(input);
        setSavingNew(false);
        return result.ok ? null : `Could not create product: ${result.data.message}`;
    };

    // delete product
    const handleDelete = async (product: Product) => {
        if (!window.confirm(`Delete ${product.name}? This cannot be undone.`)) return;

        setMessage(null);

        const result = await del(product.id);

        if (!result.ok) setMessage(`Could not delete product: ${result.data.message}`);
    };

    return (
        <main className="max-w-5xl mx-auto px-4 py-6">
            <h1 className="font-display text-2xl font-bold mb-4">Inventory</h1>

            <div className="flex justify-between">
                {/** search bar */}
                <input
                    type="search"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Search products"
                    aria-label="Search products"
                    className="w-full sm:w-72 mb-4 border border-brand-200 rounded-full px-4 py-2 text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none transition"
                />

                {isManager && (
                    <div>
                        {/** auto inactive */}
                        <button
                            type="button"
                            onClick={deactivateOutOfStock}
                            disabled={savingId !== null || outOfStock.length === 0}
                            className="px-3 py-1.5 my-2 rounded-full text-sm font-medium cursor-pointer bg-brand-50 text-brand-700 hover:bg-brand-100 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            Set out-of-stock products inactive ({outOfStock.length})
                        </button>

                        {/** create product */}
                        <button
                            type="button"
                            onClick={() => {
                                setMessage(null);
                                setShowCreate(true);
                            }}
                            className="ml-2 px-3 py-1.5 my-2 rounded-full text-sm font-medium cursor-pointer bg-brand-600 text-white hover:bg-brand-700"
                        >
                            Create New Product
                        </button>
                    </div>

                )}

            </div>


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
                        onOpen={() => {
                            setMessage(null);
                            setEditingId(product.id);
                        }}
                        onDelete={handleDelete}
                    />
                ))}
            </div>

            {/** edit dialog (managers only). keyed so its fields reset for each product */}
            {isManager && editing && (
                <EditProductDialog
                    key={editing.id}
                    product={editing}
                    saving={savingId === editing.id}
                    onSave={(changes) => send(editing, changes)}
                    onClose={() => setEditingId(null)}
                />
            )}

            {/** new product dialog (managers only) */}
            {isManager && showCreate && (
                <CreateProductDialog
                    categories={categories.filter((c) => c !== "All")}
                    saving={savingNew}
                    onSave={createNewProduct}
                    onClose={() => setShowCreate(false)}
                />
            )}
        </main>
    );
}

type ProductRowProps = {
    product: Product;
    managerControls: boolean;
    saving: boolean;
    onSave: (product: Product, changes: Partial<ProductInput>) => void;
    onOpen: () => void;
    onDelete: (product: Product) => void;
};

function ProductRow({ product, managerControls, saving, onSave, onOpen, onDelete }: ProductRowProps) {
    return (
        <div
            className={
                `flex items-center justify-between gap-4 border-b border-brand-100 py-3 
                ${product.active ? "" : "opacity-50 bg-brand-50/50"}
                ${product.stock <= 0 ? "text-red-500" : product.stock <= 10 ? "text-orange-500" : ""}`
            }
        >
            <div className="min-w-0">
                {managerControls ? (
                    // the name is the button that opens the edit dialog
                    <button
                        type="button"
                        onClick={onOpen}
                        aria-label={`Edit ${product.name}`}
                        className="block max-w-full text-left cursor-pointer group"
                    >
                        <span className="block font-medium truncate group-hover:underline">{product.name}</span>
                        <span className="block text-xs text-brand-900/50">{product.category} · Edit</span>
                    </button>
                ) : (
                    <>
                        <p className="font-medium truncate">{product.name}</p>
                        <p className="text-xs text-brand-900/50">{product.category}</p>
                    </>
                )}
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

                    {/** delete product */}
                    <button
                        type="button"
                        disabled={saving}
                        aria-label={`Delete ${product.name}`}
                        title="Delete product"
                        className="w-8 h-8 flex items-center justify-center rounded-lg border border-brand-200 text-brand-700 hover:bg-red-50 hover:text-red-600 hover:border-red-200 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer transition-colors duration-200"
                        onClick={() => { onDelete(product) }}
                    >
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            viewBox="0 0 24 24"
                            width="16"
                            height="16"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            aria-hidden="true"
                        >
                            <path d="M3 6h18" />
                            <path d="M8 6V4h8v2" />
                            <path d="M19 6l-1 14H6L5 6" />
                            <path d="M10 11v6M14 11v6" />
                        </svg>

                    </button>
                </div>
            )}
        </div>
    );
}

type EditProductDialogProps = {
    product: Product;
    saving: boolean;
    onSave: (changes: Partial<ProductInput>) => Promise<string | null>; // error message, or null on success
    onClose: () => void;
};

const inputClass =
    "w-full border border-brand-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none disabled:opacity-50";

// A form for name, description, price, weight and availability.
// Only the fields you actually changed are sent.
function EditProductDialog({ product, saving, onSave, onClose }: EditProductDialogProps) {
    // everything is typed as text, and checked when you press Save
    const [name, setName] = useState(product.name);
    const [description, setDescription] = useState(product.description ?? "");
    const [price, setPrice] = useState(product.price.toFixed(2));
    const [weight, setWeight] = useState(String(product.weightLb));
    const [category, setCategory] = useState<string>(String(product.category));
    const [available, setAvailable] = useState(product.active);
    const [problem, setProblem] = useState<string | null>(null);

    // Escape closes the dialog
    useEffect(() => {
        const onKey = (e: KeyboardEvent) => {
            if (e.key === "Escape" && !saving) onClose();
        };
        window.addEventListener("keydown", onKey);
        return () => window.removeEventListener("keydown", onKey);
    }, [saving, onClose]);

    const submit = async (e: React.FormEvent) => {
        e.preventDefault();
        setProblem(null);

        // check each field, same rules as the server
        const cleanName = name.trim();
        if (cleanName === "") return setProblem("Name is required.");
        if (cleanName.length > 160) return setProblem("Name must be 160 characters or fewer.");

        if (!/^\d+(\.\d{1,2})?$/.test(price.trim())) {
            return setProblem("Price must be a number with at most 2 decimals, like 4.50.");
        }
        const newPrice = Number(price);

        const newWeight = Number(weight);
        if (weight.trim() === "" || !Number.isFinite(newWeight) || newWeight <= 0) {
            return setProblem("Weight must be a number greater than 0.");
        }

        // collect only what changed
        const changes: Partial<ProductInput> = {};
        if (cleanName !== product.name) changes.name = cleanName;
        const cleanDescription = description.trim();
        if (cleanDescription !== (product.description ?? "")) {
            changes.description = cleanDescription === "" ? null : cleanDescription;
        }
        const cleanCategory = category.trim()
        if (cleanCategory !== (product.category)) {
            changes.category = cleanCategory;
        }
        if (newPrice !== product.price) changes.price = newPrice;
        if (newWeight !== product.weightLb) changes.weightLb = newWeight;
        if (available !== product.active) changes.active = available;

        if (Object.keys(changes).length === 0) return onClose(); // nothing to save

        const error = await onSave(changes);
        if (error) setProblem(error); // stay open so nothing typed is lost
        else onClose();
    };

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
            onMouseDown={(e) => {
                // a click on the dark backdrop (not the card) closes it
                if (e.target === e.currentTarget && !saving) onClose();
            }}
        >
            <form
                role="dialog"
                aria-modal="true"
                aria-labelledby="edit-product-title"
                onSubmit={submit}
                className="w-full max-w-md max-h-full overflow-y-auto bg-white rounded-3xl p-6 flex flex-col gap-4 shadow-xl"
            >
                <h2 id="edit-product-title" className="font-display text-xl font-bold">
                    Edit product
                </h2>

                <label className="flex flex-col gap-1 text-sm font-medium">
                    Name
                    <input
                        autoFocus
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        disabled={saving}
                        className={inputClass}
                    />
                </label>

                <label className="flex flex-col gap-1 text-sm font-medium">
                    Description
                    <textarea
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        disabled={saving}
                        rows={3}
                        className={inputClass}
                    />
                </label>

                <div className="grid grid-cols-2 gap-4">
                    <label className="flex flex-col gap-1 text-sm font-medium">
                        Price ($)
                        <input
                            inputMode="decimal"
                            value={price}
                            onChange={(e) => setPrice(e.target.value)}
                            disabled={saving}
                            className={inputClass}
                        />
                    </label>
                    <label className="flex flex-col gap-1 text-sm font-medium">
                        Weight (lb)
                        <input
                            inputMode="decimal"
                            value={weight}
                            onChange={(e) => setWeight(e.target.value)}
                            disabled={saving}
                            className={inputClass}
                        />
                    </label>
                </div>

                <label className="flex flex-col gap-1 text-sm font-medium">
                    Category
                    <input
                        value={category}
                        onChange={(e) => setCategory(e.target.value)}
                        disabled={saving}
                        className={inputClass}
                    />
                </label>

                <label className="flex items-start gap-2 text-sm">
                    <input
                        type="checkbox"
                        checked={available}
                        onChange={(e) => setAvailable(e.target.checked)}
                        disabled={saving}
                        className="mt-0.5"
                    />
                    <span>
                        <span className="font-medium">Available to customers</span>
                        {!available && (
                            <span className="block text-xs text-brand-900/60">
                                Customers won't see this product.
                            </span>
                        )}
                    </span>
                </label>

                {problem && (
                    <p role="alert" className="text-sm text-red-600">
                        {problem}
                    </p>
                )}

                <div className="flex justify-end gap-2">
                    <button
                        type="button"
                        onClick={onClose}
                        disabled={saving}
                        className="px-4 py-2 rounded-full text-sm font-medium bg-brand-50 text-brand-700 hover:bg-brand-100 disabled:opacity-50 cursor-pointer transition-colors duration-200"
                    >
                        Cancel
                    </button>
                    <button
                        type="submit"
                        disabled={saving}
                        className="px-4 py-2 rounded-full text-sm font-medium bg-brand-600 hover:bg-brand-700 text-white disabled:opacity-50 cursor-pointer transition-colors duration-200"
                    >
                        {saving ? "Saving…" : "Save"}
                    </button>
                </div>
            </form>
        </div>
    );
}

type CreateProductDialogProps = {
    categories: string[]; // existing categories, offered as suggestions
    saving: boolean;
    onSave: (input: ProductInput) => Promise<string | null>; // error message, or null on success
    onClose: () => void;
};

// A form for a new product. Everything is typed as text and checked when you press Save.
function CreateProductDialog({ categories, saving, onSave, onClose }: CreateProductDialogProps) {
    const [form, setForm] = useState({
        name: "",
        category: "",
        description: "",
        price: "",
        weightLb: "",
        stock: "0",
        lowStockThreshold: "5",
        active: true,
    });
    const [problem, setProblem] = useState<string | null>(null);

    // one helper instead of a separate onChange per field
    const set = (field: keyof typeof form, value: string | boolean) =>
        setForm((prev) => ({ ...prev, [field]: value }));

    // Escape closes the dialog
    useEffect(() => {
        const onKey = (e: KeyboardEvent) => {
            if (e.key === "Escape" && !saving) onClose();
        };
        window.addEventListener("keydown", onKey);
        return () => window.removeEventListener("keydown", onKey);
    }, [saving, onClose]);

    const submit = async (e: React.FormEvent) => {
        e.preventDefault(); // without this the browser reloads the page
        setProblem(null);

        // check each field, same rules as the server
        const name = form.name.trim();
        if (name === "") return setProblem("Name is required.");
        if (name.length > 160) return setProblem("Name must be 160 characters or fewer.");

        const category = form.category.trim();
        if (category === "") return setProblem("Category is required.");
        if (category.length > 80) return setProblem("Category must be 80 characters or fewer.");

        if (!/^\d+(\.\d{1,2})?$/.test(form.price.trim())) {
            return setProblem("Price must be a number with at most 2 decimals, like 4.50.");
        }

        const weightLb = Number(form.weightLb);
        if (form.weightLb.trim() === "" || !Number.isFinite(weightLb) || weightLb <= 0) {
            return setProblem("Weight must be a number greater than 0.");
        }

        if (!/^\d+$/.test(form.stock.trim())) return setProblem("Stock must be a whole number.");
        if (!/^\d+$/.test(form.lowStockThreshold.trim())) {
            return setProblem("Low-stock alert must be a whole number.");
        }

        const description = form.description.trim();
        const error = await onSave({
            name,
            category,
            description: description === "" ? null : description,
            price: Number(form.price),
            weightLb,
            stock: Number(form.stock),
            lowStockThreshold: Number(form.lowStockThreshold),
            imageUrl: null,
            active: form.active,
        });
        if (error) setProblem(error); // stay open so nothing typed is lost
        else onClose();
    };

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
            onMouseDown={(e) => {
                // a click on the dark backdrop (not the card) closes it
                if (e.target === e.currentTarget && !saving) onClose();
            }}
        >
            <form
                role="dialog"
                aria-modal="true"
                aria-labelledby="create-product-title"
                onSubmit={submit}
                className="w-full max-w-md max-h-full overflow-y-auto bg-white rounded-3xl p-6 flex flex-col gap-4 shadow-xl"
            >
                <h2 id="create-product-title" className="font-display text-xl font-bold">
                    New product
                </h2>

                <label className="flex flex-col gap-1 text-sm font-medium">
                    Name
                    <input
                        autoFocus
                        value={form.name}
                        onChange={(e) => set("name", e.target.value)}
                        disabled={saving}
                        className={inputClass}
                    />
                </label>

                <label className="flex flex-col gap-1 text-sm font-medium">
                    Category
                    <input
                        list="category-suggestions"
                        value={form.category}
                        onChange={(e) => set("category", e.target.value)}
                        disabled={saving}
                        className={inputClass}
                    />
                    <datalist id="category-suggestions">
                        {categories.map((c) => (
                            <option key={c} value={c} />
                        ))}
                    </datalist>
                </label>

                <label className="flex flex-col gap-1 text-sm font-medium">
                    Description
                    <textarea
                        value={form.description}
                        onChange={(e) => set("description", e.target.value)}
                        disabled={saving}
                        rows={3}
                        className={inputClass}
                    />
                </label>

                <div className="grid grid-cols-2 gap-4">
                    <label className="flex flex-col gap-1 text-sm font-medium">
                        Price ($)
                        <input
                            inputMode="decimal"
                            value={form.price}
                            onChange={(e) => set("price", e.target.value)}
                            disabled={saving}
                            className={inputClass}
                        />
                    </label>
                    <label className="flex flex-col gap-1 text-sm font-medium">
                        Weight (lb)
                        <input
                            inputMode="decimal"
                            value={form.weightLb}
                            onChange={(e) => set("weightLb", e.target.value)}
                            disabled={saving}
                            className={inputClass}
                        />
                    </label>
                    <label className="flex flex-col gap-1 text-sm font-medium">
                        Stock
                        <input
                            inputMode="numeric"
                            value={form.stock}
                            onChange={(e) => set("stock", e.target.value)}
                            disabled={saving}
                            className={inputClass}
                        />
                    </label>
                    <label className="flex flex-col gap-1 text-sm font-medium">
                        Low-stock alert at
                        <input
                            inputMode="numeric"
                            value={form.lowStockThreshold}
                            onChange={(e) => set("lowStockThreshold", e.target.value)}
                            disabled={saving}
                            className={inputClass}
                        />
                    </label>
                </div>

                <label className="flex items-center gap-2 text-sm">
                    <input
                        type="checkbox"
                        checked={form.active}
                        onChange={(e) => set("active", e.target.checked)}
                        disabled={saving}
                    />
                    <span className="font-medium">Available to customers</span>
                </label>

                {problem && (
                    <p role="alert" className="text-sm text-red-600">
                        {problem}
                    </p>
                )}

                <div className="flex justify-end gap-2">
                    <button
                        type="button"
                        onClick={onClose}
                        disabled={saving}
                        className="px-4 py-2 rounded-full text-sm font-medium bg-brand-50 text-brand-700 hover:bg-brand-100 disabled:opacity-50 cursor-pointer transition-colors duration-200"
                    >
                        Cancel
                    </button>
                    <button
                        type="submit"
                        disabled={saving}
                        className="px-4 py-2 rounded-full text-sm font-medium bg-brand-600 hover:bg-brand-700 text-white disabled:opacity-50 cursor-pointer transition-colors duration-200"
                    >
                        {saving ? "Saving…" : "Create"}
                    </button>
                </div>
            </form>
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