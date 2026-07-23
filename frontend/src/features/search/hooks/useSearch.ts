import { useQuery, useInfiniteQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useCallback, useEffect } from 'react';
import { useSearch as useSearchContext } from '../context/SearchContext';
import { searchService } from '../services/searchService';
import { SearchQuery, GlobalSearchParams } from '../types';

export const useGlobalSearch = () => {
  const { query, setState, addToRecentSearches } = useSearchContext();
  const queryClient = useQueryClient();

  // Convert SearchQuery to API params
  const toApiParams = useCallback((searchQuery: SearchQuery): GlobalSearchParams => {
    const params: GlobalSearchParams = {
      q: searchQuery.q || undefined,
      entity_type: searchQuery.entity_type,
      sort: searchQuery.sort,
      page: searchQuery.page,
      page_size: searchQuery.page_size,
    };

    if (searchQuery.filters.location) params.location = searchQuery.filters.location;
    if (searchQuery.filters.skills?.length) params.skills = searchQuery.filters.skills;
    if (searchQuery.filters.experience_min !== undefined) params.experience_min = searchQuery.filters.experience_min;
    if (searchQuery.filters.experience_max !== undefined) params.experience_max = searchQuery.filters.experience_max;
    if (searchQuery.filters.salary_min !== undefined) params.salary_min = searchQuery.filters.salary_min;
    if (searchQuery.filters.salary_max !== undefined) params.salary_max = searchQuery.filters.salary_max;
    if (searchQuery.filters.employment_type?.length) params.employment_type = searchQuery.filters.employment_type;
    if (searchQuery.filters.education_level?.length) params.education_level = searchQuery.filters.education_level;
    if (searchQuery.filters.remote !== undefined) params.remote = searchQuery.filters.remote;
    if (searchQuery.filters.company?.length) params.company = searchQuery.filters.company;

    return params;
  }, []);

  const searchQuery = useQuery({
    queryKey: ['search', query],
    queryFn: async () => {
      const params = toApiParams(query);
      
      if (!params.q && Object.keys(params).length <= 3) {
        return { results: [], total: 0, page: 1, page_size: 20, has_more: false };
      }

      const response = await searchService.globalSearch(params);
      
      // Add to recent searches
      if (params.q) {
        addToRecentSearches({
          query: params.q,
          entity_type: query.entity_type,
          timestamp: new Date().toISOString(),
          result_count: response.total,
        });
      }

      return response;
    },
    enabled: !!query.q || Object.keys(query.filters).length > 0,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  useEffect(() => {
    setState((prev: any) => ({
      ...prev,
      isSearching: searchQuery.isLoading,
      results: searchQuery.data?.results || [],
      total: searchQuery.data?.total || 0,
      hasMore: searchQuery.data?.has_more || false,
      error: searchQuery.error?.message || null,
    }));
  }, [searchQuery.isLoading, searchQuery.data, searchQuery.error, setState]);

  const refetch = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['search'] });
  }, [queryClient]);

  return {
    data: searchQuery.data,
    isLoading: searchQuery.isLoading,
    error: searchQuery.error,
    refetch,
  };
};

export const useInfiniteSearch = () => {
  const { query } = useSearchContext();

  const toApiParams = useCallback((searchQuery: SearchQuery): GlobalSearchParams => {
    const params: GlobalSearchParams = {
      q: searchQuery.q || undefined,
      entity_type: searchQuery.entity_type,
      sort: searchQuery.sort,
      page_size: searchQuery.page_size,
    };

    if (searchQuery.filters.location) params.location = searchQuery.filters.location;
    if (searchQuery.filters.skills?.length) params.skills = searchQuery.filters.skills;
    if (searchQuery.filters.experience_min !== undefined) params.experience_min = searchQuery.filters.experience_min;
    if (searchQuery.filters.experience_max !== undefined) params.experience_max = searchQuery.filters.experience_max;
    if (searchQuery.filters.salary_min !== undefined) params.salary_min = searchQuery.filters.salary_min;
    if (searchQuery.filters.salary_max !== undefined) params.salary_max = searchQuery.filters.salary_max;
    if (searchQuery.filters.employment_type?.length) params.employment_type = searchQuery.filters.employment_type;
    if (searchQuery.filters.education_level?.length) params.education_level = searchQuery.filters.education_level;
    if (searchQuery.filters.remote !== undefined) params.remote = searchQuery.filters.remote;
    if (searchQuery.filters.company?.length) params.company = searchQuery.filters.company;

    return params;
  }, []);

  return useInfiniteQuery({
    queryKey: ['search-infinite', query],
    queryFn: async ({ pageParam = 1 }) => {
      const params = toApiParams(query);
      params.page = pageParam;
      
      if (!params.q && Object.keys(params).length <= 3) {
        return { results: [], total: 0, page: 1, page_size: 20, has_more: false };
      }

      return await searchService.globalSearch(params);
    },
    initialPageParam: 1,
    getNextPageParam: (lastPage) => lastPage.has_more ? lastPage.page + 1 : undefined,
    enabled: !!query.q || Object.keys(query.filters).length > 0,
  });
};

export const useAutocomplete = (query: string, entityType: 'job' | 'candidate' | 'all' = 'all') => {
  return useQuery({
    queryKey: ['autocomplete', query, entityType],
    queryFn: () => searchService.getAutocomplete(query, entityType),
    enabled: query.length >= 2,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
};

export const useRankingExplanation = (resultId: string, resultType: 'job' | 'candidate', queryId?: string) => {
  return useQuery({
    queryKey: ['ranking', resultId, resultType, queryId],
    queryFn: () => searchService.getRankingExplanation(resultId, resultType, queryId),
    enabled: !!resultId,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
};

export const useSavedSearches = () => {
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ['saved-searches'],
    queryFn: () => searchService.getSavedSearches(),
    staleTime: 5 * 60 * 1000,
  });

  const saveSearchMutation = useMutation({
    mutationFn: ({ name, query }: { name: string; query: SearchQuery }) =>
      searchService.saveSearch(name, query),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['saved-searches'] });
    },
  });

  const updateSavedSearchMutation = useMutation({
    mutationFn: ({ id, updates }: { id: string; updates: any }) =>
      searchService.updateSavedSearch(id, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['saved-searches'] });
    },
  });

  const deleteSavedSearchMutation = useMutation({
    mutationFn: (id: string) => searchService.deleteSavedSearch(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['saved-searches'] });
    },
  });

  return {
    savedSearches: data || [],
    isLoading,
    error,
    saveSearch: saveSearchMutation.mutateAsync,
    updateSavedSearch: updateSavedSearchMutation.mutateAsync,
    deleteSavedSearch: deleteSavedSearchMutation.mutateAsync,
    isSaving: saveSearchMutation.isPending,
  };
};

export const useSearchAnalytics = () => {
  return useQuery({
    queryKey: ['search-analytics'],
    queryFn: () => searchService.getSearchAnalytics(),
    staleTime: 15 * 60 * 1000, // 15 minutes
  });
};

export const usePopularSearches = (limit: number = 10) => {
  return useQuery({
    queryKey: ['popular-searches', limit],
    queryFn: () => searchService.getPopularSearches(limit),
    staleTime: 30 * 60 * 1000, // 30 minutes
  });
};

export const useTrendingSearches = (limit: number = 10) => {
  return useQuery({
    queryKey: ['trending-searches', limit],
    queryFn: () => searchService.getTrendingSearches(limit),
    staleTime: 30 * 60 * 1000, // 30 minutes
  });
};
