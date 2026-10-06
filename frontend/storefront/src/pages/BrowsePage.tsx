import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../AuthContext";


export default function BrowsePage() {
    const { user } = useAuth();
    const navigate = useNavigate();

    // searchbar value
    const [ search, setSearch ] = useState<string>("");

    const handleAdd = (productId: string) => {
        if (!user) {
            return navigate("/login", { state: { from: "/browse" } });
        }

        // handle add to cart
    };

    return(
        <div className="">
            {/**banner if user isnt signed in  */}
            {!user && (<RegisterBanner/>)}

            {user && (
                <div className="">
                    
                </div>
            )}
        </div>
    );
}


// show banner if user isn't logged in
function RegisterBanner() {
    return(
        <div className="">

        </div>
    )
}

export type Product = {
    id: string;
    name: string;
    category: string;
    price: number;
    weightLb: number;
    stock: number;
    imageUrl?: string;
};

type ProductTileProps = {
    product : Product;
    quantityInCart?: number;
    onAdd: (productId: string) => void;
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
                    {product.name}
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