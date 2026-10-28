import { apiRequest, jsonRequest, type ApiResult } from "@ofs/shared/api";
import type { Product } from "@ofs/shared/products";

const PRODUCTS_URL = "/api/products";

// What a form edits. Same names as Product, so forms never deal with the backend's column names.
export type ProductInput = {
    name: string;
    category: string;
    price: number;
    weightLb: number;
    description: string | null;
    stock: number;
    lowStockThreshold: number;
    imageUrl: string | null;
    active: boolean;
};

// POST and PATCH want database column names, not the names GET returns. The backend silently
// ignores a key it does not know, so a wrong name loses the change with no error at all.
// `satisfies` makes the compiler complain if a field is added to ProductInput but not listed here.
const COLUMN = {
    name: "name",
    category: "category",
    price: "price",
    weightLb: "weight_lb",
    description: "description",
    stock: "stock_qty",
    lowStockThreshold: "low_stock_threshold",
    imageUrl: "image_url",
    active: "active",
} as const satisfies Record<keyof ProductInput, string>;

// Turns form values into the body POST/PATCH expect. Fields left undefined are not sent
// (null and false are real values and are sent), and anything that is not a product field is dropped.
export function toRequestBody(input: Partial<ProductInput>): Record<string, unknown> {
    const body: Record<string, unknown> = {};

    for (const field of Object.keys(COLUMN) as (keyof ProductInput)[]) {
        const value = input[field];
        if (value !== undefined) body[COLUMN[field]] = value;
    }

    return body;
}

// The server's 401 and 403 bodies are just "unauthorized" and "forbidden". Say it in words.
function friendly<T>(result: ApiResult<T>): ApiResult<T> {
    if (result.ok) return result;

    if (result.status === 401) {
        return { ...result, data: { ...result.data, message: "Please sign in again." } };
    }
    if (result.status === 403) {
        return { ...result, data: { ...result.data, message: "Only managers can change products." } };
    }
    return result;
}

// Managers only.
export async function createProduct(input: ProductInput) {
    return friendly(await apiRequest<Product>(PRODUCTS_URL, jsonRequest("POST", toRequestBody(input))));
}

// Managers only. Send just the fields that changed.
export async function updateProduct(id: number, changes: Partial<ProductInput>) {
    return friendly(await apiRequest<Product>(`${PRODUCTS_URL}/${id}`, jsonRequest("PATCH", toRequestBody(changes))));
}

// There is no DELETE: "removing" a product means making it inactive.
export const deactivateProduct = (id: number) => updateProduct(id, { active: false });
