import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { useCreateJob, useUpdateJob, useJob } from '../hooks';
import { useForm } from 'react-hook-form';
import { toast } from 'sonner';
import { X, Plus, Briefcase, DollarSign } from 'lucide-react';
import { useNavigate, useParams } from 'react-router-dom';

interface JobFormData {
  title: string;
  company_name: string;
  location: string;
  employment_type: 'full_time' | 'part_time' | 'contract' | 'internship';
  experience_level: 'entry' | 'junior' | 'mid' | 'senior' | 'lead';
  description: string;
  requirements?: string;
  responsibilities?: string;
  salary_min?: string;
  salary_max?: string;
  currency: string;
  is_remote: boolean;
  status: 'draft' | 'active';
  skills: string[];
}

const EMPLOYMENT_TYPES = [
  { value: 'full_time', label: 'Full Time' },
  { value: 'part_time', label: 'Part Time' },
  { value: 'contract', label: 'Contract' },
  { value: 'internship', label: 'Internship' },
];

const EXPERIENCE_LEVELS = [
  { value: 'entry', label: 'Entry Level' },
  { value: 'junior', label: 'Junior' },
  { value: 'mid', label: 'Mid Level' },
  { value: 'senior', label: 'Senior' },
  { value: 'lead', label: 'Lead' },
];

const COMMON_SKILLS = [
  'JavaScript',
  'TypeScript',
  'Python',
  'Java',
  'React',
  'Node.js',
  'AWS',
  'Docker',
  'Kubernetes',
  'SQL',
  'Git',
  'Agile',
  'Communication',
  'Problem Solving',
];

interface JobFormProps {
  mode?: 'create' | 'edit';
}

