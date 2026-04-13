import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuthStore } from "../store/useAuthStore";
import "./Layout.css";

const NAV_ITEMS = [
  { to: "/model", label: "LLModels" },
  { to: "/persona", label: "Persona" },
  { to: "/setup", label: "Setup" },
  { to: "/memory", label: "Memory" },
  { to: "/conversation", label: "Conversations" },
  { to: "/session", label: "Sessions" },
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
        <button className="topbar-logout btn-ghost" onClick={handleLogout}>
          Sign out
        </button>
      </header>
      <div className="layout-body">
        <nav className="sidebar">
          <ul>
            {NAV_ITEMS.map(({ to, label }) => (
              <li key={to}>
                <NavLink
                  to={to}
                  className={({ isActive }) => (isActive ? "active" : "")}
                >
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
