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
import SystemDashboard from '@/features/admin/pages/SystemDashboard';
import UserManagement from '@/features/admin/pages/UserManagement';
import CompanyManagement from '@/features/admin/pages/CompanyManagement';
import JobAdministration from '@/features/admin/pages/JobAdministration';
import ApplicationAdministration from '@/features/admin/pages/ApplicationAdministration';
import ResumeAdministration from '@/features/admin/pages/ResumeAdministration';
import SearchMonitoring from '@/features/admin/pages/SearchMonitoring';
import RecommendationMonitoring from '@/features/admin/pages/RecommendationMonitoring';
import Observability from '@/features/admin/pages/Observability';
import FeatureFlags from '@/features/admin/pages/FeatureFlags';
import AuditLogs from '@/features/admin/pages/AuditLogs';
import SecurityCenter from '@/features/admin/pages/SecurityCenter';
import SystemConfiguration from '@/features/admin/pages/SystemConfiguration';
import { AdminLayout } from '@/features/admin/components/AdminLayout';
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
              <Route element={<AdminLayout />}>
                <Route path="admin/dashboard" element={<SystemDashboard />} />
                <Route path="admin/users" element={<UserManagement />} />
                <Route path="admin/companies" element={<CompanyManagement />} />
                <Route path="admin/jobs" element={<JobAdministration />} />
                <Route path="admin/applications" element={<ApplicationAdministration />} />
                <Route path="admin/resumes" element={<ResumeAdministration />} />
                <Route path="admin/search" element={<SearchMonitoring />} />
                <Route path="admin/recommendations" element={<RecommendationMonitoring />} />
                <Route path="admin/observability" element={<Observability />} />
                <Route path="admin/feature-flags" element={<FeatureFlags />} />
                <Route path="admin/audit-logs" element={<AuditLogs />} />
                <Route path="admin/security" element={<SecurityCenter />} />
                <Route path="admin/settings" element={<SystemConfiguration />} />
              </Route>
            </Route>
          </Route>
        </Route>
      </Routes>
      <Toaster />
    </>
  );
}

export default App;
