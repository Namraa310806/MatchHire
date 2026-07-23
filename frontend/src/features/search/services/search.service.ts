import api from '@/lib/api'

export interface SearchResult {
  type: 'job' | 'candidate' | 'company'
  id: string
  title: string
  description: string
  relevanceScore: number
  data: any
}

export interface SearchFilters {
  query: string
  type?: 'job' | 'candidate' | 'company' | 'all'
  location?: string
  skills?: string[]
  experienceLevel?: string
  salaryRange?: { min: number; max: number }
}

export const searchService = {
  search: async (filters: SearchFilters, page = 1, limit = 10): Promise<{ results: SearchResult[]; total: number }> => {
    const response = await api.get('/search', {
      params: { ...filters, page, limit }
    })
    return response.data
  },

  getSearchSuggestions: async (query: string): Promise<string[]> => {
    const response = await api.get('/search/suggestions', {
      params: { query }
    })
    return response.data
  },

  getRecentSearches: async (userId: string): Promise<string[]> => {
    const response = await api.get(`/search/recent/${userId}`)
    return response.data
  },

  saveSearch: async (userId: string, query: string, filters?: SearchFilters): Promise<void> => {
    await api.post('/search/save', { userId, query, filters })
  },

  getSavedSearches: async (userId: string): Promise<Array<{ id: string; query: string; filters: SearchFilters }>> => {
    const response = await api.get(`/search/saved/${userId}`)
    return response.data
  },

  deleteSavedSearch: async (searchId: string): Promise<void> => {
    await api.delete(`/search/saved/${searchId}`)
  },
}
