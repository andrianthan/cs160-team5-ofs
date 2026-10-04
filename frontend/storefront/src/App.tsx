import { BrowserRouter, Routes, Route, Navigate, NavLink, type NavLinkRenderProps } from "react-router-dom";
import PageStub from "./pages/PageStub";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage"

// Route table from docs/part2 LLD 5 (Frontend Component Breakdown), owners from
// docs/part2/backlog.md. Replace each PageStub with the real page as it's built.
function Nav() {
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
        </nav>
      </div>
    </header>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Nav />
      <Routes>
        <Route path="/" element={<Navigate to="/browse" replace />} />
        <Route path="/login" element={<LoginPage/>} />
        <Route path="/register" element={<RegisterPage/>} />
        <Route path="/browse" element={<PageStub title="Browse Products" task="T07" owner="Kelvin" />} />
        <Route path="/cart" element={<PageStub title="Cart" task="T09" owner="Kelvin" />} />
        <Route path="/checkout" element={<PageStub title="Checkout" task="T08 / T10 / T11" owner="Andrian" />} />
        <Route path="/track" element={<PageStub title="Track Orders" task="T16" owner="Jorge" />} />
      </Routes>
    </BrowserRouter>
  );
}
