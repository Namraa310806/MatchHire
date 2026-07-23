import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { resumeService } from '../services/resumeService';
import { toast } from 'sonner';

export const useResumes = () => {
  return useQuery({
    queryKey: ['resumes'],
    queryFn: resumeService.getResumes,
  });
};

export const useResume = (id: string) => {
  return useQuery({
    queryKey: ['resumes', id],
    queryFn: () => resumeService.getResume(id),
    enabled: !!id,
  });
};

export const useActiveResume = () => {
  return useQuery({
    queryKey: ['resumes', 'active'],
    queryFn: resumeService.getActiveResume,
  });
};

export const useUploadResume = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (file: File) => resumeService.uploadResume(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['resumes'] });
      queryClient.invalidateQueries({ queryKey: ['resumes', 'active'] });
      toast.success('Resume uploaded successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Failed to upload resume');
    },
  });
};

export const useActivateResume = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: string) => resumeService.activateResume(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['resumes'] });
      queryClient.invalidateQueries({ queryKey: ['resumes', 'active'] });
      toast.success('Resume activated successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Failed to activate resume');
    },
  });
};

export const useParseResume = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: string) => resumeService.parseResume(id),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['resumes', variables] });
      toast.success('Resume parsed successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Failed to parse resume');
    },
  });
};

export const useResumeVersionHistory = (id: string) => {
  return useQuery({
    queryKey: ['resumes', id, 'versions'],
    queryFn: () => resumeService.getVersionHistory(id),
    enabled: !!id,
  });
};

export const useRollbackVersion = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, versionId }: { id: string; versionId: string }) => 
      resumeService.rollbackVersion(id, versionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['resumes'] });
      queryClient.invalidateQueries({ queryKey: ['resumes', 'active'] });
      toast.success('Resume rolled back successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Failed to rollback resume');
    },
  });
};

export const useDeleteResume = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: string) => resumeService.deleteResume(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['resumes'] });
      queryClient.invalidateQueries({ queryKey: ['resumes', 'active'] });
      toast.success('Resume deleted successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.error || 'Failed to delete resume');
    },
  });
};
