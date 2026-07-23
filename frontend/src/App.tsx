import { Routes, Route } from 'react-router-dom';
import { Toaster } from '@/components/ui/toaster';
import Layout from '@/components/layout/Layout';
import HomePage from '@/pages/HomePage';
import LoginPage from '@/pages/auth/LoginPage';
import RegisterPage from '@/pages/auth/RegisterPage';
import CandidateDashboard from '@/pages/candidate/CandidateDashboard';
import RecruiterDashboard from '@/pages/recruiter/RecruiterDashboard';
import AdminDashboard from '@/pages/admin/AdminDashboard';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import CandidateRoute from '@/components/auth/CandidateRoute';
import RecruiterRoute from '@/components/auth/RecruiterRoute';
import AdminRoute from '@/components/auth/AdminRoute';

function App() {
  return (
    <>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="login" element={<LoginPage />} />
          <Route path="register" element={<RegisterPage />} />
          
          {/* Protected Routes */}
          <Route element={<ProtectedRoute />}>
            <Route element={<CandidateRoute />}>
              <Route path="candidate/dashboard" element={<CandidateDashboard />} />
            </Route>
            <Route element={<RecruiterRoute />}>
              <Route path="recruiter/dashboard" element={<RecruiterDashboard />} />
            </Route>
            <Route element={<AdminRoute />}>
              <Route path="admin/dashboard" element={<AdminDashboard />} />
            </Route>
          </Route>
        </Route>
      </Routes>
      <Toaster />
    </>
  );
}

export default App;
