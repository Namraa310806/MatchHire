import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { featureFlagsApi } from '../services/adminService';

export function useFeatureFlags() {
  return useQuery({
    queryKey: ['admin', 'feature-flags'],
    queryFn: featureFlagsApi.getFeatureFlags,
  });
}

export function useUpdateFeatureFlag() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, enabled }: { id: string; enabled: boolean }) =>
      featureFlagsApi.updateFeatureFlag(id, enabled),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'feature-flags'] });
    },
  });
}
