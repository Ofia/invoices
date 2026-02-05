// Type definitions matching backend models

export interface User {
  id: number;
  email: string;
  google_id: string;
  created_at: string;
}

export interface Workspace {
  id: number;
  user_id: number;
  name: string;
  created_at: string;
}

export interface Supplier {
  id: number;
  workspace_id: number;
  name: string;
  email: string;
  markup_percentage: number;
  created_at: string;
}

export interface Invoice {
  id: number;
  supplier_id: number;
  workspace_id: number;
  original_total: number;
  markup_total: number;
  pdf_url: string;
  invoice_date: string;
  created_at: string;
  supplier?: Supplier; // Included in some responses
}

export interface PendingDocument {
  id: number;
  workspace_id: number;
  pdf_url: string;
  filename: string;
  status: 'pending' | 'processed' | 'rejected';
  gmail_message_id: string | null;
  uploaded_at: string;
}

// API Request/Response types

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface CreateWorkspaceRequest {
  name?: string;
}

export interface CreateSupplierRequest {
  workspace_id: number;
  name: string;
  email: string;
  markup_percentage: number;
}

export interface UpdateSupplierRequest {
  name?: string;
  email?: string;
  markup_percentage?: number;
}

export interface UpdateWorkspaceRequest {
  name: string;
}

export interface ProcessDocumentResponse {
  message: string;
  invoice: Invoice;
}

export interface CreateManualInvoiceRequest {
  supplier_id: number;
  original_total: number;
  invoice_date: string;
}

export interface GmailSyncResponse {
  message: string;
  emails_scanned: number;
  invoices_detected: number;
  documents_created: number;
  duplicates_skipped: number;
}

export interface GmailStatusResponse {
  authorized: boolean;
  email?: string;
}

// Search types
export interface InvoiceSearchResult {
  id: number;
  supplier_name: string;
  supplier_id: number;
  original_total: number;
  markup_total: number;
  invoice_date: string;
  created_at: string;
  match_field: string;
}

export interface SupplierSearchResult {
  id: number;
  name: string;
  email: string;
  markup_percentage: number;
  match_field: string;
}

export interface DocumentSearchResult {
  id: number;
  filename: string;
  status: string;
  uploaded_at: string;
  gmail_message_id: string | null;
  match_field: string;
}

export interface SearchResponse {
  query: string;
  invoices: InvoiceSearchResult[];
  suppliers: SupplierSearchResult[];
  documents: DocumentSearchResult[];
  total_results: number;
}

// Error response type
export interface ApiError {
  detail: string;
  error_type?: string;
  missing_fields?: string[];
  suggestion?: string;
}
