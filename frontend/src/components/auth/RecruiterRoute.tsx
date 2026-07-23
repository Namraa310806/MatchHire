import { Navigate } from 'react-router-dom';
import { useAuth } from '@/hooks/auth';

export default function RecruiterRoute({ children }: { children: React.ReactNode }) {
  const { isRecruiter } = useAuth();

  if (!isRecruiter) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}
