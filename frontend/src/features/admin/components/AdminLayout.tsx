import { Outlet } from 'react-router-dom';
import { AdminSidebar } from './AdminSidebar';

export function AdminLayout() {
  return (
    <div className="flex h-screen bg-slate-950">
      <AdminSidebar />
      <main className="flex-1 overflow-y-auto">
        <div className="container mx-auto p-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
