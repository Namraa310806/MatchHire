import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { searchService, CandidateSearchParams } from '../services';

export const useCandidateSearch = (params: CandidateSearchParams) => {
  return useQuery({
    queryKey: ['search', 'candidates', params],
    queryFn: () => searchService.searchCandidates(params),
    enabled: Object.keys(params).length > 0,
  });
};

export const useCandidate = (id: string) => {
  return useQuery({
    queryKey: ['candidate', id],
    queryFn: () => searchService.getCandidate(id),
    enabled: !!id,
  });
};

export const useAutocomplete = (query: string, field: string) => {
  return useQuery({
    queryKey: ['search', 'autocomplete', field, query],
    queryFn: () => searchService.getAutocomplete(query, field),
    enabled: query.length > 2,
  });
};

export const useSavedSearches = () => {
  return useQuery({
    queryKey: ['search', 'saved'],
    queryFn: searchService.getSavedSearches,
  });
};

export const useSaveSearch = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ name, params }: { name: string; params: CandidateSearchParams }) =>
      searchService.saveSearch(name, params),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['search', 'saved'] });
    },
  });
};

export const useDeleteSavedSearch = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => searchService.deleteSavedSearch(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['search', 'saved'] });
    },
  });
};

export const useSearchHistory = () => {
  return useQuery({
    queryKey: ['search', 'history'],
    queryFn: searchService.getSearchHistory,
  });
};

export const useClearSearchHistory = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: searchService.clearSearchHistory,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['search', 'history'] });
    },
  });
};
