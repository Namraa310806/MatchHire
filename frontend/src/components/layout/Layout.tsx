import { Outlet, Link, useLocation } from 'react-router-dom';
import { useAuth } from '@/hooks/auth';
import { Button } from '@/components/ui/button';

export default function Layout() {
  const location = useLocation();
  const { isAuthenticated, user, logout } = useAuth();

  const isActive = (path: string) => location.pathname === path;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4">
          <Link to="/" className="flex items-center space-x-2">
            <span className="text-xl font-bold text-emerald-400">MatchHire</span>
          </Link>
          
          <nav className="flex items-center space-x-6">
            <Link
              to="/"
              className={`text-sm transition-colors hover:text-emerald-400 ${
                isActive('/') ? 'text-emerald-400' : 'text-slate-300'
              }`}
            >
              Home
            </Link>
            
            {isAuthenticated ? (
              <>
                {user?.role === 'candidate' && (
                  <Link
                    to="/candidate/dashboard"
                    className={`text-sm transition-colors hover:text-emerald-400 ${
                      isActive('/candidate/dashboard') ? 'text-emerald-400' : 'text-slate-300'
                    }`}
                  >
                    Dashboard
                  </Link>
                )}
                {user?.role === 'recruiter' && (
                  <Link
                    to="/recruiter/dashboard"
                    className={`text-sm transition-colors hover:text-emerald-400 ${
                      isActive('/recruiter/dashboard') ? 'text-emerald-400' : 'text-slate-300'
                    }`}
                  >
                    Dashboard
                  </Link>
                )}
                {user?.role === 'admin' && (
                  <Link
                    to="/admin/dashboard"
                    className={`text-sm transition-colors hover:text-emerald-400 ${
                      isActive('/admin/dashboard') ? 'text-emerald-400' : 'text-slate-300'
                    }`}
                  >
                    Admin
                  </Link>
                )}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => logout()}
                  className="text-slate-300 hover:text-white"
                >
                  Logout
                </Button>
              </>
            ) : (
              <>
                <Link
                  to="/login"
                  className={`text-sm transition-colors hover:text-emerald-400 ${
                    isActive('/login') ? 'text-emerald-400' : 'text-slate-300'
                  }`}
                >
                  Login
                </Link>
                <Link to="/register">
                  <Button size="sm">Sign Up</Button>
                </Link>
              </>
            )}
          </nav>
        </div>
      </header>
      
      <main className="mx-auto max-w-7xl px-4 py-8">
        <Outlet />
      </main>
      
      <footer className="border-t border-slate-800 bg-slate-900/50 py-8">
        <div className="mx-auto max-w-7xl px-4 text-center text-sm text-slate-400">
          <p>&copy; 2024 MatchHire. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
