import { BrowserRouter, Routes, Route, Navigate, NavLink, type NavLinkRenderProps } from "react-router-dom";
import PageStub from "./pages/PageStub";

function Nav() {
  const link = ({ isActive }: NavLinkRenderProps) =>
    `px-3 py-2 rounded-full text-sm font-medium ${isActive ? "bg-brand-50 text-brand-700" : "text-brand-900/60"}`;
  return (
    <header className="sticky top-0 bg-white/90 backdrop-blur border-b border-brand-100">
      <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
        <span className="font-display font-bold text-brand-700 text-lg">OFS Staff</span>
        <nav className="flex gap-1">
          <NavLink to="/queue" className={link}>Prep Queue</NavLink>
          <NavLink to="/dispatch" className={link}>Dispatch</NavLink>
          <NavLink to="/inventory" className={link}>Inventory</NavLink>
          <NavLink to="/reports" className={link}>Reports</NavLink>
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
        <Route path="/" element={<Navigate to="/queue" replace />} />
        <Route path="/login" element={<PageStub title="Staff Login" task="T04" owner="Shresthkumar" />} />
        <Route path="/queue" element={<PageStub title="Preparation Queue" task="T13" owner="Ethan" />} />
        <Route path="/dispatch" element={<PageStub title="Dispatch" task="T13 / T14 / T15" owner="Ethan" />} />
        <Route path="/inventory" element={<PageStub title="Inventory" task="T05" owner="Shresthkumar" />} />
        <Route path="/reports" element={<PageStub title="Reports (Manager only)" task="T19" owner="Andrian" />} />
      </Routes>
    </BrowserRouter>
  );
}
