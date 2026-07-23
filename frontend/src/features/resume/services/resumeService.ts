import api from '@/lib/api';

export interface Resume {
  id: string;
  file_name: string;
  uploaded_at: string;
  is_active: boolean;
  file_size?: number;
  file_type?: string;
  parsed_data?: any;
  structured_data?: any;
}

export interface ResumeVersion {
  id: string;
  resume: string;
  version_number: number;
  uploaded_at: string;
  file_name: string;
  is_active: boolean;
  parsed_data?: any;
  structured_data?: any;
}

export interface ParsedResumeData {
  contact_info?: {
    email?: string;
    phone?: string;
    location?: string;
    linkedin?: string;
    github?: string;
  };
  skills?: string[];
  experience?: Array<{
    company: string;
    position: string;
    duration?: string;
    description?: string;
  }>;
  education?: Array<{
    institution: string;
    degree: string;
    field_of_study?: string;
    graduation_date?: string;
  }>;
  certifications?: Array<{
    name: string;
    issuer?: string;
    date?: string;
  }>;
}

export const resumeService = {
  // Upload resume
  uploadResume: async (file: File): Promise<Resume> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post('/resumes/upload/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Get all resumes
  getResumes: async (): Promise<Resume[]> => {
    const response = await api.get('/resumes/');
    return response.data;
  },

  // Get resume details
  getResume: async (id: string): Promise<Resume> => {
    const response = await api.get(`/resumes/${id}/`);
    return response.data;
  },

  // Get active resume
  getActiveResume: async (): Promise<Resume> => {
    const response = await api.get('/resumes/active/');
    return response.data;
  },

  // Activate resume
  activateResume: async (id: string): Promise<Resume> => {
    const response = await api.post(`/resumes/${id}/activate/`);
    return response.data;
  },

  // Parse resume
  parseResume: async (id: string): Promise<ParsedResumeData> => {
    const response = await api.post(`/resumes/${id}/parse/`);
    return response.data;
  },

  // Get parsed resume data
  getParsedResume: async (id: string): Promise<ParsedResumeData> => {
    const response = await api.get(`/resumes/${id}/parsed/`);
    return response.data;
  },

  // Get resume version history
  getVersionHistory: async (id: string): Promise<ResumeVersion[]> => {
    const response = await api.get(`/resumes/${id}/versions/`);
    return response.data;
  },

  // Get current version
  getCurrentVersion: async (id: string): Promise<ResumeVersion> => {
    const response = await api.get(`/resumes/${id}/versions/current/`);
    return response.data;
  },

  // Rollback to previous version
  rollbackVersion: async (id: string, versionId: string): Promise<Resume> => {
    const response = await api.post(`/resumes/${id}/versions/${versionId}/rollback/`);
    return response.data;
  },

  // Activate specific version
  activateVersion: async (id: string, versionId: string): Promise<Resume> => {
    const response = await api.post(`/resumes/${id}/versions/${versionId}/activate/`);
    return response.data;
  },

  // Parse specific version
  parseVersion: async (versionId: string): Promise<ParsedResumeData> => {
    const response = await api.post(`/resumes/versions/${versionId}/parse/`);
    return response.data;
  },

  // Get parsed version data
  getParsedVersion: async (versionId: string): Promise<ParsedResumeData> => {
    const response = await api.get(`/resumes/versions/${versionId}/parsed/`);
    return response.data;
  },

  // Get structured extraction from version
  getStructuredVersion: async (versionId: string): Promise<any> => {
    const response = await api.get(`/resumes/versions/${versionId}/structured/`);
    return response.data;
  },

  // Delete resume
  deleteResume: async (id: string): Promise<void> => {
    await api.delete(`/resumes/${id}/`);
  },
};
