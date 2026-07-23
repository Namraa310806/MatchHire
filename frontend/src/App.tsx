import { Routes, Route } from 'react-router-dom';
import { Toaster } from '@/components/ui/toaster';
import Layout from '@/components/layout/Layout';
import HomePage from '@/pages/HomePage';
import LoginPage from '@/pages/auth/LoginPage';
import RegisterPage from '@/pages/auth/RegisterPage';
import CandidateDashboard from '@/pages/candidate/CandidateDashboard';
import ProfilePage from '@/pages/candidate/ProfilePage';
import ResumePage from '@/pages/candidate/ResumePage';
import JobsPage from '@/pages/candidate/JobsPage';
import JobDetailsPage from '@/pages/candidate/JobDetailsPage';
import ApplicationsPage from '@/pages/candidate/ApplicationsPage';
import InterviewsPage from '@/pages/candidate/InterviewsPage';
import SavedJobsPage from '@/pages/candidate/SavedJobsPage';
import NotificationsPage from '@/pages/candidate/NotificationsPage';
import AnalyticsPage from '@/pages/candidate/AnalyticsPage';
import SettingsPage from '@/pages/candidate/SettingsPage';
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
              <Route path="candidate/profile" element={<ProfilePage />} />
              <Route path="candidate/resume" element={<ResumePage />} />
              <Route path="candidate/jobs" element={<JobsPage />} />
              <Route path="candidate/jobs/:id" element={<JobDetailsPage />} />
              <Route path="candidate/applications" element={<ApplicationsPage />} />
              <Route path="candidate/interviews" element={<InterviewsPage />} />
              <Route path="candidate/saved" element={<SavedJobsPage />} />
              <Route path="candidate/notifications" element={<NotificationsPage />} />
              <Route path="candidate/analytics" element={<AnalyticsPage />} />
              <Route path="candidate/settings" element={<SettingsPage />} />
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
