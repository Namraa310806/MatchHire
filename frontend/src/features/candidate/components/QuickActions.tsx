import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Search, FileText, User, Settings } from 'lucide-react';
import { Link } from 'react-router-dom';

export function QuickActions() {
  const actions = [
    {
      title: 'Search Jobs',
      description: 'Find your next opportunity',
      icon: Search,
      href: '/candidate/jobs',
      color: 'bg-blue-500',
    },
    {
      title: 'My Applications',
      description: 'Track your progress',
      icon: FileText,
      href: '/candidate/applications',
      color: 'bg-green-500',
    },
    {
      title: 'Update Profile',
      description: 'Complete your profile',
      icon: User,
      href: '/candidate/profile',
      color: 'bg-purple-500',
    },
    {
      title: 'Settings',
      description: 'Manage preferences',
      icon: Settings,
      href: '/candidate/settings',
      color: 'bg-gray-500',
    },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Quick Actions</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid gap-3 sm:grid-cols-2">
          {actions.map((action) => {
            const Icon = action.icon;
            return (
              <Link key={action.href} to={action.href}>
                <Button
                  variant="outline"
                  className="w-full h-auto flex-col gap-2 py-4 hover:bg-accent"
                >
                  <div className={`p-2 rounded-lg ${action.color} text-white`}>
                    <Icon className="h-5 w-5" />
                  </div>
                  <div className="text-left">
                    <p className="font-semibold text-sm">{action.title}</p>
                    <p className="text-xs text-muted-foreground">{action.description}</p>
                  </div>
                </Button>
              </Link>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
