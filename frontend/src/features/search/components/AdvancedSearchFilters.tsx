import React, { useState } from 'react';
import { Filter, X } from 'lucide-react';
import { useSearch } from '../context/SearchContext';
import { SearchFilters, SearchSortOption } from '../types';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { cn } from '@/lib/utils';

interface AdvancedSearchFiltersProps {
  className?: string;
}

const EMPLOYMENT_TYPES = [
  { value: 'full_time', label: 'Full-time' },
  { value: 'part_time', label: 'Part-time' },
  { value: 'contract', label: 'Contract' },
  { value: 'internship', label: 'Internship' },
];

const EDUCATION_LEVELS = [
  { value: 'high_school', label: 'High School' },
  { value: 'associate', label: "Associate's Degree" },
  { value: 'bachelor', label: "Bachelor's Degree" },
  { value: 'master', label: "Master's Degree" },
  { value: 'phd', label: 'PhD' },
];

const SORT_OPTIONS: Array<{ value: SearchSortOption; label: string }> = [
  { value: 'relevance', label: 'Relevance' },
  { value: 'match_score', label: 'Match Score' },
  { value: 'recent', label: 'Most Recent' },
  { value: 'salary_high', label: 'Salary: High to Low' },
  { value: 'salary_low', label: 'Salary: Low to High' },
  { value: 'experience', label: 'Experience Level' },
];

