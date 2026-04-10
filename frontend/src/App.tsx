import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import Models from "./pages/Models";
import Sessions from "./pages/Sessions";
import Setup from "./pages/Setup";

export default function App() {
  return (
    <BrowserRouter basename="/app">
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Navigate to="/setup" replace />} />
          <Route path="/setup" element={<Setup />} />
          <Route path="/models" element={<Models />} />
          <Route path="/sessions" element={<Sessions />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
