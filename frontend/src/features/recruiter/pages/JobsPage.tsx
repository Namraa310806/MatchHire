import { Button } from '@/components/ui/button';
import { Link } from 'react-router-dom';
import { JobList } from '../components/JobList';

export function JobsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Jobs</h1>
          <p className="text-muted-foreground">
            Manage your job postings and applications
          </p>
        </div>
        <Link to="/recruiter/jobs/new">
          <Button>Create Job</Button>
        </Link>
      </div>

      <JobList />
    </div>
  );
}
