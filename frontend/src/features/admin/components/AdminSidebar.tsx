import { NavLink } from 'react-router-dom';
import { cn } from '@/lib/utils';
import {
  LayoutDashboard,
  Users,
  Building2,
  Briefcase,
  FileText,
  Search,
  Brain,
  Activity,
  Flag,
  ScrollText,
  Shield,
  Settings,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useState } from 'react';

const navItems = [
  {
    title: 'Dashboard',
    href: '/admin/dashboard',
    icon: LayoutDashboard,
    description: 'System overview and metrics',
  },
  {
    title: 'Users',
    href: '/admin/users',
    icon: Users,
    description: 'Manage platform users',
  },
  {
    title: 'Companies',
    href: '/admin/companies',
    icon: Building2,
    description: 'Approve and manage companies',
  },
  {
    title: 'Jobs',
    href: '/admin/jobs',
    icon: Briefcase,
    description: 'Moderate job listings',
  },
  {
    title: 'Applications',
    href: '/admin/applications',
    icon: FileText,
    description: 'View all applications',
  },
  {
    title: 'Resumes',
    href: '/admin/resumes',
    icon: FileText,
    description: 'Manage candidate resumes',
  },
  {
    title: 'Search',
    href: '/admin/search',
    icon: Search,
    description: 'Search platform metrics',
  },
  {
    title: 'Recommendations',
    href: '/admin/recommendations',
    icon: Brain,
    description: 'Recommendation engine',
  },
  {
    title: 'Observability',
    href: '/admin/observability',
    icon: Activity,
    description: 'System performance',
  },
  {
    title: 'Feature Flags',
    href: '/admin/feature-flags',
    icon: Flag,
    description: 'Manage feature flags',
  },
  {
    title: 'Audit Logs',
    href: '/admin/audit-logs',
    icon: ScrollText,
    description: 'Administrative actions',
  },
  {
    title: 'Security',
    href: '/admin/security',
    icon: Shield,
    description: 'Security events',
  },
  {
    title: 'Settings',
    href: '/admin/settings',
    icon: Settings,
    description: 'System configuration',
  },
];

interface AdminSidebarProps {
  className?: string;
}

export function AdminSidebar({ className }: AdminSidebarProps) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div
      className={cn(
        'flex flex-col border-r border-slate-800 bg-slate-900/50 transition-all duration-300',
        collapsed ? 'w-16' : 'w-64',
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-slate-800">
        {!collapsed && (
          <div>
            <h2 className="font-bold text-lg">Admin Console</h2>
            <p className="text-xs text-slate-400">MatchHire</p>
          </div>
        )}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setCollapsed(!collapsed)}
          className="ml-auto"
        >
          {collapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </Button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto p-2 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.href}
            to={item.href}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-slate-800 text-white'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/50',
                collapsed && 'justify-center'
              )
            }
            title={collapsed ? item.title : undefined}
          >
            <item.icon className="h-4 w-4 flex-shrink-0" />
            {!collapsed && (
              <div className="flex-1">
                <span>{item.title}</span>
              </div>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-slate-800">
        {!collapsed && (
          <div className="text-xs text-slate-500">
            <p>MatchHire Admin Console</p>
            <p className="mt-1">v1.0.0</p>
          </div>
        )}
      </div>
    </div>
  );
}
