import { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuthStore } from "../store/useAuthStore";
import "./Layout.css";

const NAV_ITEMS = [
  { to: "/model", label: "LLModels" },
  { to: "/persona", label: "Persona" },
  { to: "/setup", label: "Setup" },
  { to: "/memory", label: "Memory" },
  { to: "/conversation", label: "Conversations" },
  { to: "/chat", label: "Chat" },
];

export default function Layout() {
  const logout = useAuthStore((s) => s.logout);
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <div className="layout">
      <header className="topbar">
        <div className="topbar-left">
          <button
            className="topbar-hamburger"
            onClick={() => setSidebarOpen((o) => !o)}
            aria-label="Toggle navigation"
          >
            <span /><span /><span />
          </button>
          <span className="topbar-title">Alpha</span>
        </div>
        <button className="topbar-logout btn-ghost" onClick={handleLogout}>
          Sign out
        </button>
      </header>
      {sidebarOpen && (
        <div className="sidebar-backdrop" onClick={() => setSidebarOpen(false)} />
      )}
      <div className="layout-body">
        <nav className={`sidebar${sidebarOpen ? " sidebar--open" : ""}`}>
          <ul>
            {NAV_ITEMS.map(({ to, label }) => (
              <li key={to}>
                <NavLink
                  to={to}
                  className={({ isActive }) => (isActive ? "active" : "")}
                  onClick={() => setSidebarOpen(false)}
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
