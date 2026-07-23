import api from '@/lib/api';

export interface CandidateSearchResult {
  id: string;
  email: string;
  first_name?: string;
  last_name?: string;
  candidate_profile?: {
    title?: string;
    skills?: string[];
    location?: string;
    experience_years?: number;
    resume_url?: string;
    education?: Array<{
      institution: string;
      degree: string;
      field_of_study: string;
    }>;
    experience?: Array<{
      company: string;
      position: string;
      start_date: string;
      end_date?: string;
    }>;
  };
  match_score?: number;
  match_signals?: Record<string, number>;
}

export interface CandidateSearchParams {
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
  page?: number;
  page_size?: number;
  ordering?: string;
}

export interface PaginatedCandidates {
  count: number;
  next: string | null;
  previous: string | null;
  results: CandidateSearchResult[];
}

export interface SavedSearch {
  id: string;
  name: string;
  query_params: Record<string, any>;
  created_at: string;
}

export const searchService = {
  // Search candidates
  searchCandidates: async (
    params: CandidateSearchParams
  ): Promise<PaginatedCandidates> => {
    const response = await api.get('/search/candidates/', { params });
    return response.data;
  },

  // Get candidate details
  getCandidate: async (id: string): Promise<CandidateSearchResult> => {
    const response = await api.get(`/candidates/${id}/`);
    return response.data;
  },

  // Get autocomplete suggestions
  getAutocomplete: async (query: string, field: string): Promise<string[]> => {
    const response = await api.get('/search/autocomplete/', {
      params: { q: query, field },
    });
    return response.data;
  },

  // Save search
  saveSearch: async (name: string, params: CandidateSearchParams): Promise<SavedSearch> => {
    const response = await api.post('/search/saved/', {
      name,
      query_params: params,
    });
    return response.data;
  },

  // Get saved searches
  getSavedSearches: async (): Promise<SavedSearch[]> => {
    const response = await api.get('/search/saved/');
    return response.data;
  },

  // Delete saved search
  deleteSavedSearch: async (id: string): Promise<void> => {
    await api.delete(`/search/saved/${id}/`);
  },

  // Get search history
  getSearchHistory: async (): Promise<Array<{ query: string; timestamp: string }>> => {
    const response = await api.get('/search/history/');
    return response.data;
  },

  // Clear search history
  clearSearchHistory: async (): Promise<void> => {
    await api.delete('/search/history/');
  },
};