export const AdvancedSearchFilters: React.FC<AdvancedSearchFiltersProps> = ({ className }) => {
  const { query, setFilters, setSort } = useSearch();
  const [expandedSections, setExpandedSections] = useState<string[]>(['location', 'skills']);

  const filters = query.filters;

  const activeFilterCount = Object.values(filters).filter(
    (value) => value !== undefined && value !== null && value !== '' &&
    (Array.isArray(value) ? value.length > 0 : true)
  ).length;

  const handleFilterChange = (key: keyof SearchFilters, value: any) => {
    setFilters({ [key]: value });
  };

  const handleEmploymentTypeToggle = (value: string) => {
    const current = filters.employment_type || [];
    const updated = current.includes(value as any)
      ? current.filter((v: string) => v !== value)
      : [...current, value];
    setFilters({ employment_type: updated as any });
  };

  const handleEducationLevelToggle = (value: string) => {
    const current = filters.education_level || [];
    const updated = current.includes(value)
      ? current.filter((v: string) => v !== value)
      : [...current, value];
    setFilters({ education_level: updated });
  };

  const clearAllFilters = () => {
    setFilters({});
    setSort('relevance');
  };

  const hasActiveFilters = activeFilterCount > 0;

  return (
    <div className={cn('space-y-4', className)}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Filter className="h-5 w-5" />
          <h3 className="font-semibold">Filters</h3>
          {hasActiveFilters && (
            <Badge variant="secondary">{activeFilterCount} active</Badge>
          )}
        </div>
        {hasActiveFilters && (
          <Button variant="ghost" size="sm" onClick={clearAllFilters}>
            <X className="h-4 w-4 mr-1" />
            Clear all
          </Button>
        )}
      </div>

      <Accordion
        type="multiple"
        value={expandedSections}
        onValueChange={setExpandedSections}
        className="w-full"
      >
        {/* Location Filter */}
        <AccordionItem value="location">
          <AccordionTrigger className="text-sm">Location</AccordionTrigger>
          <AccordionContent className="space-y-3 pt-2">
            <div>
              <Label htmlFor="location">City, State, or Country</Label>
              <Input
                id="location"
                placeholder="e.g., San Francisco, CA"
                value={filters.location || ''}
                onChange={(e) => handleFilterChange('location', e.target.value)}
                className="mt-1"
              />
            </div>
            <div className="flex items-center space-x-2">
              <Checkbox
                id="remote"
                checked={filters.remote || false}
                onCheckedChange={(checked) => handleFilterChange('remote', checked)}
              />
              <Label htmlFor="remote" className="text-sm font-normal">
                Remote only
              </Label>
            </div>
          </AccordionContent>
        </AccordionItem>

        {/* Skills Filter */}
        <AccordionItem value="skills">
          <AccordionTrigger className="text-sm">Skills</AccordionTrigger>
          <AccordionContent className="space-y-3 pt-2">
            <div>
              <Label htmlFor="skills">Skills (comma separated)</Label>
              <Input
                id="skills"
                placeholder="e.g., React, TypeScript, Python"
                value={filters.skills?.join(', ') || ''}
                onChange={(e) => {
                  const skills = e.target.value
                    .split(',')
                    .map((s) => s.trim())
                    .filter(Boolean);
                  handleFilterChange('skills', skills);
                }}
                className="mt-1"
              />
            </div>
            {filters.skills && filters.skills.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {filters.skills.map((skill: string) => (
                  <Badge key={skill} variant="secondary" className="text-xs">
                    {skill}
                    <button
                      onClick={() => {
                        const updated = filters.skills?.filter((s: string) => s !== skill);
                        handleFilterChange('skills', updated);
                      }}
                      className="ml-1 hover:text-destructive"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </Badge>
                ))}
              </div>
            )}
          </AccordionContent>
        </AccordionItem>

        {/* Experience Filter */}
        <AccordionItem value="experience">
          <AccordionTrigger className="text-sm">Experience Level</AccordionTrigger>
          <AccordionContent className="space-y-3 pt-2">
            <div>
              <Label>
                Years of Experience: {filters.experience_min || 0} - {filters.experience_max || '10+'}
              </Label>
              <div className="grid grid-cols-2 gap-3 mt-2">
                <div>
                  <Label htmlFor="exp-min" className="text-xs">Min Years</Label>
                  <Input
                    id="exp-min"
                    type="number"
                    min="0"
                    max="10"
                    placeholder="0"
                    value={filters.experience_min || ''}
                    onChange={(e) => handleFilterChange('experience_min', e.target.value ? Number(e.target.value) : undefined)}
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label htmlFor="exp-max" className="text-xs">Max Years</Label>
                  <Input
                    id="exp-max"
                    type="number"
                    min="0"
                    max="10"
                    placeholder="10"
                    value={filters.experience_max || ''}
                    onChange={(e) => handleFilterChange('experience_max', e.target.value ? Number(e.target.value) : undefined)}
                    className="mt-1"
                  />
                </div>
              </div>
            </div>
          </AccordionContent>
        </AccordionItem>

        {/* Salary Filter */}
        <AccordionItem value="salary">
          <AccordionTrigger className="text-sm">Salary Range</AccordionTrigger>
          <AccordionContent className="space-y-3 pt-2">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label htmlFor="salary-min">Min ($)</Label>
                <Input
                  id="salary-min"
                  type="number"
                  placeholder="0"
                  value={filters.salary_min || ''}
                  onChange={(e) => handleFilterChange('salary_min', e.target.value ? Number(e.target.value) : undefined)}
                  className="mt-1"
                />
              </div>
              <div>
                <Label htmlFor="salary-max">Max ($)</Label>
                <Input
                  id="salary-max"
                  type="number"
                  placeholder="Any"
                  value={filters.salary_max || ''}
                  onChange={(e) => handleFilterChange('salary_max', e.target.value ? Number(e.target.value) : undefined)}
                  className="mt-1"
                />
              </div>
            </div>
          </AccordionContent>
        </AccordionItem>

        {/* Employment Type Filter */}
        <AccordionItem value="employment_type">
          <AccordionTrigger className="text-sm">Employment Type</AccordionTrigger>
          <AccordionContent className="space-y-2 pt-2">
            {EMPLOYMENT_TYPES.map((type) => (
              <div key={type.value} className="flex items-center space-x-2">
                <Checkbox
                  id={`employment-${type.value}`}
                  checked={filters.employment_type?.includes(type.value as any) || false}
                  onCheckedChange={() => handleEmploymentTypeToggle(type.value as any)}
                />
                <Label
                  htmlFor={`employment-${type.value}`}
                  className="text-sm font-normal cursor-pointer"
                >
                  {type.label}
                </Label>
              </div>
            ))}
          </AccordionContent>
        </AccordionItem>

        {/* Education Level Filter */}
        <AccordionItem value="education">
          <AccordionTrigger className="text-sm">Education Level</AccordionTrigger>
          <AccordionContent className="space-y-2 pt-2">
            {EDUCATION_LEVELS.map((level) => (
              <div key={level.value} className="flex items-center space-x-2">
                <Checkbox
                  id={`education-${level.value}`}
                  checked={filters.education_level?.includes(level.value) || false}
                  onCheckedChange={() => handleEducationLevelToggle(level.value)}
                />
                <Label
                  htmlFor={`education-${level.value}`}
                  className="text-sm font-normal cursor-pointer"
                >
                  {level.label}
                </Label>
              </div>
            ))}
          </AccordionContent>
        </AccordionItem>

        {/* Company Filter */}
        <AccordionItem value="company">
          <AccordionTrigger className="text-sm">Company</AccordionTrigger>
          <AccordionContent className="space-y-3 pt-2">
            <div>
              <Label htmlFor="company">Companies (comma separated)</Label>
              <Input
                id="company"
                placeholder="e.g., Google, Microsoft, Apple"
                value={filters.company?.join(', ') || ''}
                onChange={(e) => {
                  const companies = e.target.value
                    .split(',')
                    .map((s) => s.trim())
                    .filter(Boolean);
                  handleFilterChange('company', companies);
                }}
                className="mt-1"
              />
            </div>
            {filters.company && filters.company.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {filters.company.map((company: string) => (
                  <Badge key={company} variant="secondary" className="text-xs">
                    {company}
                    <button
                      onClick={() => {
                        const updated = filters.company?.filter((c: string) => c !== company);
                        handleFilterChange('company', updated);
                      }}
                      className="ml-1 hover:text-destructive"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </Badge>
                ))}
              </div>
            )}
          </AccordionContent>
        </AccordionItem>
      </Accordion>

      <div className="border-t pt-4 mt-4" />

      {/* Sort */}
      <div className="space-y-2">
        <Label htmlFor="sort">Sort by</Label>
        <Select value={query.sort} onValueChange={(value: SearchSortOption) => setSort(value)}>
          <SelectTrigger id="sort">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {SORT_OPTIONS.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </div>
  );
};
