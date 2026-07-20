import { useCallback, useEffect, useState } from "react";
import { Navigate, Route, Routes, useNavigate } from "react-router-dom";
import { api, clearToken, getToken, setUnauthorizedHandler } from "./api";
import Layout from "./components/Layout";
import Login from "./pages/Login";
import Overview from "./pages/Overview";
import Videos from "./pages/Videos";
import VideoDetail from "./pages/VideoDetail";
import Expressions from "./pages/Expressions";
import ExpressionDetail from "./pages/ExpressionDetail";
import Channels from "./pages/Channels";
import Delivery from "./pages/Delivery";

export default function App() {
  const [authed, setAuthed] = useState<boolean | null>(getToken() ? null : false);
  const navigate = useNavigate();

  const logout = useCallback(() => {
    clearToken();
    setAuthed(false);
    navigate("/login", { replace: true });
  }, [navigate]);

  useEffect(() => {
    setUnauthorizedHandler(() => {
      clearToken();
      setAuthed(false);
    });
  }, []);

  useEffect(() => {
    if (getToken()) {
      api("/auth/check")
        .then(() => setAuthed(true))
        .catch(() => setAuthed(false));
    }
  }, []);

  if (authed === null) {
    return (
      <div className="flex h-screen items-center justify-center text-muted">
        checking session…
      </div>
    );
  }

  if (!authed) {
    return (
      <Routes>
        <Route path="*" element={<Login onAuthed={() => setAuthed(true)} />} />
      </Routes>
    );
  }

  return (
    <Routes>
      <Route element={<Layout onLogout={logout} />}>
        <Route path="/" element={<Overview />} />
        <Route path="/videos" element={<Videos />} />
        <Route path="/videos/:id" element={<VideoDetail />} />
        <Route path="/expressions" element={<Expressions />} />
        <Route path="/expressions/:id" element={<ExpressionDetail />} />
        <Route path="/channels" element={<Channels />} />
        <Route path="/delivery" element={<Delivery />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
