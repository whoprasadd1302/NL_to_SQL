"use client";

import { useState, useCallback } from "react";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export interface SqlExecutionResult {
  success: boolean;
  language: string;
  language_name: string;
  sql: string;
  results: Array<Record<string, any>>;
  summary: string;
  chart_type?: string | null;
  chart_data?: any;
  count?: number;
  execution_time?: number;
  error?: string;
}

export interface DbColumn {
  name: string;
  type: string;
  primary_key?: boolean;
  nullable?: boolean;
}

export interface DbForeignKey {
  from_table: string;
  from_column: string;
  to_table: string;
  to_column: string;
  relationship?: string;
}

export interface DbSchema {
  tables: string[];
  columns: Record<string, DbColumn[]>;
  foreign_keys: DbForeignKey[];
  schema_context?: string;
}

export interface UseSqlEngineState {
  isLoading: boolean;
  isStreaming: boolean;
  error: string | null;
  sql: string;
  results: Array<Record<string, any>>;
  summary: string;
  chartType: string | null;
  chartData: any;
  schema: DbSchema | null;
  executionTime: number | null;
  rowCount: number;
  language: string;
  languageName: string;
}

/**
 * Escapes CSV values according to RFC 4180.
 */
function escapeCsvValue(val: any): string {
  if (val === null || val === undefined) return "";
  const str = String(val);
  if (str.includes(",") || str.includes('"') || str.includes("\n") || str.includes("\r")) {
    return `"${str.replace(/"/g, '""')}"`;
  }
  return str;
}

/**
 * Helper to trigger client-side file download for a blob or string.
 */
