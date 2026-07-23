import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Spinner } from '@/components/ui/spinner';
import { EmptyState } from '@/components/ui/empty-state';
import { Briefcase, MapPin, DollarSign, Clock, Heart, Share2, Trash2 } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { Link } from 'react-router-dom';
import { useState } from 'react';

// Mock saved jobs data - in production this would come from backend API
const mockSavedJobs = [
  {
    id: '1',
    title: 'Senior Software Engineer',
    company: 'Tech Corp',
    location: 'San Francisco, CA',
    salary_min: 150000,
    salary_max: 200000,
    employment_type: 'full-time',
    experience_level: 'senior',
    remote: true,
    skills: ['React', 'TypeScript', 'Node.js'],
    posted_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: '2',
    title: 'Full Stack Developer',
    company: 'Data Systems Inc',
    location: 'New York, NY',
    salary_min: 120000,
    salary_max: 160000,
    employment_type: 'full-time',
    experience_level: 'mid',
    remote: false,
    skills: ['Python', 'Django', 'React'],
    posted_at: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
  },
];

export default function SavedJobsPage() {
  const [savedJobs, setSavedJobs] = useState(mockSavedJobs);
  const [isLoading, setIsLoading] = useState(false);

  const handleRemove = (id: string) => {
    if (confirm('Are you sure you want to remove this job from saved jobs?')) {
      setSavedJobs(savedJobs.filter(job => job.id !== id));
    }
  };

  const handleShare = (job: any) => {
    // In production, this would open a share dialog or copy link
    const url = `${window.location.origin}/candidate/jobs/${job.id}`;
    navigator.clipboard.writeText(url);
    alert('Job link copied to clipboard!');
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Saved Jobs</h1>
        <p className="text-muted-foreground mt-2">Jobs you've bookmarked for later</p>
      </div>

      {savedJobs.length > 0 ? (
        <div className="space-y-4">
          {savedJobs.map((job) => (
            <SavedJobCard
              key={job.id}
              job={job}
              onRemove={() => handleRemove(job.id)}
              onShare={() => handleShare(job)}
            />
          ))}
        </div>
      ) : (
        <EmptyState
          title="No saved jobs"
          description="Save jobs you're interested in to view them later"
          action={
            <Link to="/candidate/jobs">
              <Button>Browse Jobs</Button>
            </Link>
          }
        />
      )}
    </div>
  );
}

interface SavedJobCardProps {
  job: any;
  onRemove: () => void;
  onShare: () => void;
}

function SavedJobCard({ job, onRemove, onShare }: SavedJobCardProps) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-4 flex-1">
            <div className="p-3 bg-primary/10 rounded-lg">
              <Briefcase className="h-6 w-6 text-primary" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-lg">{job.title}</h3>
              <p className="text-muted-foreground">{job.company}</p>
              <div className="flex flex-wrap gap-3 mt-2 text-sm text-muted-foreground">
                <div className="flex items-center gap-1">
                  <MapPin className="h-4 w-4" />
                  {job.location}
                </div>
                {job.salary_min && job.salary_max && (
                  <div className="flex items-center gap-1">
                    <DollarSign className="h-4 w-4" />
                    ${job.salary_min.toLocaleString()} - ${job.salary_max.toLocaleString()}
                  </div>
                )}
                <div className="flex items-center gap-1">
                  <Clock className="h-4 w-4" />
                  {formatDistanceToNow(new Date(job.posted_at), { addSuffix: true })}
                </div>
              </div>
              <div className="flex flex-wrap gap-2 mt-3">
                <Badge variant="secondary">{job.employment_type}</Badge>
                <Badge variant="secondary">{job.experience_level}</Badge>
                {job.remote && <Badge variant="outline">Remote</Badge>}
                {job.skills?.slice(0, 3).map((skill: string) => (
                  <Badge key={skill} variant="outline">{skill}</Badge>
                ))}
              </div>
            </div>
          </div>
          <div className="flex gap-2">
            <Link to={`/candidate/jobs/${job.id}`}>
              <Button variant="outline">View Details</Button>
            </Link>
            <Button variant="outline" size="icon" onClick={onShare}>
              <Share2 className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="icon" onClick={onRemove}>
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
