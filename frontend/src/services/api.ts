import axios from 'axios';
import {
  DueDiligenceRequest,
  DueDiligenceResponse,
  EntityInfo,
  ReportRequest,
  CheckStatus
} from '../types/api';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

console.log('API: Base URL configured as:', API_BASE_URL);

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding auth headers if needed
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    // const token = localStorage.getItem('auth_token');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for handling errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      // Could redirect to login page
    }
    return Promise.reject(error);
  }
);

export const dueDiligenceApi = {
  // Create new due diligence check
  createCheck: async (request: DueDiligenceRequest): Promise<DueDiligenceResponse> => {
    console.log('API: Creating due diligence check:', request);
    console.log('API: Making request to:', `${API_BASE_URL}/due-diligence`);

    try {
      const response = await api.post('/due-diligence/', request);
      console.log('API: Success response:', response.data);
      return response.data;
    } catch (error: any) {
      console.error('API: Error creating check:', error);
      console.error('API: Error response:', error.response?.data);
      console.error('API: Error status:', error.response?.status);
      throw error;
    }
  },

  // Get due diligence check by ID
  getCheck: async (checkId: string): Promise<DueDiligenceResponse> => {
    const response = await api.get(`/due-diligence/${checkId}/`);
    return response.data;
  },

  // Start processing for a check
  startProcessing: async (checkId: string): Promise<{ status: string }> => {
    const response = await api.post(`/due-diligence/${checkId}/start`);
    return response.data;
  },

  // List all due diligence checks
  listChecks: async (
    skip?: number,
    limit?: number,
    status?: CheckStatus
  ): Promise<DueDiligenceResponse[]> => {
    const params = new URLSearchParams();
    if (skip !== undefined) params.append('skip', skip.toString());
    if (limit !== undefined) params.append('limit', limit.toString());
    if (status) params.append('status', status);

    const response = await api.get(`/due-diligence/?${params.toString()}`);
    return response.data;
  },
};

export const entitiesApi = {
  // Get entity by LEI number
  getEntity: async (leiNumber: string): Promise<EntityInfo> => {
    const response = await api.get(`/entities/${leiNumber}`);
    return response.data;
  },

  // Search entities
  searchEntities: async (
    name?: string,
    entityType?: string,
    jurisdiction?: string,
    skip?: number,
    limit?: number
  ): Promise<EntityInfo[]> => {
    const params = new URLSearchParams();
    if (name) params.append('name', name);
    if (entityType) params.append('entity_type', entityType);
    if (jurisdiction) params.append('jurisdiction', jurisdiction);
    if (skip !== undefined) params.append('skip', skip.toString());
    if (limit !== undefined) params.append('limit', limit.toString());

    const response = await api.get(`/entities?${params.toString()}`);
    return response.data;
  },
};

export const reportsApi = {
  // Generate report
  generateReport: async (request: ReportRequest): Promise<Blob> => {
    const response = await api.post('/reports/generate', request, {
      responseType: 'blob',
    });
    return response.data;
  },
};

export const adminApi = {
  // Get admin logs for a due diligence check
  getAdminLogs: async (checkId: string) => {
    const response = await api.get(`/admin/logs/${checkId}`);
    return response.data;
  },
};

export default api;