import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import { AuthProvider, useAuth } from "@/context/AuthContext";
import Layout from "@/components/Layout";
import Login from "@/pages/Login";
import Dashboard from "@/pages/Dashboard";
import Cases from "@/pages/Cases";
import CaseForm from "@/pages/CaseForm";
import CaseDetail from "@/pages/CaseDetail";
import Approvals from "@/pages/Approvals";
import TimelinePage from "@/pages/TimelinePage";
import DocumentsPage from "@/pages/DocumentsPage";
import Reports from "@/pages/Reports";
import MasterData from "@/pages/MasterData";
import Users from "@/pages/Users";
import Database from "@/pages/Database";
import "@/App.css";

function Protected({ children, deptOnly }) {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#f8fafc]">
        <p className="text-sm text-slate-500">Memuat...</p>
      </div>
    );
  }
  if (!user) return <Navigate to="/login" replace />;
  if (deptOnly && user.role !== "dept_head") return <Navigate to="/" replace />;
  return <Layout>{children}</Layout>;
}

function LoginRoute() {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (user) return <Navigate to="/" replace />;
  return <Login />;
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginRoute />} />
          <Route path="/" element={<Protected><Dashboard /></Protected>} />
          <Route path="/perkara" element={<Protected><Cases /></Protected>} />
          <Route path="/perkara/baru" element={<Protected><CaseForm /></Protected>} />
          <Route path="/perkara/:id" element={<Protected><CaseDetail /></Protected>} />
          <Route path="/perkara/:id/edit" element={<Protected><CaseForm /></Protected>} />
          <Route path="/approval" element={<Protected><Approvals /></Protected>} />
          <Route path="/timeline" element={<Protected><TimelinePage /></Protected>} />
          <Route path="/dokumen" element={<Protected><DocumentsPage /></Protected>} />
          <Route path="/laporan" element={<Protected><Reports /></Protected>} />
          <Route path="/master-data" element={<Protected><MasterData /></Protected>} />
          <Route path="/users" element={<Protected deptOnly><Users /></Protected>} />
          <Route path="/database" element={<Protected deptOnly><Database /></Protected>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" richColors />
    </AuthProvider>
  );
}

export default App;
