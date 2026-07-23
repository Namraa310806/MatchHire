import { Navigate } from 'react-router-dom';
import { useAuth } from '@/hooks/auth';

export default function CandidateRoute({ children }: { children: React.ReactNode }) {
  const { isCandidate } = useAuth();

  if (!isCandidate) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}
