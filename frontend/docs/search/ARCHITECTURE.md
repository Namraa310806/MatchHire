# Search Platform Architecture

## Overview

The MatchHire search platform is a unified, AI-powered search and recommendation system that provides exceptional search experiences for both candidates and recruiters. The architecture is designed to showcase the backend's advanced capabilities including semantic search, hybrid ranking, and AI-powered recommendations.

## Core Principles

1. **Unified Search Architecture**: Single search system shared across candidates and recruiters
2. **Explainable AI**: Every search result and recommendation includes detailed explanations
3. **Performance First**: Optimized for speed with debouncing, caching, and virtualization
4. **User-Centric**: Designed around user needs with intuitive interfaces
5. **Accessibility First**: Keyboard navigation, screen reader support, and WCAG compliance

## Architecture Layers

### 1. Data Layer

**Location**: `src/features/search/types/`

- **SearchQuery**: Core search query structure
- **SearchState**: Search state management
- **SearchResult**: Unified result format for jobs and candidates
- **RankingExplanation**: Detailed ranking breakdown
- **SearchAnalytics**: Analytics and metrics

### 2. Service Layer

**Location**: `src/features/search/services/`

**searchService.ts**:
- Global search across entities
- Entity-specific search (jobs/candidates)
- Autocomplete and suggestions
- Ranking explanations
- Saved searches management
- Search analytics
- Event tracking

### 3. State Management Layer

**Location**: `src/features/search/context/`

**SearchContext.tsx**:
- Centralized search state
- URL synchronization
- LocalStorage persistence
- Search preferences
- Recent searches management

### 4. Hooks Layer

**Location**: `src/features/search/hooks/`

**useSearch.ts**:
- `useGlobalSearch`: Main search hook with TanStack Query
- `useInfiniteSearch`: Infinite scrolling support
- `useAutocomplete`: Autocomplete suggestions
- `useRankingExplanation`: Ranking explanations
- `useSavedSearches`: Saved searches management
- `useSearchAnalytics`: Analytics data
- `usePopularSearches`: Popular search queries
- `useTrendingSearches`: Trending searches

**useDebounce.ts**:
- `useDebounce`: Debounced values
- `useDebouncedCallback`: Debounced functions

**useVirtualizedList.ts**:
- `useVirtualizedList`: Dynamic height virtualization
- `useVirtualizedListFixed`: Fixed height virtualization

### 5. Component Layer

**Location**: `src/features/search/components/`

**Core Components**:
- `GlobalSearchBar`: Universal search with autocomplete
- `AdvancedSearchFilters`: Comprehensive filter system
- `SearchResultCard`: Rich result cards with match scores
- `RankingExplanationComponent`: Detailed ranking visualization
- `RecommendationCenter`: AI recommendation hub
- `RecommendationExplainability`: Recommendation details
- `SearchHistory`: Search history management
- `SearchAnalytics`: Analytics dashboard

**UX Components**:
- `SearchLoadingStates`: Loading skeletons
- `SearchEmptyStates`: Empty and error states

### 6. Page Layer

**Location**: `src/features/search/pages/`

- `SearchPage`: Main search page with full functionality

## Data Flow

### Search Flow

```
User Input → GlobalSearchBar
    ↓
SearchContext (URL sync, state update)
    ↓
useGlobalSearch hook (debounced)
    ↓
searchService.globalSearch()
    ↓
Backend API
    ↓
SearchResult[] with ranking data
    ↓
SearchResultCard components
    ↓
User interaction (click, save, share)
```

### Recommendation Flow

```
User Profile → Backend Recommendation Engine
    ↓
recommendationService.getRecommendedCandidates()
    ↓
RecommendationCenter component
    ↓
RecommendationExplainability component
    ↓
User feedback (helpful/not relevant)
    ↓
Backend feedback loop
```

## Key Features

### 1. Global Search Architecture

- **Shared Query State**: Single source of truth for search queries
- **URL Synchronization**: Search state reflected in URL
- **Search Persistence**: Preferences and history saved to localStorage
- **Keyboard Shortcuts**: Cmd/Ctrl+K for quick search access
- **Search Preferences**: Customizable default settings

### 2. Universal Search Bar

- **Autocomplete**: Real-time suggestions as you type
- **Recent Searches**: Quick access to recent queries
- **Popular Searches**: Trending search terms
- **Keyboard Navigation**: Full keyboard support
- **Debounced Input**: Optimized API calls

### 3. Advanced Search

- **Boolean Filters**: AND/OR logic for filters
- **Facets**: Multi-dimensional filtering
- **Range Filters**: Salary, experience ranges
- **Date Filters**: Recency filtering
- **Skill Filters**: Skill-based matching
- **Location Filters**: Geographic filtering
- **Company Filters**: Company-specific search
- **Sorting**: Multiple sort options

### 4. Rich Search Results

- **Match Scores**: AI-powered match percentages
- **Highlighted Keywords**: Visual emphasis on matches
- **Recommendation Badges**: AI-recommended items
- **Quick Actions**: Save, share, quick apply
- **Related Items**: Similar results

### 5. Hybrid Ranking Visualization

- **Overall Match Score**: Aggregate score
- **Semantic Score**: AI semantic matching
- **Keyword Score**: Exact keyword matching
- **Recency Score**: Freshness factor
- **Popularity Score**: Engagement metrics
- **Ranking Explanation**: Why this result ranked higher
- **Confidence Indicator**: Score reliability

### 6. Recommendation Center

