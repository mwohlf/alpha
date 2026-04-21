import {
  BrowserRouter,
  Navigate,
  Outlet,
  Route,
  Routes,
} from "react-router-dom";
import Chat from "./pages/Chat";
import Login from "./pages/Login";
import Model from "./pages/Model";
import Conversation from "./pages/Conversation";
import Persona from "./pages/Persona";
import Memory from "./pages/Memory";
import Setup from "./pages/Setup";
import { useAuthStore } from "./store/useAuthStore";
import Layout from "./components/Layout";

function RequireAuth() {
  const token = useAuthStore((s) => s.token);
  const isAuthenticated = !!token;
  // Get the hydration status from Zustand
  const hasHydrated = useAuthStore.persist.hasHydrated();
  console.log("[RequireAuth]", { hasHydrated, isAuthenticated, token });
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
            <Route path="/model" element={<Model />} />
            <Route path="/persona" element={<Persona />} />
            <Route path="/memory" element={<Memory />} />
            <Route path="/chat" element={<Chat />} />
            <Route path="/conversation" element={<Conversation />} />
          </Route>
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
