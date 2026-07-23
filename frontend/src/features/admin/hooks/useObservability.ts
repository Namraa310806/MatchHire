import { useQuery } from '@tanstack/react-query';
import { searchMetricsApi, recommendationMetricsApi, systemMetricsApi } from '../services/adminService';

export function useSearchMetrics() {
  return useQuery({
    queryKey: ['observability', 'search'],
    queryFn: searchMetricsApi.getSearchMetrics,
    refetchInterval: 60000, // Refresh every minute
    staleTime: 30000,
  });
}

export function useRecommendationMetrics() {
  return useQuery({
    queryKey: ['observability', 'recommendation'],
    queryFn: recommendationMetricsApi.getRecommendationMetrics,
    refetchInterval: 60000, // Refresh every minute
    staleTime: 30000,
  });
}

export function useSystemMetrics() {
  return useQuery({
    queryKey: ['observability', 'system'],
    queryFn: systemMetricsApi.getSystemMetrics,
    refetchInterval: 30000, // Refresh every 30 seconds
    staleTime: 15000,
  });
}
