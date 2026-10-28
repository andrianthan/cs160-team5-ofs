import { apiRequest } from "../api/client";
import type { Product } from "./types";

// Public: no sign-in needed. The server only lists active products, sorted by name.
export const listProducts = () => apiRequest<Product[]>("/api/products");

// Employee only
export const listAllProducts = () => apiRequest<Product[]>("/api/products/all");
