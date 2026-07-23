import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { X, Plus, Filter } from 'lucide-react';

interface CandidateSearchFiltersProps {
  filters: CandidateFilters;
  onFiltersChange: (filters: CandidateFilters) => void;
}

export interface CandidateFilters {
  q?: string;
  skills?: string[];
  location?: string;
  experience_min?: number;
  experience_max?: number;
  education_level?: string;
  availability?: string;
  remote_friendly?: boolean;
  salary_min?: number;
  salary_max?: number;
}

const EDUCATION_LEVELS = [
  { value: 'high_school', label: 'High School' },
  { value: 'associate', label: 'Associate Degree' },
  { value: 'bachelor', label: 'Bachelor Degree' },
  { value: 'master', label: 'Master Degree' },
  { value: 'phd', label: 'PhD' },
];

const AVAILABILITY_OPTIONS = [
  { value: 'immediate', label: 'Immediate' },
  { value: '2_weeks', label: 'Within 2 weeks' },
  { value: '1_month', label: 'Within 1 month' },
  { value: '3_months', label: 'Within 3 months' },
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
  'Leadership',
  'Problem Solving',
];

export function CandidateSearchFilters({
  filters,
  onFiltersChange,
}: CandidateSearchFiltersProps) {
  const skills = filters.skills || [];

  const addSkill = (skill: string) => {
    if (!skills.includes(skill)) {
      onFiltersChange({ ...filters, skills: [...skills, skill] });
    }
  };

  const removeSkill = (skill: string) => {
    onFiltersChange({ ...filters, skills: skills.filter((s) => s !== skill) });
  };

  const clearFilters = () => {
    onFiltersChange({});
  };

  const hasActiveFilters = Object.keys(filters).some(
    (key) => filters[key as keyof CandidateFilters] !== undefined
  );

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Search Filters
          </CardTitle>
          {hasActiveFilters && (
            <Button variant="ghost" size="sm" onClick={clearFilters}>
              Clear All
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Search Query */}
        <div className="space-y-2">
          <Label htmlFor="search">Search</Label>
          <Input
            id="search"
            placeholder="Search by name, title, or skills..."
            value={filters.q || ''}
            onChange={(e) => onFiltersChange({ ...filters, q: e.target.value })}
          />
        </div>

        {/* Location */}
        <div className="space-y-2">
          <Label htmlFor="location">Location</Label>
          <Input
            id="location"
            placeholder="City, state, or country"
            value={filters.location || ''}
            onChange={(e) => onFiltersChange({ ...filters, location: e.target.value })}
          />
        </div>

        {/* Experience Range */}
        <div className="space-y-2">
          <Label>Experience (years)</Label>
          <div className="flex gap-2">
            <Input
              type="number"
              placeholder="Min"
              value={filters.experience_min || ''}
              onChange={(e) =>
                onFiltersChange({
                  ...filters,
                  experience_min: e.target.value ? parseInt(e.target.value) : undefined,
                })
              }
            />
            <Input
              type="number"
              placeholder="Max"
              value={filters.experience_max || ''}
              onChange={(e) =>
                onFiltersChange({
                  ...filters,
                  experience_max: e.target.value ? parseInt(e.target.value) : undefined,
                })
              }
            />
          </div>
        </div>

        {/* Education Level */}
        <div className="space-y-2">
          <Label htmlFor="education">Education Level</Label>
          <Select
            value={filters.education_level || ''}
            onValueChange={(value) =>
              onFiltersChange({ ...filters, education_level: value || undefined })
            }
          >
            <SelectTrigger>
              <SelectValue placeholder="Select education level" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">All Levels</SelectItem>
              {EDUCATION_LEVELS.map((level) => (
                <SelectItem key={level.value} value={level.value}>
                  {level.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Availability */}
        <div className="space-y-2">
          <Label htmlFor="availability">Availability</Label>
          <Select
            value={filters.availability || ''}
            onValueChange={(value) =>
              onFiltersChange({ ...filters, availability: value || undefined })
            }
          >
            <SelectTrigger>
              <SelectValue placeholder="Select availability" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">Any</SelectItem>
              {AVAILABILITY_OPTIONS.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Salary Range */}
        <div className="space-y-2">
          <Label>Salary Range</Label>
          <div className="flex gap-2">
            <Input
              type="number"
              placeholder="Min"
              value={filters.salary_min || ''}
              onChange={(e) =>
                onFiltersChange({
                  ...filters,
                  salary_min: e.target.value ? parseInt(e.target.value) : undefined,
                })
              }
            />
            <Input
              type="number"
              placeholder="Max"
              value={filters.salary_max || ''}
              onChange={(e) =>
                onFiltersChange({
                  ...filters,
                  salary_max: e.target.value ? parseInt(e.target.value) : undefined,
                })
              }
            />
          </div>
        </div>

        {/* Remote Friendly */}
        <div className="flex items-center space-x-2">
          <Switch
            id="remote_friendly"
            checked={filters.remote_friendly || false}
            onCheckedChange={(checked) =>
              onFiltersChange({ ...filters, remote_friendly: checked })
            }
          />
          <Label htmlFor="remote_friendly" className="cursor-pointer">
            Remote-friendly candidates only
          </Label>
        </div>

        {/* Skills */}
        <div className="space-y-2">
          <Label>Skills</Label>
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
              size="icon"
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
        </div>
      </CardContent>
    </Card>
  );
}
