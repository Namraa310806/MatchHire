import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import type { User } from '@/types';

export function useAuth() {
  const queryClient = useQueryClient();

  const { data: user, isLoading } = useQuery<User>({
    queryKey: ['auth', 'me'],
    queryFn: async () => {
      const response = await api.get('/auth/me/');
      return response.data;
    },
    retry: false,
  });

  const loginMutation = useMutation({
    mutationFn: async (credentials: { email: string; password: string }) => {
      const response = await api.post('/auth/login/', credentials);
      return response.data;
    },
    onSuccess: (data) => {
      localStorage.setItem('access_token', data.access);
      localStorage.setItem('refresh_token', data.refresh);
      queryClient.invalidateQueries({ queryKey: ['auth', 'me'] });
    },
  });

  const registerCandidateMutation = useMutation({
    mutationFn: async (data: {
      email: string;
      password: string;
      first_name: string;
      last_name: string;
    }) => {
      const response = await api.post('/auth/register/candidate/', data);
      return response.data;
    },
  });

  const registerRecruiterMutation = useMutation({
    mutationFn: async (data: {
      email: string;
      password: string;
      first_name: string;
      last_name: string;
      company: string;
    }) => {
      const response = await api.post('/auth/register/recruiter/', data);
      return response.data;
    },
  });

  const logoutMutation = useMutation({
    mutationFn: async () => {
      await api.post('/auth/logout/');
    },
    onSuccess: () => {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      queryClient.invalidateQueries({ queryKey: ['auth', 'me'] });
    },
  });

  const isAuthenticated = !!user;
  const isCandidate = user?.role === 'candidate';
  const isRecruiter = user?.role === 'recruiter';
  const isAdmin = user?.role === 'admin';

  return {
    user,
    isLoading,
    isAuthenticated,
    isCandidate,
    isRecruiter,
    isAdmin,
    login: loginMutation.mutateAsync,
    registerCandidate: registerCandidateMutation.mutateAsync,
    registerRecruiter: registerRecruiterMutation.mutateAsync,
    logout: logoutMutation.mutateAsync,
  };
}
