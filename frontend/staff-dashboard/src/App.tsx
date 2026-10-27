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
  LoginPage,
  NavPill,
  PageStub,
} from "@ofs/shared/components";

const STAFF_ROLES: UserRole[] = ["employee", "manager"];

function Nav() {
  const { user } = useAuth();

  return (
    <AppHeader brand={<NavLink to="/queue">OFS Staff</NavLink>}>
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
                title="OFS Staff"
                subtitle="Sign in with an Employee or Manager account."
                defaultRedirect="/queue"
              />
            }
          />
          <Route
            path="/queue"
            element={
              <RequireAuth roles={STAFF_ROLES}>
                <PageStub
                  title="Preparation Queue"
                  task="T13"
                  owner="Ethan"
                />
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
                <PageStub
                  title="Inventory"
                  task="T05"
                  owner="Shresthkumar"
                />
              </RequireAuth>
            }
          />
          <Route
            path="/reports"
            element={
              <RequireAuth roles={["manager"]}>
                <PageStub
                  title="Reports (Manager only)"
                  task="T19"
                  owner="Andrian"
                />
              </RequireAuth>
            }
          />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
