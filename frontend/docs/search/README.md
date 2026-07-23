# Search & Recommendation Platform

## Overview

The MatchHire Search & Recommendation Platform is a comprehensive, AI-powered search system that provides exceptional search experiences for both candidates and recruiters. This platform showcases the backend's advanced capabilities including semantic search, hybrid ranking, and AI-powered recommendations.

## Features

### Core Search Capabilities

- **Universal Search**: Single search bar for jobs, candidates, skills, and more
- **Autocomplete**: Real-time suggestions as you type
- **Advanced Filters**: Comprehensive filtering system with boolean logic
- **Rich Results**: Detailed result cards with match scores and highlights
- **Ranking Explanations**: Understand why results appear in your search
- **Search History**: Track and reuse previous searches
- **Saved Searches**: Save and organize frequent searches

### AI-Powered Recommendations

- **Personalized Recommendations**: AI-curated job/candidate suggestions
- **Recommendation Explainability**: Understand why items are recommended
- **Feedback Loop**: Improve recommendations with your feedback
- **Similar Items**: Discover related opportunities
- **Trending Content**: See what's popular

### Analytics & Insights

- **Search Analytics**: Understand search behavior
- **Popular Searches**: See what others are searching for
- **Filter Usage**: Understand how filters are used
- **Performance Metrics**: Monitor search performance

## Quick Start

### Basic Search

```tsx
import { SearchProvider, GlobalSearchBar } from '@/features/search';

function App() {
  return (
    <SearchProvider>
      <GlobalSearchBar />
    </SearchProvider>
  );
}
```

### Full Search Page

```tsx
import { SearchPage } from '@/features/search/pages';

function App() {
  return <SearchPage />;
}
```

### Using Search Context

```tsx
import { useSearch } from '@/features/search/context/SearchContext';

function MyComponent() {
  const { query, setQuery, state } = useSearch();
  
  const handleSearch = (searchTerm: string) => {
    setQuery({ q: searchTerm, page: 1 });
  };
  
  return (
    <div>
      <input 
        value={query.q}
        onChange={(e) => handleSearch(e.target.value)}
      />
      {state.results.map(result => (
        <div key={result.id}>{result.data.title}</div>
      ))}
    </div>
  );
}
```

### Using Search Hooks

```tsx
import { useGlobalSearch, useAutocomplete } from '@/features/search/hooks/useSearch';

function MyComponent() {
  const { data, isLoading, refetch } = useGlobalSearch();
  const { data: suggestions } = useAutocomplete('react');
  
  return (
    <div>
      {isLoading && <div>Loading...</div>}
      {data?.results.map(result => (
        <div key={result.id}>{result.data.title}</div>
      ))}
    </div>
  );
}
```

## Component Reference

### SearchProvider

Wraps your application to provide search context.

```tsx
<SearchProvider>
  <YourApp />
</SearchProvider>
```

### GlobalSearchBar

Universal search bar with autocomplete and suggestions.

```tsx
<GlobalSearchBar 
  placeholder="Search jobs, candidates..."
  autoFocus={false}
  className="max-w-2xl"
/>
```

### AdvancedSearchFilters

Comprehensive filter system for advanced search.

```tsx
<AdvancedSearchFilters className="w-80" />
```

### SearchResultCard

Rich result card with match scores and actions.

```tsx
<SearchResultCard
  result={searchResult}
  onResultClick={(result) => navigate(`/jobs/${result.id}`)}
  onSave={(result) => saveItem(result)}
  showRankingExplanation={true}
  rankingExplanation={rankingData}
/>
```

### RankingExplanationComponent

Detailed visualization of ranking factors.

```tsx
<RankingExplanationComponent
  explanation={rankingExplanation}
  className="mt-4"
/>
```

### RecommendationCenter

AI-powered recommendation hub.

```tsx
<RecommendationCenter
  userType="recruiter"
  recommendedItems={recommendations}
  trendingItems={trending}
  recentlyViewed={recent}
  onItemClick={(item) => viewDetails(item)}
  onFeedback={(id, feedback) => provideFeedback(id, feedback)}
/>
```

### RecommendationExplainability

Detailed recommendation explanation with feedback.

```tsx
<RecommendationExplainability
  explanation={recommendationExplanation}
  onFeedback={(id, feedback) => provideFeedback(id, feedback)}
  onHide={(id) => hideRecommendation(id)}
/>
```

