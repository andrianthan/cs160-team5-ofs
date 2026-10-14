import { useState, useEffect } from 'react';
import { useAuth } from "../AuthContext";

import { Link, Navigate, useNavigate, useLocation } from "react-router-dom";

export type Cart = {
    id: number;

};


export default function CartPage() {
    const { user } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();

    // check login
    if (!user) {
        const from = (location.state as { from?: string } | null)?.from ?? "/browse";
        return <Navigate to={from} replace />;
    }



    return (
        <div>

        </div>
    );
}