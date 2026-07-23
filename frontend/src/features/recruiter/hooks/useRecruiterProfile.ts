import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { recruiterService, RecruiterProfileUpdate } from '../services';

export const useRecruiterProfile = () => {
  const queryClient = useQueryClient();

  const profileQuery = useQuery({
    queryKey: ['recruiter', 'profile'],
    queryFn: recruiterService.getProfile,
  });

  const updateProfileMutation = useMutation({
    mutationFn: (data: RecruiterProfileUpdate) =>
      recruiterService.updateProfile(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recruiter', 'profile'] });
    },
  });

  const uploadLogoMutation = useMutation({
    mutationFn: (file: File) => recruiterService.uploadCompanyLogo(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recruiter', 'profile'] });
    },
  });

  return {
    profile: profileQuery.data,
    isLoading: profileQuery.isLoading,
    error: profileQuery.error,
    updateProfile: updateProfileMutation.mutate,
    isUpdating: updateProfileMutation.isPending,
    uploadLogo: uploadLogoMutation.mutate,
    isUploadingLogo: uploadLogoMutation.isPending,
  };
};
