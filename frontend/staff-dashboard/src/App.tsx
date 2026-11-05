import { BrowserRouter, Navigate, NavLink, Route, Routes } from "react-router-dom";
import {
  AuthProvider,
  RequireAuth,
  useAuth,
  type UserRole,
} from "@ofs/shared/auth";
import {
  AccountMenu,
  AppHeader,
  BrandMark,
  LoginPage,
  NavPill,
  PageStub,
} from "@ofs/shared/components";

import InventoryPage from "./pages/InventoryPage";
import OrderQueuePage from "./pages/OrderQueuePage";
import ReportsPage from "./pages/ReportsPage";

const STAFF_ROLES: UserRole[] = ["employee", "manager"];

function Nav() {
  const { user } = useAuth();

  return (
    <AppHeader brand={<NavLink to="/queue"><BrandMark suffix="Staff" /></NavLink>}>
      {user && (
        <>
          <NavPill to="/queue">Prep Queue</NavPill>
          <NavPill to="/dispatch">Dispatch</NavPill>
          <NavPill to="/inventory">Inventory</NavPill>
          {user.role === "manager" && (
            <NavPill to="/reports">Reports</NavPill>
          )}
          <AccountMenu />
        </>
      )}
    </AppHeader>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider portal="staff">
        <Nav />
        <Routes>
          <Route path="/" element={<Navigate to="/queue" replace />} />
          <Route
            path="/login"
            element={
              <LoginPage
                title="Basil Staff"
                subtitle="Sign in with an Employee or Manager account."
                defaultRedirect="/queue"
              />
            }
          />
          <Route
            path="/queue"
            element={
              <RequireAuth roles={STAFF_ROLES}>
                <OrderQueuePage />
              </RequireAuth>
            }
          />
          <Route
            path="/dispatch"
            element={
              <RequireAuth roles={STAFF_ROLES}>
                <PageStub
                  title="Dispatch"
                  task="T13 / T14 / T15"
                  owner="Ethan"
                />
              </RequireAuth>
            }
          />
          <Route
            path="/inventory"
            element={
              <RequireAuth roles={STAFF_ROLES}>
                <InventoryPage />
              </RequireAuth>
            }
          />
          <Route
            path="/reports"
            element={
              <RequireAuth roles={["manager"]}>
                <ReportsPage />
              </RequireAuth>
            }
          />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
