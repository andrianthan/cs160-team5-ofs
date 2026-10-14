import { useState } from "react";
import { BrowserRouter, Routes, Route, Navigate, NavLink, type NavLinkRenderProps } from "react-router-dom";

import { AuthProvider, useAuth } from "./AuthContext";
import RequireAuth from "./RequireAuth";

import PageStub from "./pages/PageStub";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import BrowsePage from "./pages/BrowsePage";

// Route table from docs/part2 LLD 5 (Frontend Component Breakdown), owners from
// docs/part2/backlog.md. Replace each PageStub with the real page as it's built.
function ProfileMenu() {
  const { logout } = useAuth();
  const [open, setOpen] = useState(false);

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        aria-label="Account menu"
        className="w-9 h-9 rounded-full bg-brand-100 text-brand-700 flex items-center justify-center hover:bg-brand-200"
      >
        <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true">
          <circle cx="12" cy="8" r="4" />
          <path d="M4 20c0-4 3.6-6 8-6s8 2 8 6z" />
        </svg>
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-40 bg-white border border-brand-100 rounded-2xl shadow-lg p-1">
          <button onClick={logout} className="w-full text-left px-3 py-2 rounded-xl text-sm hover:bg-brand-50">
            Log out
          </button>
        </div>
      )}
    </div>
  );
}

function Nav() {
  const { user } = useAuth();

  const link = ({ isActive }: NavLinkRenderProps) =>
    `px-3 py-2 rounded-full text-sm font-medium ${isActive ? "bg-brand-50 text-brand-700" : "text-brand-900/60"}`;
  return (
    <header className="sticky top-0 bg-white/90 backdrop-blur border-b border-brand-100">
      <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between">
        <span className="font-display font-bold text-brand-700 text-lg">OFS</span>
        <nav className="flex gap-1">
          <NavLink to="/browse" className={link}>Browse</NavLink>
          <NavLink to="/cart" className={link}>Cart</NavLink>
          <NavLink to="/track" className={link}>Track</NavLink>
          {user && <ProfileMenu />}
          {user === null && (
            <div className="flex gap-1">
              <NavLink to="/login" className={link}>Sign in</NavLink>
              <NavLink
                to="/register"
                className="px-3 py-2 rounded-full text-sm font-medium bg-brand-600 text-white"
              >
                Register
              </NavLink>
            </div>
          )}
        </nav>
      </div>
    </header>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider portal="customer">
        <Nav />
        <Routes>
          <Route path="/" element={<Navigate to="/browse" replace />} />
          <Route 
            path="/login"
            element={
              <LoginPage/>
            }
          />
          <Route path="/register" element={<RegisterPage/>} />
          <Route path="/browse" element={
            <BrowsePage/>} 
          />
          <Route path="/cart" element={
            <RequireAuth>
              <PageStub title="Cart" task="T09" owner="Kelvin" />
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
      </AuthProvider>
    </BrowserRouter>
  );
}
