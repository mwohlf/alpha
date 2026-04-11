import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuthStore } from "../store/useAuthStore";
import "./Layout.css";

const NAV_ITEMS = [
  { to: "/setup", label: "Setup" },
  { to: "/models", label: "Models" },
  { to: "/sessions", label: "Sessions" },
  { to: "/chat", label: "Chat" },
];

export default function Layout() {
  const logout = useAuthStore((s) => s.logout);
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <div className="layout">
      <header className="topbar">
        <span className="topbar-title">Alpha</span>
        <button className="topbar-logout" onClick={handleLogout}>Sign out</button>
      </header>
      <div className="layout-body">
        <nav className="sidebar">
          <ul>
            {NAV_ITEMS.map(({ to, label }) => (
              <li key={to}>
                <NavLink to={to} className={({ isActive }) => isActive ? "active" : ""}>
                  {label}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
        <main className="content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
