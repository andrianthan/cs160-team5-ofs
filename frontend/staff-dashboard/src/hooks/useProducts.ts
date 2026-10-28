import { useCallback, useEffect, useState } from "react";

import { listAllProducts, type Product } from "@ofs/shared/products";

import { createProduct, updateProduct, type ProductInput } from "../api/products";

const byName = (a: Product, b: Product) => a.name.localeCompare(b.name);

// The product list for the dashboard, plus the actions that change it.
// After a save the list is updated from the server's reply, so there is no need to reload.
export function useProducts() {
    const [products, setProducts] = useState<Product[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const refresh = useCallback(async () => {
        const result = await listAllProducts();

        if (result.ok) {
            setProducts(result.data);
            setError(null);
        } else {
            setError(result.data.message);
        }
        setLoading(false);
    }, []);

    // first load (a zero-delay timer, the same way AuthProvider does its first check)
    useEffect(() => {
        const first = window.setTimeout(() => void refresh(), 0);
        return () => window.clearTimeout(first);
    }, [refresh]);

    // The list only holds active products (that is all GET returns), so an inactive one is left out.
    const create = async (input: ProductInput) => {
        const result = await createProduct(input);

        if (result.ok) {
            setProducts((list) => [...list, result.data].sort(byName));
        }
        return result;
    };

    const update = async (id: number, changes: Partial<ProductInput>) => {
        const result = await updateProduct(id, changes);

        if (result.ok) {
            setProducts((list) => list.map((p) => (p.id === id ? result.data : p)).sort(byName));
        }
        return result;
    };

    const deactivate = (id: number) => update(id, { active: false });

    return { products, loading, error, refresh, create, update, deactivate };
}
