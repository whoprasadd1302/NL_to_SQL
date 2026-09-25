export type Role = "user" | "assistant";

export interface SqlResult {
  success: boolean;
  columns: string[];
  rows: (string | number | null)[][];
  row_count: number;
  error?: string | null;
}

export interface Message {
  id: string;
  role: Role;
  content: string;
  timestamp: Date;
  isError?: boolean;
  isStreaming?: boolean;
  sqlResult?: SqlResult | null;
}

export interface ChatSession {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface ChatState {
  messages: Message[];
  isLoading: boolean;
  error: string | null;
}
