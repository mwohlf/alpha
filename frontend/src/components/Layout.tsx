import { NavLink, Outlet } from "react-router-dom";
import "./Layout.css";

const NAV_ITEMS = [
  { to: "/setup", label: "Setup" },
  { to: "/models", label: "Models" },
  { to: "/sessions", label: "Sessions" },
];

export default function Layout() {
  return (
    <div className="layout">
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
  );
}
