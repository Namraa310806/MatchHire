import api from '@/lib/api';
import {
  SearchQuery,
  SearchResult,
  RankingExplanation,
  SearchSuggestion,
  SavedSearch,
  SearchAnalytics,
} from '../types';

export interface GlobalSearchParams {
  q?: string;
  entity_type?: 'job' | 'candidate' | 'all';
  location?: string;
  skills?: string[];
  experience_min?: number;
  experience_max?: number;
  salary_min?: number;
  salary_max?: number;
  employment_type?: string[];
  education_level?: string[];
  remote?: boolean;
  company?: string[];
  sort?: string;
  page?: number;
  page_size?: number;
}

export interface GlobalSearchResponse {
  results: SearchResult[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
  query_id?: string;
}

export interface RankingResponse {
  explanation: RankingExplanation;
}

export const searchService = {
  // Global search across jobs and candidates
  globalSearch: async (
    params: GlobalSearchParams
  ): Promise<GlobalSearchResponse> => {
    const response = await api.get('/search/global/', { params });
    return response.data;
  },

  // Search jobs specifically
  searchJobs: async (
    params: GlobalSearchParams
  ): Promise<GlobalSearchResponse> => {
    const response = await api.get('/search/jobs/', { params });
    return response.data;
  },

  // Search candidates specifically
  searchCandidates: async (
    params: GlobalSearchParams
  ): Promise<GlobalSearchResponse> => {
    const response = await api.get('/search/candidates/', { params });
    return response.data;
  },

  // Get autocomplete suggestions
  getAutocomplete: async (
    query: string,
    entity_type?: 'job' | 'candidate' | 'all'
  ): Promise<SearchSuggestion[]> => {
    const response = await api.get('/search/autocomplete/', {
      params: { q: query, entity_type },
    });
    return response.data;
  },

  // Get ranking explanation for a specific result
  getRankingExplanation: async (
    resultId: string,
    resultType: 'job' | 'candidate',
    queryId?: string
  ): Promise<RankingResponse> => {
    const response = await api.get(`/search/ranking/${resultType}/${resultId}/`, {
      params: queryId ? { query_id: queryId } : {},
    });
    return response.data;
  },

  // Save a search
  saveSearch: async (name: string, query: SearchQuery): Promise<SavedSearch> => {
    const response = await api.post('/search/saved/', {
      name,
      query_params: query,
    });
    return response.data;
  },

  // Get saved searches
  getSavedSearches: async (): Promise<SavedSearch[]> => {
    const response = await api.get('/search/saved/');
    return response.data;
  },

  // Update saved search
  updateSavedSearch: async (
    id: string,
    updates: Partial<SavedSearch>
  ): Promise<SavedSearch> => {
    const response = await api.patch(`/search/saved/${id}/`, updates);
    return response.data;
  },

  // Delete saved search
  deleteSavedSearch: async (id: string): Promise<void> => {
    await api.delete(`/search/saved/${id}/`);
  },

  // Run saved search
  runSavedSearch: async (id: string): Promise<GlobalSearchResponse> => {
    const response = await api.post(`/search/saved/${id}/run/`);
    return response.data;
  },

  // Get search analytics
  getSearchAnalytics: async (): Promise<SearchAnalytics> => {
    const response = await api.get('/search/analytics/');
    return response.data;
  },

  // Track search event
  trackSearchEvent: async (event: {
    query: string;
    result_count: number;
    filters_used: string[];
    response_time: number;
  }): Promise<void> => {
    await api.post('/search/analytics/events/', event);
  },

  // Track result click
  trackResultClick: async (data: {
    result_id: string;
    result_type: string;
    position: number;
    query_id?: string;
  }): Promise<void> => {
    await api.post('/search/analytics/clicks/', data);
  },

  // Get popular searches
  getPopularSearches: async (limit: number = 10): Promise<string[]> => {
    const response = await api.get('/search/popular/', { params: { limit } });
    return response.data;
  },

  // Get trending searches
  getTrendingSearches: async (limit: number = 10): Promise<string[]> => {
    const response = await api.get('/search/trending/', { params: { limit } });
    return response.data;
  },
};
