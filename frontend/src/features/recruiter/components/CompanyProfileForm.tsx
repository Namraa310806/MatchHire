import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { FileUpload } from '@/components/ui/file-upload';
import { useRecruiterProfile } from '../hooks';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { toast } from 'sonner';
import { X, Plus, Building2, Users, Link as LinkIcon } from 'lucide-react';

const companyProfileSchema = z.object({
  company: z.string().min(1, 'Company name is required'),
  title: z.string().min(1, 'Job title is required'),
  location: z.string().min(1, 'Location is required'),
  company_website: z.string().url('Invalid URL').optional().or(z.literal('')),
  company_size: z.string().optional(),
  industry: z.string().optional(),
  company_description: z.string().optional(),
  benefits: z.array(z.string()).optional(),
  culture: z.string().optional(),
  social_links: z.object({
    linkedin: z.string().url('Invalid URL').optional().or(z.literal('')),
    twitter: z.string().url('Invalid URL').optional().or(z.literal('')),
    facebook: z.string().url('Invalid URL').optional().or(z.literal('')),
  }).optional(),
  hiring_preferences: z.object({
    experience_levels: z.array(z.string()).optional(),
    employment_types: z.array(z.string()).optional(),
    remote_friendly: z.boolean().optional(),
  }).optional(),
});

type CompanyProfileFormData = z.infer<typeof companyProfileSchema>;

const COMPANY_SIZES = [
  '1-10',
  '11-50',
  '51-200',
  '201-500',
  '501-1000',
  '1000+',
];

const INDUSTRIES = [
  'Technology',
  'Healthcare',
  'Finance',
  'Education',
  'Retail',
  'Manufacturing',
  'Consulting',
  'Media',
  'Non-profit',
  'Other',
];

const EXPERIENCE_LEVELS = ['entry', 'junior', 'mid', 'senior', 'lead'];
const EMPLOYMENT_TYPES = ['full_time', 'part_time', 'contract', 'internship'];
const COMMON_BENEFITS = [
  'Health Insurance',
  'Remote Work',
  'Flexible Hours',
  '401(k)',
  'Paid Time Off',
  'Stock Options',
  'Gym Membership',
  'Learning Budget',
];