### SearchHistory

Search history management with recent and saved searches.

```tsx
<SearchHistory
  recentSearches={recent}
  savedSearches={saved}
  onRunSearch={(query, type) => executeSearch(query, type)}
  onSaveSearch={(name, query) => saveSearch(name, query)}
  onDeleteSavedSearch={(id) => deleteSearch(id)}
  onPinSearch={(id) => pinSearch(id)}
  onUnpinSearch={(id) => unpinSearch(id)}
/>
```

### SearchAnalytics

Analytics dashboard for search insights.

```tsx
<SearchAnalytics
  analytics={analyticsData}
  className="mt-6"
/>
```

## Hooks Reference

### useGlobalSearch

Main search hook with TanStack Query integration.

```tsx
const { data, isLoading, error, refetch } = useGlobalSearch();
```

### useInfiniteSearch

Infinite scrolling support for large result sets.

```tsx
const { data, fetchNextPage, hasNextPage, isFetchingNextPage } = useInfiniteSearch();
```

### useAutocomplete

Autocomplete suggestions for search input.

```tsx
const { data: suggestions, isLoading } = useAutocomplete('react', 'job');
```

### useRankingExplanation

Get ranking explanation for a specific result.

```tsx
const { data: explanation } = useRankingExplanation(resultId, 'job');
```

### useSavedSearches

Manage saved searches.

```tsx
const { 
  savedSearches, 
  saveSearch, 
  updateSavedSearch, 
  deleteSavedSearch,
  isSaving 
} = useSavedSearches();
```

### useSearchAnalytics

Get search analytics data.

```tsx
const { data: analytics } = useSearchAnalytics();
```

### useDebounce

Debounce values and functions.

```tsx
const debouncedValue = useDebounce(value, 300);
const debouncedCallback = useDebouncedCallback(callback, 300);
```

### useVirtualizedList

Virtualize large lists for performance.

```tsx
const { visibleItems, totalHeight, handleScroll, containerRef } = useVirtualizedList({
  itemCount: 1000,
  itemHeight: 100,
  containerHeight: 600,
  overscan: 5
});
```

## Service Reference

### searchService

Main search service for API interactions.

```tsx
import { searchService } from '@/features/search/services/searchService';

// Global search
const results = await searchService.globalSearch({
  q: 'react developer',
  entity_type: 'candidate',
  location: 'San Francisco',
  page: 1,
  page_size: 20
});

// Autocomplete
const suggestions = await searchService.getAutocomplete('react', 'job');

// Ranking explanation
const explanation = await searchService.getRankingExplanation('123', 'job');

// Save search
const saved = await searchService.saveSearch('My Search', queryParams);

// Get analytics
const analytics = await searchService.getSearchAnalytics();
```

## Styling

All components use Tailwind CSS and can be customized using the `className` prop.

```tsx
<GlobalSearchBar className="max-w-4xl mx-auto" />
<AdvancedSearchFilters className="w-72" />
<SearchResultCard className="hover:shadow-xl" />
```

## Performance

The search platform is optimized for performance:

- **Debounced Input**: 300ms debounce to reduce API calls
- **Virtualized Lists**: Handle 10,000+ items smoothly
- **TanStack Query Caching**: Intelligent caching with 5-minute stale time
- **Code Splitting**: Components lazy-loaded on demand
- **Image Optimization**: Lazy loading for result images

## Accessibility

The search platform is built with accessibility in mind:

- **Keyboard Navigation**: Full keyboard support (Tab, Enter, Arrow keys)
- **Screen Reader Support**: ARIA labels and live regions
- **Focus Management**: Proper focus handling
- **High Contrast**: WCAG 2.1 AA compliant
- **Semantic HTML**: Proper heading structure

## Browser Support

- Chrome/Edge: Latest 2 versions
- Firefox: Latest 2 versions
- Safari: Latest 2 versions
- Mobile browsers: iOS Safari 12+, Chrome Mobile

## Contributing

When contributing to the search platform:

1. Follow the existing component structure
2. Use TypeScript for type safety
3. Add proper accessibility attributes
4. Include loading and error states
5. Write tests for new features
6. Update documentation

## License

Internal MatchHire project.
