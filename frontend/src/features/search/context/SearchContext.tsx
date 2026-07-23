import React, { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  SearchQuery,
  SearchState,
  SearchEntityType,
  SearchSortOption,
  SearchFilters,
  SearchPreferences,
  RecentSearch,
} from '../types';

interface SearchContextType {
  query: SearchQuery;
  state: SearchState;
  preferences: SearchPreferences;
  recentSearches: RecentSearch[];
  setQuery: (query: Partial<SearchQuery>) => void;
  setFilters: (filters: Partial<SearchFilters>) => void;
  setSort: (sort: SearchSortOption) => void;
  setPage: (page: number) => void;
  setEntityType: (type: SearchEntityType) => void;
  performSearch: () => void;
  clearSearch: () => void;
  updatePreferences: (prefs: Partial<SearchPreferences>) => void;
  addToRecentSearches: (search: RecentSearch) => void;
  clearRecentSearches: () => void;
  setState: React.Dispatch<React.SetStateAction<SearchState>>;
}

const SearchContext = createContext<SearchContextType | undefined>(undefined);

const DEFAULT_QUERY: SearchQuery = {
  q: '',
  entity_type: 'all',
  filters: {},
  sort: 'relevance',
  page: 1,
  page_size: 20,
};

const DEFAULT_STATE: SearchState = {
  query: DEFAULT_QUERY,
  isSearching: false,
  results: [],
  total: 0,
  hasMore: true,
  error: null,
};

const DEFAULT_PREFERENCES: SearchPreferences = {
  default_entity_type: 'all',
  default_sort: 'relevance',
  results_per_page: 20,
  auto_search: true,
  show_ranking_explanations: true,
  keyboard_shortcuts_enabled: true,
};

interface SearchProviderProps {
  children: ReactNode;
}

export const SearchProvider: React.FC<SearchProviderProps> = ({ children }) => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [query, setQueryState] = useState<SearchQuery>(() => {
    // Initialize from URL params
    const urlQuery = searchParams.get('q') || '';
    const entityType = (searchParams.get('type') as SearchEntityType) || 'all';
    const sort = (searchParams.get('sort') as SearchSortOption) || 'relevance';
    const page = parseInt(searchParams.get('page') || '1', 10);
    
    return {
      q: urlQuery,
      entity_type: entityType,
      filters: {},
      sort,
      page,
      page_size: 20,
    };
  });
  const [state, setState] = useState<SearchState>(DEFAULT_STATE);
  const [preferences, setPreferences] = useState<SearchPreferences>(DEFAULT_PREFERENCES);
  const [recentSearches, setRecentSearchesState] = useState<RecentSearch[]>([]);

  // Load preferences from localStorage
  useEffect(() => {
    const savedPrefs = localStorage.getItem('search_preferences');
    if (savedPrefs) {
      try {
        setPreferences(JSON.parse(savedPrefs));
      } catch (e) {
        console.error('Failed to load search preferences:', e);
      }
    }
  }, []);

  // Load recent searches from localStorage
  useEffect(() => {
    const savedRecent = localStorage.getItem('recent_searches');
    if (savedRecent) {
      try {
        setRecentSearchesState(JSON.parse(savedRecent));
      } catch (e) {
        console.error('Failed to load recent searches:', e);
      }
    }
  }, []);

  // Sync query to URL
  useEffect(() => {
    const params: Record<string, string> = {};
    
    if (query.q) params.q = query.q;
    if (query.entity_type !== 'all') params.type = query.entity_type;
    if (query.sort !== 'relevance') params.sort = query.sort;
    if (query.page > 1) params.page = query.page.toString();
    
    Object.entries(query.filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        if (Array.isArray(value)) {
          params[key] = value.join(',');
        } else {
          params[key] = String(value);
        }
      }
    });
    
    setSearchParams(params, { replace: true });
  }, [query, setSearchParams]);

  // Save preferences to localStorage
  const updatePreferences = useCallback((prefs: Partial<SearchPreferences>) => {
    const newPrefs = { ...preferences, ...prefs };
    setPreferences(newPrefs);
    localStorage.setItem('search_preferences', JSON.stringify(newPrefs));
  }, [preferences]);

  const setQuery = useCallback((updates: Partial<SearchQuery>) => {
    setQueryState(prev => ({ ...prev, ...updates }));
  }, []);

  const setFilters = useCallback((filters: Partial<SearchFilters>) => {
    setQueryState(prev => ({
      ...prev,
      filters: { ...prev.filters, ...filters },
      page: 1, // Reset to page 1 when filters change
    }));
  }, []);

  const setSort = useCallback((sort: SearchSortOption) => {
    setQueryState(prev => ({ ...prev, sort }));
  }, []);

  const setPage = useCallback((page: number) => {
    setQueryState(prev => ({ ...prev, page }));
  }, []);

  const setEntityType = useCallback((type: SearchEntityType) => {
    setQueryState(prev => ({ ...prev, entity_type: type, page: 1 }));
  }, []);

  const performSearch = useCallback(() => {
    setState(prev => ({ ...prev, isSearching: true, error: null }));
    // This will be handled by the search hook
  }, []);

  const clearSearch = useCallback(() => {
    setQueryState(DEFAULT_QUERY);
    setState(DEFAULT_STATE);
  }, []);

  const addToRecentSearches = useCallback((search: RecentSearch) => {
    setRecentSearchesState(prev => {
      const filtered = prev.filter(s => s.query !== search.query);
      const updated = [search, ...filtered].slice(0, 10); // Keep last 10
      localStorage.setItem('recent_searches', JSON.stringify(updated));
      return updated;
    });
  }, []);

  const clearRecentSearches = useCallback(() => {
    setRecentSearchesState([]);
    localStorage.removeItem('recent_searches');
  }, []);

  const value: SearchContextType = {
    query,
    state,
    preferences,
    recentSearches,
    setQuery,
    setFilters,
    setSort,
    setPage,
    setEntityType,
    performSearch,
    clearSearch,
    updatePreferences,
    addToRecentSearches,
    clearRecentSearches,
    setState,
  };

  return <SearchContext.Provider value={value}>{children}</SearchContext.Provider>;
};

export const useSearch = (): SearchContextType => {
  const context = useContext(SearchContext);
  if (context === undefined) {
    throw new Error('useSearch must be used within a SearchProvider');
  }
  return context;
};
