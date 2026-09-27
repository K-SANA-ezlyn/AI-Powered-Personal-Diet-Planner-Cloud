import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import DisclaimerBanner from "./components/DisclaimerBanner";
import Navbar from "./components/Navbar";
import ProtectedRoute from "./components/ProtectedRoute";
import { AuthProvider, useAuth } from "./context/AuthContext";
import CloudFilesPage from "./pages/CloudFilesPage";
import DashboardPage from "./pages/DashboardPage";
import GeneratePlanPage from "./pages/GeneratePlanPage";
import LandingPage from "./pages/LandingPage";
import LoginPage from "./pages/LoginPage";
import PlanResultPage from "./pages/PlanResultPage";
import ProfilePage from "./pages/ProfilePage";
import RegisterPage from "./pages/RegisterPage";
import SavedPlansPage from "./pages/SavedPlansPage";

function Shell() {
  const { user } = useAuth();

  return (
    <BrowserRouter>
      {user && <Navbar />}
      <DisclaimerBanner />
      <Routes>
        {/* public */}
        <Route path="/" element={user ? <Navigate to="/dashboard" replace /> : <LandingPage />} />
        <Route path="/login" element={user ? <Navigate to="/dashboard" replace /> : <LoginPage />} />
        <Route path="/register" element={user ? <Navigate to="/dashboard" replace /> : <RegisterPage />} />

        {/* protected */}
        <Route path="/dashboard" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
        <Route path="/profile" element={<ProtectedRoute><ProfilePage /></ProtectedRoute>} />
        <Route path="/generate" element={<ProtectedRoute><GeneratePlanPage /></ProtectedRoute>} />
        <Route path="/plans" element={<ProtectedRoute><SavedPlansPage /></ProtectedRoute>} />
        <Route path="/plans/:id" element={<ProtectedRoute><PlanResultPage /></ProtectedRoute>} />
        <Route path="/files" element={<ProtectedRoute><CloudFilesPage /></ProtectedRoute>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Shell />
    </AuthProvider>
  );
}
