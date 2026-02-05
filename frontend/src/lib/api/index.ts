import apiClient from './client';
import type {
  User,
  Workspace,
  Supplier,
  Invoice,
  PendingDocument,
  CreateWorkspaceRequest,
  CreateSupplierRequest,
  UpdateSupplierRequest,
  UpdateWorkspaceRequest,
  ProcessDocumentResponse,
  CreateManualInvoiceRequest,
  GmailSyncResponse,
  GmailStatusResponse,
} from './types';

/**
 * API Module
 *
 * Centralized API methods for all backend endpoints.
 * Each function is typed and returns a Promise with the expected data.
 */

// ============================================================================
// Authentication
// ============================================================================

export const auth = {
  /**
   * Get Google OAuth URL to redirect user for login
   * Backend handles the redirect, so we just return the endpoint URL
   */
  getGoogleAuthUrl: (): string => {
    const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    return `${baseUrl}/auth/google`;
  },

  /**
   * Get current authenticated user info
   */
  getCurrentUser: async (): Promise<User> => {
    const response = await apiClient.get<User>('/auth/me');
    return response.data;
  },

  /**
   * Logout (client-side only - just removes token)
   */
  logout: () => {
    localStorage.removeItem('auth_token');
  },
};

// ============================================================================
// Workspaces
// ============================================================================

export const workspaces = {
  /**
   * Get all workspaces for current user
   */
  list: async (): Promise<Workspace[]> => {
    const response = await apiClient.get<Workspace[]>('/workspaces');
    return response.data;
  },

  /**
   * Get a specific workspace by ID
   */
  get: async (id: number): Promise<Workspace> => {
    const response = await apiClient.get<Workspace>(`/workspaces/${id}`);
    return response.data;
  },

  /**
   * Create a new workspace
   */
  create: async (data: CreateWorkspaceRequest): Promise<Workspace> => {
    const response = await apiClient.post<Workspace>('/workspaces', data);
    return response.data;
  },

  /**
   * Update workspace name
   */
  update: async (id: number, data: UpdateWorkspaceRequest): Promise<Workspace> => {
    const response = await apiClient.put<Workspace>(`/workspaces/${id}`, data);
    return response.data;
  },

  /**
   * Delete workspace (fails if workspace has data)
   */
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/workspaces/${id}`);
  },
};

// ============================================================================
// Suppliers
// ============================================================================

export const suppliers = {
  /**
   * Get all suppliers for a workspace
   */
  list: async (workspaceId: number): Promise<Supplier[]> => {
    const response = await apiClient.get<Supplier[]>('/suppliers', {
      params: { workspace_id: workspaceId },
    });
    return response.data;
  },

  /**
   * Get a specific supplier by ID
   */
  get: async (id: number): Promise<Supplier> => {
    const response = await apiClient.get<Supplier>(`/suppliers/${id}`);
    return response.data;
  },

  /**
   * Create a new supplier
   */
  create: async (data: CreateSupplierRequest): Promise<Supplier> => {
    const response = await apiClient.post<Supplier>('/suppliers', data);
    return response.data;
  },

  /**
   * Update supplier details
   */
  update: async (id: number, data: UpdateSupplierRequest): Promise<Supplier> => {
    const response = await apiClient.put<Supplier>(`/suppliers/${id}`, data);
    return response.data;
  },

  /**
   * Delete supplier (cascade deletes invoices)
   */
  delete: async (id: number): Promise<{ message: string; deleted_invoices: number }> => {
    const response = await apiClient.delete<{ message: string; deleted_invoices: number }>(
      `/suppliers/${id}`
    );
    return response.data;
  },

  /**
   * Get all invoices for a supplier (before deletion)
   */
  getInvoices: async (id: number): Promise<Invoice[]> => {
    const response = await apiClient.get<Invoice[]>(`/suppliers/${id}/invoices`);
    return response.data;
  },
};

// ============================================================================
// Documents
// ============================================================================

export const documents = {
  /**
   * Get all documents for a workspace
   */
  list: async (workspaceId: number): Promise<PendingDocument[]> => {
    const response = await apiClient.get<PendingDocument[]>('/documents', {
      params: { workspace_id: workspaceId },
    });
    return response.data;
  },

  /**
   * Upload a new document (PDF, image, etc.)
   */
  upload: async (workspaceId: number, file: File): Promise<PendingDocument> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('workspace_id', workspaceId.toString());

    const response = await apiClient.post<PendingDocument>('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  /**
   * Process a pending document with AI extraction
   */
  process: async (id: number): Promise<ProcessDocumentResponse> => {
    const response = await apiClient.post<ProcessDocumentResponse>(`/documents/${id}/process`);
    return response.data;
  },

  /**
   * Create invoice manually (when AI extraction fails)
   */
  createManualInvoice: async (
    id: number,
    data: CreateManualInvoiceRequest
  ): Promise<ProcessDocumentResponse> => {
    const response = await apiClient.post<ProcessDocumentResponse>(
      `/documents/${id}/create-invoice-manual`,
      data
    );
    return response.data;
  },

  /**
   * Reject a pending document
   */
  reject: async (id: number): Promise<{ message: string }> => {
    const response = await apiClient.post<{ message: string }>(`/documents/${id}/reject`);
    return response.data;
  },
};

// ============================================================================
// Invoices
// ============================================================================

export const invoices = {
  /**
   * Get all invoices for a workspace
   * @param sort - "asc" for A-Z (oldest first), "desc" for Z-A (newest first)
   */
  list: async (
    workspaceId: number,
    sort: 'asc' | 'desc' = 'desc'
  ): Promise<Invoice[]> => {
    const response = await apiClient.get<Invoice[]>('/invoices', {
      params: { workspace_id: workspaceId, sort },
    });
    return response.data;
  },

  /**
   * Get a specific invoice by ID
   */
  get: async (id: number): Promise<Invoice> => {
    const response = await apiClient.get<Invoice>(`/invoices/${id}`);
    return response.data;
  },

  /**
   * Download invoice PDF
   * Returns a blob URL that can be used in an <a> tag or opened in new tab
   */
  downloadPdf: async (id: number): Promise<string> => {
    const response = await apiClient.get(`/invoices/${id}/download`, {
      responseType: 'blob',
    });

    // Create a blob URL for the PDF
    const blob = new Blob([response.data], { type: 'application/pdf' });
    return URL.createObjectURL(blob);
  },
};

// ============================================================================
// Gmail Integration
// ============================================================================

export const gmail = {
  /**
   * Sync Gmail inbox for invoices
   */
  sync: async (workspaceId: number, daysBack: number = 7): Promise<GmailSyncResponse> => {
    const response = await apiClient.post<GmailSyncResponse>('/gmail/sync', null, {
      params: { workspace_id: workspaceId, days_back: daysBack },
    });
    return response.data;
  },

  /**
   * Check Gmail authorization status
   */
  getStatus: async (): Promise<GmailStatusResponse> => {
    const response = await apiClient.get<GmailStatusResponse>('/gmail/status');
    return response.data;
  },
};

// Export all as a single object (alternative usage pattern)
const api = {
  auth,
  workspaces,
  suppliers,
  documents,
  invoices,
  gmail,
};

export default api;
