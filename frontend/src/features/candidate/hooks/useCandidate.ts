import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { candidateService, CandidateProfileUpdate } from '../services/candidateService';
import { toast } from 'sonner';

export const useCandidateProfile = () => {
  return useQuery({
    queryKey: ['candidate', 'profile'],
    queryFn: candidateService.getProfile,
  });
};

export const useCurrentUser = () => {
  return useQuery({
    queryKey: ['user', 'current'],
    queryFn: candidateService.getCurrentUser,
  });
};

export const useUpdateCandidateProfile = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: CandidateProfileUpdate) => candidateService.updateProfile(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['candidate', 'profile'] });
      toast.success('Profile updated successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Failed to update profile');
    },
  });
};

export const useUpdateUser = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: { first_name?: string; last_name?: string; email?: string }) => 
      candidateService.updateUser(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user', 'current'] });
      toast.success('Account updated successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Failed to update account');
    },
  });
};