export function JobForm({ mode = 'create' }: JobFormProps) {
  const navigate = useNavigate();
  const { id } = useParams();
  const isEdit = mode === 'edit' && id;

  const { data: job, isLoading: isLoadingJob } = useJob(id || '');
  const createJob = useCreateJob();
  const updateJob = useUpdateJob();

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isDirty },
  } = useForm<JobFormData>({
    defaultValues: {
      title: '',
      company_name: '',
      location: '',
      employment_type: 'full_time',
      experience_level: 'mid',
      description: '',
      requirements: '',
      responsibilities: '',
      salary_min: '',
      salary_max: '',
      currency: 'USD',
      is_remote: false,
      status: 'draft',
      skills: [],
    },
  });

  // Update form when job data loads
  React.useEffect(() => {
    if (isEdit && job) {
      setValue('title', job.title);
      setValue('company_name', job.company_name);
      setValue('location', job.location);
      setValue('employment_type', job.employment_type);
      setValue('experience_level', job.experience_level);
      setValue('description', job.description);
      setValue('requirements', job.requirements || '');
      setValue('responsibilities', job.responsibilities || '');
      setValue('salary_min', job.salary_min?.toString() || '');
      setValue('salary_max', job.salary_max?.toString() || '');
      setValue('currency', job.currency);
      setValue('is_remote', job.is_remote);
      setValue('status', job.status === 'closed' ? 'draft' : job.status);
      setValue('skills', job.skills || []);
    }
  }, [isEdit, job, setValue]);

  const skills = watch('skills') || [];
  const isRemote = watch('is_remote') || false;
  const status = watch('status') || 'draft';

  const onSubmit = async (data: any) => {
    try {
      const jobData = {
        ...data,
        salary_min: data.salary_min ? parseFloat(data.salary_min) : undefined,
        salary_max: data.salary_max ? parseFloat(data.salary_max) : undefined,
      };

      if (isEdit && id) {
        await updateJob.mutateAsync({ id, data: jobData });
        toast.success('Job updated successfully');
      } else {
        const newJob = await createJob.mutateAsync(jobData);
        toast.success('Job created successfully');
        navigate(`/recruiter/jobs/${newJob.id}`);
      }
    } catch (error) {
      toast.error(isEdit ? 'Failed to update job' : 'Failed to create job');
    }
  };

  const addSkill = (skill: string) => {
    if (!skills.includes(skill)) {
      setValue('skills', [...skills, skill]);
    }
  };

  const removeSkill = (skill: string) => {
    setValue('skills', skills.filter((s) => s !== skill));
  };

  if (isEdit && isLoadingJob) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <p className="text-muted-foreground">Loading job...</p>
        </div>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {/* Basic Information */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Briefcase className="h-5 w-5" />
            Basic Information
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="title">Job Title *</Label>
            <Input
              id="title"
              {...register('title')}
              placeholder="Senior Software Engineer"
            />
            {errors.title && (
              <p className="text-sm text-red-500">{errors.title.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="company_name">Company Name *</Label>
            <Input
              id="company_name"
              {...register('company_name')}
              placeholder="Acme Corporation"
            />
            {errors.company_name && (
              <p className="text-sm text-red-500">{errors.company_name.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="location">Location *</Label>
            <Input
              id="location"
              {...register('location')}
              placeholder="San Francisco, CA"
            />
            {errors.location && (
              <p className="text-sm text-red-500">{errors.location.message}</p>
            )}
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="employment_type">Employment Type *</Label>
              <Select
                value={watch('employment_type')}
                onValueChange={(value) =>
                  setValue('employment_type', value as any)
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select employment type" />
                </SelectTrigger>
                <SelectContent>
                  {EMPLOYMENT_TYPES.map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      {type.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {errors.employment_type && (
                <p className="text-sm text-red-500">
                  {errors.employment_type.message}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="experience_level">Experience Level *</Label>
              <Select
                value={watch('experience_level')}
                onValueChange={(value) =>
                  setValue('experience_level', value as any)
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select experience level" />
                </SelectTrigger>
                <SelectContent>
                  {EXPERIENCE_LEVELS.map((level) => (
                    <SelectItem key={level.value} value={level.value}>
                      {level.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {errors.experience_level && (
                <p className="text-sm text-red-500">
                  {errors.experience_level.message}
                </p>
              )}
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <Switch
              id="is_remote"
              checked={isRemote}
              onCheckedChange={(checked) => setValue('is_remote', checked)}
            />
            <Label htmlFor="is_remote" className="cursor-pointer">
              This is a remote position
            </Label>
          </div>
        </CardContent>
      </Card>

      {/* Job Description */}
      <Card>
        <CardHeader>
          <CardTitle>Job Description</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="description">Description *</Label>
            <Textarea
              id="description"
              {...register('description')}
              placeholder="Describe the role, team, and what the candidate will be working on..."
              rows={6}
            />
            {errors.description && (
              <p className="text-sm text-red-500">{errors.description.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="responsibilities">Responsibilities</Label>
            <Textarea
              id="responsibilities"
              {...register('responsibilities')}
              placeholder="List the key responsibilities and day-to-day tasks..."
              rows={4}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="requirements">Requirements</Label>
            <Textarea
              id="requirements"
              {...register('requirements')}
              placeholder="List the required qualifications, skills, and experience..."
              rows={4}
            />
          </div>
        </CardContent>
      </Card>

      {/* Skills */}
      <Card>
        <CardHeader>
          <CardTitle>Required Skills</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-2">
            {COMMON_SKILLS.map((skill) => (
              <Badge
                key={skill}
                variant={skills.includes(skill) ? 'default' : 'outline'}
                className="cursor-pointer"
                onClick={() =>
                  skills.includes(skill) ? removeSkill(skill) : addSkill(skill)
                }
              >
                {skills.includes(skill) && <X className="h-3 w-3 mr-1" />}
                {skill}
              </Badge>
            ))}
          </div>
          <div className="flex gap-2">
            <Input
              placeholder="Add custom skill"
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  const value = e.currentTarget.value;
                  if (value && !skills.includes(value)) {
                    addSkill(value);
                    e.currentTarget.value = '';
                  }
                }
              }}
            />
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                const input = document.querySelector(
                  'input[placeholder="Add custom skill"]'
                ) as HTMLInputElement;
                if (input?.value && !skills.includes(input.value)) {
                  addSkill(input.value);
                  input.value = '';
                }
              }}
            >
              <Plus className="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Compensation */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <DollarSign className="h-5 w-5" />
            Compensation
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-3">
            <div className="space-y-2">
              <Label htmlFor="salary_min">Minimum Salary</Label>
              <Input
                id="salary_min"
                {...register('salary_min')}
                type="number"
                placeholder="80000"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="salary_max">Maximum Salary</Label>
              <Input
                id="salary_max"
                {...register('salary_max')}
                type="number"
                placeholder="120000"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="currency">Currency</Label>
              <Select
                value={watch('currency')}
                onValueChange={(value) => setValue('currency', value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select currency" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="USD">USD</SelectItem>
                  <SelectItem value="EUR">EUR</SelectItem>
                  <SelectItem value="GBP">GBP</SelectItem>
                  <SelectItem value="CAD">CAD</SelectItem>
                  <SelectItem value="AUD">AUD</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Job Status */}
      <Card>
        <CardHeader>
          <CardTitle>Job Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <input
                type="radio"
                id="draft"
                value="draft"
                checked={status === 'draft'}
                onChange={() => setValue('status', 'draft')}
                className="h-4 w-4"
              />
              <Label htmlFor="draft" className="cursor-pointer">
                Draft - Save as draft, not visible to candidates
              </Label>
            </div>
            <div className="flex items-center space-x-2">
              <input
                type="radio"
                id="active"
                value="active"
                checked={status === 'active'}
                onChange={() => setValue('status', 'active')}
                className="h-4 w-4"
              />
              <Label htmlFor="active" className="cursor-pointer">
                Active - Publish and make visible to candidates
              </Label>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-between">
        <Button
          type="button"
          variant="outline"
          onClick={() => navigate('/recruiter/jobs')}
        >
          Cancel
        </Button>
        <div className="flex gap-4">
          <Button
            type="button"
            variant="outline"
            onClick={() => {
              setValue('status', 'draft');
              handleSubmit(onSubmit)();
            }}
            disabled={!isDirty}
          >
            Save as Draft
          </Button>
          <Button
            type="button"
            onClick={() => {
              setValue('status', 'active');
              handleSubmit(onSubmit)();
            }}
            disabled={!isDirty}
          >
            {isEdit ? 'Update Job' : 'Publish Job'}
          </Button>
        </div>
      </div>
    </form>
  );
}
