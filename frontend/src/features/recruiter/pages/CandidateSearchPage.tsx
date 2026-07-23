import { useState } from 'react';
import { CandidateSearchFilters, CandidateFilters } from '../components/CandidateSearchFilters';
import { CandidateSearchResults } from '../components/CandidateSearchResults';

export function CandidateSearchPage() {
  const [filters, setFilters] = useState<CandidateFilters>({});

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Candidate Search</h1>
        <p className="text-muted-foreground">
          Find the perfect candidates for your open positions
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-4">
        <div className="lg:col-span-1">
          <CandidateSearchFilters filters={filters} onFiltersChange={setFilters} />
        </div>
        <div className="lg:col-span-3">
          <CandidateSearchResults filters={filters} />
        </div>
      </div>
    </div>
  );
}
