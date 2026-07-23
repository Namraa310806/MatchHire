export type SearchEntityType = 'job' | 'candidate' | 'all';

export type SearchSortOption =
  | 'relevance'
  | 'match_score'
  | 'recent'
  | 'salary_high'
  | 'salary_low'
  | 'experience';

export type SearchFilterType =
  | 'location'
  | 'skills'
  | 'experience'
  | 'salary'
  | 'employment_type'
  | 'education_level'
  | 'remote'
  | 'company';

export interface SearchFilters {
  location?: string;
  skills?: string[];
  experience_min?: number;
  experience_max?: number;
  salary_min?: number;
  salary_max?: number;
  employment_type?: ('full_time' | 'part_time' | 'contract' | 'internship')[];
  education_level?: string[];
  remote?: boolean;
  company?: string[];
}

export interface SearchQuery {
  q: string;
  entity_type: SearchEntityType;
  filters: SearchFilters;
  sort: SearchSortOption;
  page: number;
  page_size: number;
}

export interface SearchState {
  query: SearchQuery;
  isSearching: boolean;
  results: any[];
  total: number;
  hasMore: boolean;
  error: string | null;
}

export interface SearchResult {
  id: string;
  type: SearchEntityType;
  score: number;
  semantic_score?: number;
  keyword_score?: number;
  recency_score?: number;
  popularity_score?: number;
  highlighted_fields?: Record<string, string[]>;
  data: any;
}

export interface RankingExplanation {
  overall_score: number;
  semantic_score: number;
  keyword_score: number;
  recency_score: number;
  popularity_score: number;
  factors: Array<{
    name: string;
    value: number;
    description: string;
  }>;
  confidence: 'high' | 'medium' | 'low';
}

export interface SearchSuggestion {
  type: 'query' | 'skill' | 'location' | 'company';
  value: string;
  count?: number;
}

export interface RecentSearch {
  query: string;
  entity_type: SearchEntityType;
  timestamp: string;
  result_count?: number;
}

export interface SavedSearch {
  id: string;
  name: string;
  query: SearchQuery;
  query_params?: SearchQuery;
  created_at: string;
  last_used?: string;
  is_pinned: boolean;
  notification_enabled: boolean;
}

export interface SearchPreferences {
  default_entity_type: SearchEntityType;
  default_sort: SearchSortOption;
  results_per_page: number;
  auto_search: boolean;
  show_ranking_explanations: boolean;
  keyboard_shortcuts_enabled: boolean;
}

export interface SearchAnalytics {
  total_searches: number;
  popular_queries: Array<{ query: string; count: number }>;
  filter_usage: Record<string, number>;
  average_results_per_search: number;
  zero_result_queries: string[];
  most_viewed_results: Array<{ id: string; type: string; views: number }>;
  recommendation_acceptance_rate: number;
  average_response_time: number;
}

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