export function CompanyProfileForm() {
  const { profile, updateProfile, uploadLogo, isUpdating } = useRecruiterProfile();

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isDirty },
  } = useForm<CompanyProfileFormData>({
    resolver: zodResolver(companyProfileSchema),
    defaultValues: {
      company: profile?.company || '',
      title: profile?.title || '',
      location: profile?.location || '',
      company_website: profile?.company_website || '',
      company_size: profile?.company_size || '',
      industry: profile?.industry || '',
      company_description: profile?.company_description || '',
      benefits: profile?.benefits || [],
      culture: profile?.culture || '',
      social_links: profile?.social_links || {
        linkedin: '',
        twitter: '',
        facebook: '',
      },
      hiring_preferences: profile?.hiring_preferences || {
        experience_levels: [],
        employment_types: [],
        remote_friendly: false,
      },
    },
  });

  const benefits = watch('benefits') || [];
  const experienceLevels = watch('hiring_preferences.experience_levels') || [];
  const employmentTypes = watch('hiring_preferences.employment_types') || [];
  const remoteFriendly = watch('hiring_preferences.remote_friendly') || false;

  const onSubmit = async (data: CompanyProfileFormData) => {
    try {
      await updateProfile(data);
      toast.success('Company profile updated successfully');
    } catch (error) {
      toast.error('Failed to update company profile');
    }
  };

  const handleLogoUpload = async (files: File[]) => {
    if (files.length > 0) {
      try {
        await uploadLogo(files[0]);
        toast.success('Company logo uploaded successfully');
      } catch (error) {
        toast.error('Failed to upload logo');
      }
    }
  };

  const addBenefit = (benefit: string) => {
    if (!benefits.includes(benefit)) {
      setValue('benefits', [...benefits, benefit]);
    }
  };

  const removeBenefit = (benefit: string) => {
    setValue('benefits', benefits.filter((b) => b !== benefit));
  };

  const toggleExperienceLevel = (level: string) => {
    const current = experienceLevels.includes(level)
      ? experienceLevels.filter((l) => l !== level)
      : [...experienceLevels, level];
    setValue('hiring_preferences.experience_levels', current);
  };

  const toggleEmploymentType = (type: string) => {
    const current = employmentTypes.includes(type)
      ? employmentTypes.filter((t) => t !== type)
      : [...employmentTypes, type];
    setValue('hiring_preferences.employment_types', current);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {/* Company Logo */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Building2 className="h-5 w-5" />
            Company Logo
          </CardTitle>
        </CardHeader>
        <CardContent>
          <FileUpload
            accept="image/*"
            maxSize={5 * 1024 * 1024}
            onFileSelect={handleLogoUpload}
            multiple={false}
          />
          {profile?.company_logo && (
            <div className="mt-4">
              <p className="text-sm text-muted-foreground mb-2">Current logo:</p>
              <img
                src={profile.company_logo}
                alt="Company logo"
                className="h-20 w-auto rounded border"
              />
            </div>
          )}
        </CardContent>
      </Card>

      {/* Basic Information */}
      <Card>
        <CardHeader>
          <CardTitle>Basic Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="company">Company Name *</Label>
              <Input
                id="company"
                {...register('company')}
                placeholder="Acme Corporation"
              />
              {errors.company && (
                <p className="text-sm text-red-500">{errors.company.message}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="title">Your Title *</Label>
              <Input
                id="title"
                {...register('title')}
                placeholder="Senior Recruiter"
              />
              {errors.title && (
                <p className="text-sm text-red-500">{errors.title.message}</p>
              )}
            </div>
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
              <Label htmlFor="company_website">Website</Label>
              <Input
                id="company_website"
                {...register('company_website')}
                placeholder="https://example.com"
              />
              {errors.company_website && (
                <p className="text-sm text-red-500">{errors.company_website.message}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="company_size">Company Size</Label>
              <Select
                value={watch('company_size')}
                onValueChange={(value) => setValue('company_size', value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select company size" />
                </SelectTrigger>
                <SelectContent>
                  {COMPANY_SIZES.map((size) => (
                    <SelectItem key={size} value={size}>
                      {size} employees
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="industry">Industry</Label>
            <Select
              value={watch('industry')}
              onValueChange={(value) => setValue('industry', value)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select industry" />
              </SelectTrigger>
              <SelectContent>
                {INDUSTRIES.map((industry) => (
                  <SelectItem key={industry} value={industry}>
                    {industry}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Company Description */}
      <Card>
        <CardHeader>
          <CardTitle>Company Description</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="company_description">About the Company</Label>
            <Textarea
              id="company_description"
              {...register('company_description')}
              placeholder="Tell candidates about your company mission, values, and what makes it a great place to work..."
              rows={4}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="culture">Company Culture</Label>
            <Textarea
              id="culture"
              {...register('culture')}
              placeholder="Describe your work environment, team dynamics, and company culture..."
              rows={3}
            />
          </div>
        </CardContent>
      </Card>

      {/* Benefits */}
      <Card>
        <CardHeader>
          <CardTitle>Benefits & Perks</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-2">
            {COMMON_BENEFITS.map((benefit) => (
              <Badge
                key={benefit}
                variant={benefits.includes(benefit) ? 'default' : 'outline'}
                className="cursor-pointer"
                onClick={() =>
                  benefits.includes(benefit)
                    ? removeBenefit(benefit)
                    : addBenefit(benefit)
                }
              >
                {benefits.includes(benefit) && <X className="h-3 w-3 mr-1" />}
                {benefit}
              </Badge>
            ))}
          </div>
          <div className="flex gap-2">
            <Input
              placeholder="Add custom benefit"
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  const value = e.currentTarget.value;
                  if (value && !benefits.includes(value)) {
                    addBenefit(value);
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
                  'input[placeholder="Add custom benefit"]'
                ) as HTMLInputElement;
                if (input?.value && !benefits.includes(input.value)) {
                  addBenefit(input.value);
                  input.value = '';
                }
              }}
            >
              <Plus className="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Social Links */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <LinkIcon className="h-5 w-5" />
            Social Links
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="linkedin">LinkedIn</Label>
            <Input
              id="linkedin"
              {...register('social_links.linkedin')}
              placeholder="https://linkedin.com/company/yourcompany"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="twitter">Twitter/X</Label>
            <Input
              id="twitter"
              {...register('social_links.twitter')}
              placeholder="https://twitter.com/yourcompany"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="facebook">Facebook</Label>
            <Input
              id="facebook"
              {...register('social_links.facebook')}
              placeholder="https://facebook.com/yourcompany"
            />
          </div>
        </CardContent>
      </Card>

      {/* Hiring Preferences */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Hiring Preferences
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Experience Levels</Label>
            <div className="flex flex-wrap gap-2">
              {EXPERIENCE_LEVELS.map((level) => (
                <Badge
                  key={level}
                  variant={experienceLevels.includes(level) ? 'default' : 'outline'}
                  className="cursor-pointer capitalize"
                  onClick={() => toggleExperienceLevel(level)}
                >
                  {level}
                </Badge>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <Label>Employment Types</Label>
            <div className="flex flex-wrap gap-2">
              {EMPLOYMENT_TYPES.map((type) => (
                <Badge
                  key={type}
                  variant={employmentTypes.includes(type) ? 'default' : 'outline'}
                  className="cursor-pointer capitalize"
                  onClick={() => toggleEmploymentType(type)}
                >
                  {type.replace('_', ' ')}
                </Badge>
              ))}
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="remote_friendly"
              checked={remoteFriendly}
              onChange={(e) =>
                setValue('hiring_preferences.remote_friendly', e.target.checked)
              }
              className="h-4 w-4"
            />
            <Label htmlFor="remote_friendly" className="cursor-pointer">
              Remote-friendly company
            </Label>
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end gap-4">
        <Button type="submit" disabled={!isDirty || isUpdating}>
          {isUpdating ? 'Saving...' : 'Save Changes'}
        </Button>
      </div>
    </form>
  );
}
