import { useState } from 'react';
import { useJobs, useSearchJobs } from '@/features/jobs/hooks/useJobs';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Pagination, PaginationContent, PaginationItem, PaginationLink, PaginationNext, PaginationPrevious } from '@/components/ui/pagination';
import { Spinner } from '@/components/ui/spinner';
import { EmptyState } from '@/components/ui/empty-state';
import { Search, MapPin, DollarSign, Briefcase, Clock, Filter } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { Link } from 'react-router-dom';

export default function JobsPage() {
  const [searchParams, setSearchParams] = useState({
    query: '',
    location: '',
    employment_type: '',
    experience_level: '',
    remote: false,
    salary_min: undefined as number | undefined,
    salary_max: undefined as number | undefined,
    skills: [] as string[],
    page: 1,
    page_size: 20,
    sort_by: 'posted_at',
    sort_order: 'desc' as 'asc' | 'desc',
  });

  const [showFilters, setShowFilters] = useState(false);
  const { data: jobsData, isLoading } = useSearchJobs(searchParams);

  const handleSearch = (query: string) => {
    setSearchParams({ ...searchParams, query, page: 1 });
  };

  const handleFilterChange = (key: string, value: any) => {
    setSearchParams({ ...searchParams, [key]: value, page: 1 });
  };

  const handlePageChange = (page: number) => {
    setSearchParams({ ...searchParams, page });
  };

  const employmentTypes = [
    { value: 'full-time', label: 'Full-time' },
    { value: 'part-time', label: 'Part-time' },
    { value: 'contract', label: 'Contract' },
    { value: 'internship', label: 'Internship' },
  ];

  const experienceLevels = [
    { value: 'entry', label: 'Entry Level' },
    { value: 'mid', label: 'Mid Level' },
    { value: 'senior', label: 'Senior Level' },
    { value: 'executive', label: 'Executive' },
  ];

  const commonSkills = [
    'JavaScript', 'Python', 'React', 'Node.js', 'TypeScript',
    'Java', 'Go', 'AWS', 'Docker', 'Kubernetes', 'SQL', 'Machine Learning'
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Job Search</h1>
        <p className="text-muted-foreground mt-2">Find your next opportunity</p>
      </div>

      {/* Search Bar */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search jobs by title, company, or keywords..."
                className="pl-10"
                value={searchParams.query}
                onChange={(e) => handleSearch(e.target.value)}
              />
            </div>
            <Button
              variant="outline"
              onClick={() => setShowFilters(!showFilters)}
            >
              <Filter className="h-4 w-4 mr-2" />
              Filters
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Filters */}
      {showFilters && (
        <Card>
          <CardHeader>
            <CardTitle>Filters</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              <div className="space-y-2">
                <Label>Location</Label>
                <Input
                  placeholder="City, state, or remote"
                  value={searchParams.location}
                  onChange={(e) => handleFilterChange('location', e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label>Employment Type</Label>
                <Select
                  value={searchParams.employment_type}
                  onValueChange={(value) => handleFilterChange('employment_type', value)}
                >
                  <SelectTrigger>

                    <SelectValue placeholder="Select type" />
                  </SelectTrigger>
                  <SelectContent>
                    {employmentTypes.map((type) => (
                      <SelectItem key={type.value} value={type.value}>
                        {type.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Experience Level</Label>
                <Select
                  value={searchParams.experience_level}
                  onValueChange={(value) => handleFilterChange('experience_level', value)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select level" />
                  </SelectTrigger>
                  <SelectContent>
                    {experienceLevels.map((level) => (
                      <SelectItem key={level.value} value={level.value}>
                        {level.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Salary Range (Min)</Label>
                <Input
                  type="number"
                  placeholder="Min salary"
                  value={searchParams.salary_min || ''}
                  onChange={(e) => handleFilterChange('salary_min', e.target.value ? parseInt(e.target.value) : undefined)}
                />
              </div>

              <div className="space-y-2">
                <Label>Salary Range (Max)</Label>
                <Input
                  type="number"
                  placeholder="Max salary"
                  value={searchParams.salary_max || ''}
                  onChange={(e) => handleFilterChange('salary_max', e.target.value ? parseInt(e.target.value) : undefined)}
                />
              </div>

              <div className="space-y-2 flex items-center">
                <Checkbox
                  id="remote"
                  checked={searchParams.remote}
                  onCheckedChange={(checked) => handleFilterChange('remote', checked)}
                />
                <Label htmlFor="remote" className="ml-2">Remote Only</Label>
              </div>
            </div>

            <div className="space-y-2">
              <Label>Skills</Label>
              <div className="flex flex-wrap gap-2">
                {commonSkills.map((skill) => (
                  <Badge
                    key={skill}
                    variant={searchParams.skills.includes(skill) ? 'default' : 'outline'}
                    className="cursor-pointer"
                    onClick={() => {
                      const newSkills = searchParams.skills.includes(skill)
                        ? searchParams.skills.filter(s => s !== skill)
                        : [...searchParams.skills, skill];
                      handleFilterChange('skills', newSkills);
                    }}
                  >
                    {skill}
                  </Badge>
                ))}
              </div>
            </div>

            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={() => setSearchParams({
                  ...searchParams,
                  query: '',
                  location: '',
                  employment_type: '',
                  experience_level: '',
                  remote: false,
                  salary_min: undefined,
                  salary_max: undefined,
                  skills: [],
                })}
              >
                Clear Filters
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Results */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Spinner />
        </div>
      ) : jobsData && jobsData.results.length > 0 ? (
        <>
          <div className="space-y-4">
            {jobsData.results.map((job) => (
              <JobCard key={job.id} job={job} />
            ))}
          </div>

          <Pagination>
            <PaginationContent>
              <PaginationItem>
                <PaginationPrevious 
                  onClick={() => handlePageChange(Math.max(1, jobsData.page - 1))}
                  className={jobsData.page === 1 ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
                />
              </PaginationItem>
              {Array.from({ length: Math.min(5, jobsData.total_pages) }, (_, i) => {
                const pageNum = i + 1;
                return (
                  <PaginationItem key={pageNum}>
                    <PaginationLink
                      onClick={() => handlePageChange(pageNum)}
                      isActive={pageNum === jobsData.page}
                      className="cursor-pointer"
                    >
                      {pageNum}
                    </PaginationLink>
                  </PaginationItem>
                );
              })}
              <PaginationItem>
                <PaginationNext 
                  onClick={() => handlePageChange(Math.min(jobsData.total_pages, jobsData.page + 1))}
                  className={jobsData.page === jobsData.total_pages ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
                />
              </PaginationItem>
            </PaginationContent>
          </Pagination>
        </>
      ) : (
        <EmptyState
          title="No jobs found"
          description="Try adjusting your search criteria or filters"
        />
      )}
    </div>
  );
}

interface JobCardProps {
  job: any;
}

function JobCard({ job }: JobCardProps) {
  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="pt-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <div className="flex items-start gap-4">
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
          </div>
          <Link to={`/candidate/jobs/${job.id}`}>
            <Button>View Details</Button>
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
