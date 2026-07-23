import React from 'react';
import { SearchProvider, useSearch } from '../context/SearchContext';
import { GlobalSearchBar } from '../components/GlobalSearchBar';
import { AdvancedSearchFilters } from '../components/AdvancedSearchFilters';
import { SearchResultCard } from '../components/SearchResultCard';
import { SearchResultsSkeleton } from '../components/SearchLoadingStates';
import { EmptySearchState, SearchErrorState } from '../components/SearchEmptyStates';

const SearchContent: React.FC = () => {
  const { query, state, setFilters, clearSearch } = useSearch();

  const handleClearFilters = () => {
    setFilters({});
  };

  const handleResetSearch = () => {
    clearSearch();
  };

  if (state.isSearching) {
    return (
      <div className="space-y-6">
        <GlobalSearchBar autoFocus />
        <SearchResultsSkeleton count={6} />
      </div>
    );
  }

  if (state.error) {
    return (
      <div className="space-y-6">
        <GlobalSearchBar autoFocus />
        <SearchErrorState 
          message={state.error}
          onRetry={() => window.location.reload()}
        />
      </div>
    );
  }

  if (!query.q && Object.keys(query.filters).length === 0) {
    return (
      <div className="space-y-6">
        <GlobalSearchBar autoFocus />
        <div className="text-center py-12">
          <h2 className="text-2xl font-bold mb-2">Search Jobs & Candidates</h2>
          <p className="text-muted-foreground">
            Use the search bar above to find jobs, candidates, skills, and more.
          </p>
        </div>
      </div>
    );
  }

  if (state.results.length === 0) {
    return (
      <div className="space-y-6">
        <GlobalSearchBar autoFocus />
        <EmptySearchState 
          onClearFilters={handleClearFilters}
          onResetSearch={handleResetSearch}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <GlobalSearchBar autoFocus />
      
      <div className="flex flex-col lg:flex-row gap-6">
        {/* Filters Sidebar */}
        <aside className="lg:w-80 flex-shrink-0">
          <AdvancedSearchFilters />
        </aside>

        {/* Results */}
        <div className="flex-1">
          <div className="flex items-center justify-between mb-4">
            <p className="text-sm text-muted-foreground">
              {state.total} results found
            </p>
          </div>
          
          <div className="grid gap-4">
            {state.results.map((result) => (
              <SearchResultCard
                key={result.id}
                result={result}
                onResultClick={(result) => console.log('Clicked result:', result)}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export const SearchPage: React.FC = () => {
  return (
    <SearchProvider>
      <div className="container mx-auto py-8">
        <SearchContent />
      </div>
    </SearchProvider>
  );
};
