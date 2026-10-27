import { BrowserRouter, Routes, Route, Navigate, useLocation, NavLink } from "react-router-dom";
import { AuthProvider, RequireAuth, useAuth } from "@ofs/shared/auth";
import {
  AccountMenu,
  AppHeader,
  NavPill,
  PageStub,
} from "@ofs/shared/components";

import { CartProvider } from "./CartContext";

import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import BrowsePage from "./pages/BrowsePage";
import CartPage from "./pages/CartPage";
import CartMenu from "./components/CartMenu";

function Nav() {
  const { user } = useAuth();
  const { pathname } = useLocation();

  return (
    <AppHeader
      width="max-w-5xl"
      brand={<NavLink to="/browse">OFS</NavLink>}
    >
      <NavPill to="/browse">Browse</NavPill>
      <CartMenu key={pathname} />
      <NavPill to="/track">Track</NavPill>
      {user && <AccountMenu />}
      {user === null && (
        <div className="flex gap-1">
          <NavPill to="/login">Sign in</NavPill>
          <NavLink
            to="/register"
            className="rounded-full bg-brand-600 px-3 py-2 text-sm font-medium text-white"
          >
            Register
          </NavLink>
        </div>
      )}
    </AppHeader>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider portal="customer">
        <CartProvider>
          <Nav />
          <Routes>
            <Route path="/" element={<Navigate to="/browse" replace />} />
            <Route
              path="/login"
              element={
                <LoginPage />
              }
            />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/browse" element={
              <BrowsePage />}
            />
            <Route path="/cart" element={
              <RequireAuth>
                <CartPage />
              </RequireAuth>
            }
            />
            <Route
              path="/checkout"
              element={
                <RequireAuth>
                  <PageStub title="Checkout" task="T08 / T10 / T11" owner="Andrian" />
                </RequireAuth>
              }
            />
            <Route
              path="/track"
              element={
                <RequireAuth>
                  <PageStub title="Track Orders" task="T16" owner="Jorge" />
                </RequireAuth>
              }
            />
          </Routes>
        </CartProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}
