import { Navigate } from 'react-router-dom';
import { useAuth } from '@/hooks/auth';

export default function AdminRoute({ children }: { children: React.ReactNode }) {
  const { isAdmin } = useAuth();

  if (!isAdmin) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}
