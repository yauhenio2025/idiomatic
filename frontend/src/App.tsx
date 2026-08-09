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
import Grammar from "./pages/Grammar";
import GrammarUnit from "./pages/GrammarUnit";
import CastReview from "./pages/CastReview";
import RescueLab from "./pages/RescueLab";
import RescueItem from "./pages/RescueItem";
import RescueFormats from "./pages/RescueFormats";
import Delivery from "./pages/Delivery";
import DJ from "./pages/DJ";
import Triage from "./pages/Triage";
import Legacy from "./pages/Legacy";

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
        <Route path="/grammar" element={<Grammar />} />
        <Route path="/grammar/unit/:key" element={<GrammarUnit />} />
        <Route path="/cast" element={<CastReview />} />
        <Route path="/rescue" element={<RescueLab />} />
        <Route path="/rescue/item/:id" element={<RescueItem />} />
        <Route path="/rescue/formats" element={<RescueFormats />} />
        <Route path="/dj" element={<DJ />} />
        <Route path="/triage" element={<Triage />} />
        <Route path="/delivery" element={<Delivery />} />
        <Route path="/legacy" element={<Legacy />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
