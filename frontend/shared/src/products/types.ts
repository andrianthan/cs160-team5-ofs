// What GET /api/products returns for each product. Both apps read this shape.
// (`updated_at` is the one field the backend sends in snake_case.)
export type Product = {
    id: number;
    name: string;
    category: string;
    description: string | null;
    price: number;
    weightLb: number;
    stock: number;
    imageUrl: string | null;
    active: boolean;
    updated_at: string;
};
