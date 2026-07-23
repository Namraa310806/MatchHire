import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Search, Filter, X } from 'lucide-react';

interface FilterOption {
  value: string;
  label: string;
}

interface AdminFilterBarProps {
  searchPlaceholder?: string;
  searchValue: string;
  onSearchChange: (value: string) => void;
  filters?: {
    key: string;
    label: string;
    options: FilterOption[];
    value: string;
    onChange: (value: string) => void;
  }[];
  onClear?: () => void;
}

export function AdminFilterBar({
  searchPlaceholder = 'Search...',
  searchValue,
  onSearchChange,
  filters = [],
  onClear,
}: AdminFilterBarProps) {
  const hasActiveFilters = searchValue || filters.some(f => f.value);

  return (
    <div className="flex flex-col gap-4 md:flex-row md:items-center">
      <div className="flex-1">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <Input
            placeholder={searchPlaceholder}
            value={searchValue}
            onChange={(e) => onSearchChange(e.target.value)}
            className="pl-10 border-slate-700 bg-slate-800/50"
          />
        </div>
      </div>
      <div className="flex gap-2 flex-wrap">
        {filters.map((filter) => (
          <Select key={filter.key} value={filter.value} onValueChange={filter.onChange}>
            <SelectTrigger className="w-40 border-slate-700 bg-slate-800/50">
              <Filter className="h-4 w-4 mr-2" />
              <SelectValue placeholder={filter.label} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">{`All ${filter.label}s`}</SelectItem>
              {filter.options.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        ))}
        {hasActiveFilters && onClear && (
          <Button
            variant="outline"
            onClick={onClear}
            className="border-slate-700"
          >
            <X className="h-4 w-4 mr-2" />
            Clear
          </Button>
        )}
      </div>
    </div>
  );
}
