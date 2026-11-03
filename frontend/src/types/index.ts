// ─── Auth ─────────────────────────────────────────────────────────────────────

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

// ─── Documents ────────────────────────────────────────────────────────────────

export type DocumentStatus = "pending" | "processing" | "completed" | "failed";

export interface Document {
  id: string;
  filename: string;
  original_name: string;
  file_size: number | null;
  mime_type: string | null;
  page_count: number | null;
  status: DocumentStatus;
  error_message: string | null;
  created_at: string;
  updated_at: string | null;
}

// ─── Conversations ────────────────────────────────────────────────────────────

export type MessageRole = "user" | "assistant";

export interface MessageSource {
  id: string;
  document_id: string;
  document_name: string;
  page_number: number | null;
  relevance_score: number | null;
}

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  sources: MessageSource[];
  latency_ms: number | null;
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string | null;
  document_count: number;
}

export interface ConversationDetail extends Conversation {
  messages: Message[];
}

// ─── Dashboard ────────────────────────────────────────────────────────────────

export interface DashboardStats {
  total_documents: number;
  total_conversations: number;
  total_queries: number;
  documents_by_status: Record<string, number>;
}

// ─── Pagination ───────────────────────────────────────────────────────────────

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

// ─── API Errors ───────────────────────────────────────────────────────────────

export interface ApiError {
  detail: string;
  code?: string;
}