function triggerBrowserDownload(content: Blob | string, filename = "query_results.csv") {
  if (typeof window === "undefined") return;

  const blob = typeof content === "string" ? new Blob([content], { type: "text/csv;charset=utf-8;" }) : content;
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.style.display = "none";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export function useSqlEngine() {
  const [state, setState] = useState<UseSqlEngineState>({
    isLoading: false,
    isStreaming: false,
    error: null,
    sql: "",
    results: [],
    summary: "",
    chartType: null,
    chartData: null,
    schema: null,
    executionTime: null,
    rowCount: 0,
    language: "en",
    languageName: "English",
  });

  const reset = useCallback(() => {
    setState((prev) => ({
      ...prev,
      isLoading: false,
      isStreaming: false,
      error: null,
      sql: "",
      results: [],
      summary: "",
      chartType: null,
      chartData: null,
      executionTime: null,
      rowCount: 0,
    }));
  }, []);

  /**
   * Introspects target database schema from backend GET /sql/schema.
   */
  const getSchema = useCallback(async (dbPath?: string): Promise<DbSchema | null> => {
    setState((prev) => ({ ...prev, isLoading: true, error: null }));
    try {
      const url = new URL(`${BACKEND_URL}/sql/schema`);
      if (dbPath) {
        url.searchParams.set("db_path", dbPath);
      }

      const res = await fetch(url.toString());
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Failed to fetch schema (${res.status})`);
      }

      const schemaData: DbSchema = await res.json();
      setState((prev) => ({
        ...prev,
        schema: schemaData,
        isLoading: false,
        error: null,
      }));
      return schemaData;
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : "Failed to load database schema";
      setState((prev) => ({ ...prev, isLoading: false, error: errMsg }));
      return null;
    }
  }, []);

  /**
   * Streams generated SQL tokens via SSE endpoint POST /sql/stream.
   */
  const generateSql = useCallback(
    async (
      query: string,
      language = "auto",
      dbPath?: string,
      sessionId = "default",
      onToken?: (token: string) => void
    ): Promise<string> => {
      const trimmedQuery = query.trim();
      if (!trimmedQuery) {
        setState((prev) => ({ ...prev, error: "Query cannot be empty" }));
        return "";
      }

      setState((prev) => ({
        ...prev,
        isLoading: true,
        isStreaming: true,
        error: null,
        sql: "",
      }));

      try {
        const response = await fetch(`${BACKEND_URL}/sql/stream`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            query: trimmedQuery,
            language,
            db_path: dbPath,
            session_id: sessionId,
          }),
        });

        if (!response.ok || !response.body) {
          const errData = await response.json().catch(() => ({}));
          throw new Error(errData.detail || `SQL stream request failed (${response.status})`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let accumulatedSql = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const data = JSON.parse(line.slice(6));
                if (data.token) {
                  accumulatedSql += data.token;
                  onToken?.(data.token);
                  setState((prev) => ({ ...prev, sql: prev.sql + data.token }));
                } else if (data.done) {
                  if (data.sql) {
                    accumulatedSql = data.sql;
                  }
                  setState((prev) => ({
                    ...prev,
                    sql: accumulatedSql,
                    isStreaming: false,
                    isLoading: false,
                  }));
                } else if (data.error) {
                  throw new Error(data.error);
                }
              } catch (parseErr) {
                // Ignore chunk parse error
              }
            }
          }
        }

        setState((prev) => ({
          ...prev,
          sql: accumulatedSql,
          isStreaming: false,
          isLoading: false,
          error: null,
        }));

        return accumulatedSql;
      } catch (err) {
        const errMsg = err instanceof Error ? err.message : "Error streaming SQL";
        setState((prev) => ({
          ...prev,
          isStreaming: false,
          isLoading: false,
          error: errMsg,
        }));
        return "";
      }
    },
    []
  );

  /**
   * Complete pipeline: generates, validates, executes SQL, and returns result payload.
   */
  const executeSql = useCallback(
    async (
      query: string,
      language = "auto",
      dbPath?: string,
      sessionId = "default"
    ): Promise<SqlExecutionResult> => {
      const trimmedQuery = query.trim();
      if (!trimmedQuery) {
        const emptyResult: SqlExecutionResult = {
          success: false,
          language: "en",
          language_name: "English",
          sql: "",
          results: [],
          summary: "Query cannot be empty",
          error: "Query cannot be empty",
        };
        setState((prev) => ({ ...prev, error: "Query cannot be empty" }));
        return emptyResult;
      }

      setState((prev) => ({
        ...prev,
        isLoading: true,
        error: null,
      }));

      try {
        const res = await fetch(`${BACKEND_URL}/sql/execute`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            query: trimmedQuery,
            language,
            db_path: dbPath,
            session_id: sessionId,
          }),
        });

        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.detail || `Execution request failed (${res.status})`);
        }

        const data: SqlExecutionResult = await res.json();

        if (!data.success) {
          setState((prev) => ({
            ...prev,
            isLoading: false,
            error: data.error || data.summary || "Execution failed",
            sql: data.sql || "",
            results: [],
            summary: data.summary || "",
            chartType: null,
            chartData: null,
            executionTime: data.execution_time ?? null,
            rowCount: 0,
            language: data.language || "en",
            languageName: data.language_name || "English",
          }));
          return data;
        }

        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: null,
          sql: data.sql,
          results: data.results || [],
          summary: data.summary,
          chartType: data.chart_type ?? null,
          chartData: data.chart_data ?? null,
          executionTime: data.execution_time ?? null,
          rowCount: data.count ?? data.results?.length ?? 0,
          language: data.language || "en",
          languageName: data.language_name || "English",
        }));

        return data;
      } catch (err) {
        const errMsg = err instanceof Error ? err.message : "Error executing SQL";
        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: errMsg,
        }));
        return {
          success: false,
          language: "en",
          language_name: "English",
          sql: "",
          results: [],
          summary: errMsg,
          error: errMsg,
        };
      }
    },
    []
  );

  /**
   * Exports result set as CSV by calling POST /sql/export or local fallback.
   */
  const exportCsv = useCallback(
    async (
      results?: Array<Record<string, any>>,
      query?: string,
      sql?: string,
      dbPath?: string
    ): Promise<void> => {
      const dataToExport = results || state.results;

      try {
        const response = await fetch(`${BACKEND_URL}/sql/export`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            data: dataToExport.length > 0 ? dataToExport : undefined,
            query,
            sql: sql || state.sql,
            db_path: dbPath,
          }),
        });

        if (response.ok) {
          const blob = await response.blob();
          triggerBrowserDownload(blob, "query_results.csv");
          return;
        }
      } catch (fetchErr) {
        console.warn("Backend CSV export failed, using client-side fallback:", fetchErr);
      }

      // Client-side fallback if backend unreachable
      if (dataToExport && dataToExport.length > 0) {
        const cols = Object.keys(dataToExport[0]);
        const header = cols.map(escapeCsvValue).join(",");
        const rows = dataToExport.map((row) =>
          cols.map((col) => escapeCsvValue(row[col])).join(",")
        );
        const csvContent = [header, ...rows].join("\r\n");
        triggerBrowserDownload(csvContent, "query_results.csv");
      }
    },
    [state.results, state.sql]
  );

  return {
    ...state,
    generateSql,
    executeSql,
    exportCsv,
    getSchema,
    reset,
  };
}

export default useSqlEngine;