- **Recommended Jobs/Candidates**: AI-powered suggestions
- **Related Items**: Similar recommendations
- **Trending Items**: Popular content
- **Recently Viewed**: Quick access to viewed items
- **Feedback Actions**: Helpful/not relevant feedback

### 7. Recommendation Explainability

- **Why Recommended**: Clear explanation
- **Matching Skills**: Skill overlap visualization
- **Matching Experience**: Experience alignment
- **Missing Skills**: Improvement opportunities
- **Resume Similarity**: Document matching
- **Job Similarity**: Position alignment
- **Confidence Level**: Recommendation reliability

### 8. Search History

- **Recent Searches**: Last 10 searches
- **Saved Searches**: Named saved queries
- **Pinned Searches**: Important searches
- **Search Statistics**: Usage metrics
- **Quick Reuse**: One-click search execution

### 9. Saved Searches

- **Create**: Save current search
- **Rename**: Update search names
- **Duplicate**: Copy searches
- **Delete**: Remove searches
- **Share**: Share with team
- **Favorite**: Mark as favorite

### 10. Search Analytics

- **Popular Searches**: Most used queries
- **Filter Usage**: Filter statistics
- **Recommendation Acceptance**: Feedback metrics
- **Search Performance**: Response times
- **Success Rate**: Result return rate
- **Most Viewed**: Popular results

### 11. Performance Optimizations

- **Debounced Requests**: 300ms debounce delay
- **Query Cancellation**: Cancel pending requests
- **Infinite Scrolling**: Virtual pagination
- **Virtualized Lists**: Render only visible items
- **TanStack Query Cache**: Intelligent caching
- **Background Refetch**: Keep data fresh
- **Prefetching**: Anticipatory data loading

### 12. User Experience

- **Loading Skeletons**: Visual feedback during loading
- **Animated Transitions**: Smooth state changes
- **Empty States**: Helpful empty states
- **Error Recovery**: Graceful error handling
- **No-result Suggestions**: Alternative search suggestions
- **Responsive Design**: Mobile-first approach
- **Accessibility**: WCAG 2.1 AA compliance
- **Keyboard Navigation**: Full keyboard support

## Backend Integration

### API Endpoints

**Search Endpoints**:
- `GET /search/global/` - Global search
- `GET /search/jobs/` - Job search
- `GET /search/candidates/` - Candidate search
- `GET /search/autocomplete/` - Autocomplete
- `GET /search/ranking/{type}/{id}/` - Ranking explanation

**Saved Searches**:
- `POST /search/saved/` - Save search
- `GET /search/saved/` - Get saved searches
- `PATCH /search/saved/{id}/` - Update saved search
- `DELETE /search/saved/{id}/` - Delete saved search
- `POST /search/saved/{id}/run/` - Run saved search

**Analytics**:
- `GET /search/analytics/` - Get analytics
- `POST /search/analytics/events/` - Track events
- `POST /search/analytics/clicks/` - Track clicks
- `GET /search/popular/` - Popular searches
- `GET /search/trending/` - Trending searches

**Recommendations**:
- `GET /recruiter/candidates/` - Matching candidates
- `GET /recruiter/recommendations/` - Recommended candidates
- `GET /candidates/{id}/similar/` - Similar candidates
- `POST /recommendations/{id}/feedback/` - Feedback

## Caching Strategy

### TanStack Query Configuration

- **staleTime**: 5 minutes for search results
- **cacheTime**: 10 minutes for analytics
- **refetchOnWindowFocus**: Disabled for search
- **refetchOnReconnect**: Enabled
- **retry**: 3 times with exponential backoff

### LocalStorage Caching

- **search_preferences**: User preferences
- **recent_searches**: Last 10 searches
- **saved_searches**: Saved search metadata

## Performance Metrics

### Target Performance

- **Search Response**: < 500ms
- **Autocomplete**: < 200ms
- **Page Load**: < 2s
- **Time to Interactive**: < 3s

### Optimization Techniques

1. **Debouncing**: Reduce API calls by 70%
2. **Virtualization**: Handle 10,000+ items smoothly
3. **Caching**: 80% cache hit rate
4. **Code Splitting**: Lazy load components
5. **Image Optimization**: Lazy load images
6. **Bundle Size**: < 200KB gzipped

## Accessibility

### Keyboard Navigation

- `Cmd/Ctrl+K`: Open search
- `Escape`: Close search
- `Tab`: Navigate between results
- `Enter`: Select result
- `Arrow Keys`: Navigate suggestions

### Screen Reader Support

- ARIA labels on all interactive elements
- Live regions for dynamic content
- Semantic HTML structure
- Focus management

### Visual Accessibility

- High contrast mode support
- Scalable text
- Color-blind friendly palettes
- Clear visual hierarchy

## Security Considerations

- **XSS Prevention**: React's built-in escaping
- **CSRF Protection**: Token-based authentication
- **Rate Limiting**: API rate limits
- **Input Validation**: Zod schema validation
- **Secure Storage**: Sensitive data in httpOnly cookies

## Future Enhancements

1. **Voice Search**: Speech-to-text integration
2. **Image Search**: Visual search capabilities
3. **Natural Language**: NLP query understanding
4. **Collaborative Search**: Team search features
5. **Search Alerts**: Email notifications for saved searches
6. **Advanced Analytics**: More detailed metrics
7. **A/B Testing**: Search algorithm optimization
8. **ML Pipeline**: Continuous learning from feedback
