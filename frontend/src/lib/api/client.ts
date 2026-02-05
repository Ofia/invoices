import axios from 'axios';
import type { AxiosInstance, InternalAxiosRequestConfig } from 'axios';

// Create axios instance with base configuration
const apiClient: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds
  withCredentials: true, // Required for CORS requests with credentials
});

/**
 * Request Interceptor
 *
 * Automatically adds JWT token to every request if it exists in localStorage
 * This means we don't have to manually add the Authorization header each time
 */
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('auth_token');

    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * Response Interceptor
 *
 * Handles common error scenarios:
 * - 401 Unauthorized: Clear token and redirect to login
 * - Network errors: Provide user-friendly messages
 */
apiClient.interceptors.response.use(
  (response) => {
    // Success response - just return the data
    return response;
  },
  (error) => {
    // Handle 401 Unauthorized - token expired or invalid
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');

      // Only redirect if not already on login page
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }

    // Network error (no response from server)
    if (!error.response) {
      error.message = 'Network error - please check your connection';
    }

    return Promise.reject(error);
  }
);

export default apiClient;
