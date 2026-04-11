import {
  BrowserRouter,
  Navigate,
  Outlet,
  Route,
  Routes,
} from "react-router-dom";
import Chat from "./pages/Chat";
import Login from "./pages/Login";
import Models from "./pages/Models";
import Sessions from "./pages/Sessions";
import Setup from "./pages/Setup";
import { useAuthStore } from "./store/useAuthStore";
import Layout from "./components/Layout";

function RequireAuth() {
  const isAuthenticated = useAuthStore((s) => !!s.token);
  // Get the hydration status from Zustand
  const hasHydrated = useAuthStore.persist.hasHydrated();
  // If we haven't checked localStorage yet, show nothing (or a spinner)
  if (!hasHydrated) {
    return <div>Loading...</div>; // Or return null
  }
  return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <BrowserRouter basename="/app">
      <Routes>
        {/* Public Route */}
        <Route path="/login" element={<Login />} />

        {/* Protected Routes with Layout */}
        <Route element={<RequireAuth />}>
          <Route element={<Layout />}>
            <Route index element={<Navigate to="/setup" replace />} />
            <Route path="/setup" element={<Setup />} />
            <Route path="/models" element={<Models />} />
            <Route path="/sessions" element={<Sessions />} />
            <Route path="/chat" element={<Chat />} />
          </Route>
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
