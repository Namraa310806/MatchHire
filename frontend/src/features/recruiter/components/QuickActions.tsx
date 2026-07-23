import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Plus, Search, Calendar, FileText, Users } from 'lucide-react';
import { Link } from 'react-router-dom';

export function QuickActions() {
  const actions = [
    {
      title: 'Post New Job',
      description: 'Create a new job posting',
      icon: Plus,
      href: '/recruiter/jobs/new',
      variant: 'default' as const,
    },
    {
      title: 'Search Candidates',
      description: 'Find matching candidates',
      icon: Search,
      href: '/recruiter/candidates/search',
      variant: 'outline' as const,
    },
    {
      title: 'Schedule Interview',
      description: 'Set up candidate interviews',
      icon: Calendar,
      href: '/recruiter/interviews',
      variant: 'outline' as const,
    },
    {
      title: 'View Applications',
      description: 'Review pending applications',
      icon: FileText,
      href: '/recruiter/applications',
      variant: 'outline' as const,
    },
    {
      title: 'Recommendations',
      description: 'AI-suggested candidates',
      icon: Users,
      href: '/recruiter/recommendations',
      variant: 'outline' as const,
    },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Quick Actions</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-1">
          {actions.map((action) => {
            const Icon = action.icon;
            return (
              <Link key={action.title} to={action.href}>
                <Button
                  variant={action.variant}
                  className="w-full justify-start h-auto py-3"
                >
                  <Icon className="mr-2 h-4 w-4" />
                  <div className="text-left">
                    <div className="font-medium">{action.title}</div>
                    <div className="text-xs text-muted-foreground">
                      {action.description}
                    </div>
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
