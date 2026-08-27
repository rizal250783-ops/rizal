import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "sonner";
import { AuthProvider, useAuth } from "./context/AuthContext";
import Layout from "./components/Layout";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import NotesList from "./pages/NotesList";
import NoteForm from "./pages/NoteForm";
import NoteDetail from "./pages/NoteDetail";
import ApprovedNotes from "./pages/ApprovedNotes";
import Notifications from "./pages/Notifications";
import Monitoring from "./pages/Monitoring";
import UserManagement from "./pages/UserManagement";
import MasterData from "./pages/MasterData";
import AuditTrail from "./pages/AuditTrail";
import RiskAssessment from "./pages/RiskAssessment";
import ChangePassword from "./pages/ChangePassword";
import { Loader2 } from "lucide-react";

function Protected({ children, roles, nip }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="min-h-screen flex items-center justify-center"><Loader2 className="animate-spin text-[#00A0A0]" size={32} /></div>;
  if (!user) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(user.role)) return <Navigate to="/dashboard" replace />;
  if (nip && user.nip !== nip) return <Navigate to="/dashboard" replace />;
  return children;
}

function AppRoutes() {
  const { user, loading } = useAuth();
  return (
    <Routes>
      <Route path="/login" element={loading ? null : user ? <Navigate to="/dashboard" replace /> : <Login />} />
      <Route element={<Protected><Layout /></Protected>}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/notes" element={<NotesList />} />
        <Route path="/notes/new" element={<Protected roles={["RCO"]}><NoteForm /></Protected>} />
        <Route path="/notes/:id/edit" element={<Protected roles={["RCO"]}><NoteForm /></Protected>} />
        <Route path="/notes/:id" element={<NoteDetail />} />
        <Route path="/approved" element={<ApprovedNotes />} />
        <Route path="/monitoring" element={<Protected roles={["RCRM", "RCG"]}><Monitoring /></Protected>} />
        <Route path="/risk-assessment" element={<Protected roles={["RCG"]}><RiskAssessment /></Protected>} />
        <Route path="/users" element={<Protected roles={["RCG"]} nip="2183008345"><UserManagement /></Protected>} />
        <Route path="/master" element={<Protected roles={["RCG"]} nip="2183008345"><MasterData /></Protected>} />
        <Route path="/audit" element={<Protected roles={["RCG"]} nip="2183008345"><AuditTrail /></Protected>} />
        <Route path="/notifications" element={<Notifications />} />
        <Route path="/change-password" element={<ChangePassword />} />
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <div className="App">
      <Toaster position="top-right" richColors />
      <BrowserRouter>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </BrowserRouter>
    </div>
  );
}
