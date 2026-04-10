import { ReactElement } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import Login from "./pages/Login";
import Models from "./pages/Models";
import Sessions from "./pages/Sessions";
import Setup from "./pages/Setup";
import { useAuthStore } from "./store/useAuthStore";

function RequireAuth({ children }: { children: ReactElement }) {
  const token = useAuthStore((s) => s.token);
  return token ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <BrowserRouter basename="/app">
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          element={
            <RequireAuth>
              <Layout />
            </RequireAuth>
          }
        >
          <Route index element={<Navigate to="/setup" replace />} />
          <Route path="/setup" element={<Setup />} />
          <Route path="/models" element={<Models />} />
          <Route path="/sessions" element={<Sessions />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
