import { useEffect } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { Toaster } from "sonner";

import { AppLayout } from "@/components/layout/AppLayout";
import { initTheme } from "@/lib/themes";
import AssistantPage from "@/pages/Assistant";
import LibraryPage from "@/pages/Library";
import LoginPage from "@/pages/Login";
import MindMapPage from "@/pages/MindMap";
import NoteDetailPage from "@/pages/NoteDetail";
import SettingsPage from "@/pages/Settings";
import { useAuth } from "@/stores/auth";

function RequireAuth() {
  const token = useAuth((s) => s.token);
  if (!token) return <Navigate to="/login" replace />;
  return <AppLayout />;
}

export default function App() {
  useEffect(() => {
    initTheme();
  }, []);

  return (
    <>
      <Toaster position="top-center" richColors />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<RequireAuth />}>
          <Route path="/" element={<AssistantPage />} />
          <Route path="/library" element={<LibraryPage />} />
          <Route path="/notes/:id" element={<NoteDetailPage />} />
          <Route path="/mindmap" element={<MindMapPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          {/* 舊路由導向 */}
          <Route path="/chat" element={<Navigate to="/" replace />} />
          <Route path="/knowledge" element={<Navigate to="/library" replace />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}
