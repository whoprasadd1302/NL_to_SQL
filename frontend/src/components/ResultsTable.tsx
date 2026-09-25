"use client";

import React, { useState, useMemo } from "react";

export interface ResultsTableProps {
  data: Array<Record<string, any>>;
  columns?: string[];
  pageSize?: number;
  title?: string;
  onExportCsv?: () => void;
}

type SortDirection = "asc" | "desc" | null;

/**
 * Escapes CSV field values according to RFC 4180.
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
 * Downloads data as a CSV file in the browser.
 */
function downloadCsv(data: Array<Record<string, any>>, columns: string[], filename = "query_results.csv") {
  if (!data || data.length === 0) return;

  const header = columns.map(escapeCsvValue).join(",");
  const rows = data.map((row) =>
    columns.map((col) => escapeCsvValue(row[col])).join(",")
  );

  const csvContent = [header, ...rows].join("\r\n");
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);

  const link = document.createElement("a");
  link.setAttribute("href", url);
  link.setAttribute("download", filename);
  link.style.visibility = "hidden";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export function ResultsTable({
  data = [],
  columns: propColumns,
  pageSize = 50,
  title,
  onExportCsv,
}: ResultsTableProps) {
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<SortDirection>(null);
  const [currentPage, setCurrentPage] = useState<number>(1);

  // Derive columns if not provided
  const columns = useMemo(() => {
    if (propColumns && propColumns.length > 0) return propColumns;
    if (data && data.length > 0) return Object.keys(data[0]);
    return [];
  }, [propColumns, data]);

  // Sorting logic
  const handleSort = (column: string) => {
    if (sortColumn !== column) {
      setSortColumn(column);
      setSortDirection("asc");
    } else if (sortDirection === "asc") {
      setSortDirection("desc");
    } else if (sortDirection === "desc") {
      setSortColumn(null);
      setSortDirection(null);
    } else {
      setSortDirection("asc");
    }
    setCurrentPage(1);
  };

  const sortedData = useMemo(() => {
    if (!data || data.length === 0) return [];
    if (!sortColumn || !sortDirection) return data;

    return [...data].sort((a, b) => {
      const aVal = a[sortColumn];
      const bVal = b[sortColumn];

      if (aVal === bVal) return 0;
      if (aVal === null || aVal === undefined) return 1;
      if (bVal === null || bVal === undefined) return -1;

      if (typeof aVal === "number" && typeof bVal === "number") {
        return sortDirection === "asc" ? aVal - bVal : bVal - aVal;
      }

      const aStr = String(aVal).toLowerCase();
      const bStr = String(bVal).toLowerCase();
      if (aStr < bStr) return sortDirection === "asc" ? -1 : 1;
      if (aStr > bStr) return sortDirection === "asc" ? 1 : -1;
      return 0;
    });
  }, [data, sortColumn, sortDirection]);

  // Pagination logic
  const totalRows = sortedData.length;
  const totalPages = Math.max(1, Math.ceil(totalRows / pageSize));
  const safeCurrentPage = Math.min(currentPage, totalPages);

  const paginatedData = useMemo(() => {
    const startIndex = (safeCurrentPage - 1) * pageSize;
    return sortedData.slice(startIndex, startIndex + pageSize);
  }, [sortedData, safeCurrentPage, pageSize]);

  const handleExport = () => {
    if (onExportCsv) {
      onExportCsv();
    } else {
      downloadCsv(sortedData, columns);
    }
  };

  // Empty state
  if (!data || data.length === 0) {
    return (
      <div
        className="glass"
        data-testid="results-table-empty"
        style={{
          borderRadius: 12,
          padding: "32px 20px",
          textAlign: "center",
          background: "rgba(15, 23, 42, 0.7)",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          margin: "12px 0",
          color: "var(--text-muted, #94a3b8)",
        }}
      >
        <div style={{ fontSize: 28, marginBottom: 8 }}>📊</div>
        <div style={{ fontSize: 15, fontWeight: 600, color: "#e2e8f0", marginBottom: 4 }}>
          No Results Found
        </div>
        <div style={{ fontSize: 13, color: "#94a3b8" }}>
          The query returned 0 records. Try refining your question.
        </div>
      </div>
    );
  }

  const startRow = (safeCurrentPage - 1) * pageSize + 1;
  const endRow = Math.min(safeCurrentPage * pageSize, totalRows);

  return (
    <div
      className="glass"
      data-testid="results-table-container"
      style={{
        borderRadius: 12,
        overflow: "hidden",
        border: "1px solid rgba(139, 92, 246, 0.25)",
        background: "rgba(15, 23, 42, 0.8)",
        backdropFilter: "blur(12px)",
        boxShadow: "0 8px 32px rgba(0, 0, 0, 0.37)",
        margin: "12px 0",
      }}
    >
      {/* Table Header Bar */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "10px 16px",
          background: "rgba(30, 41, 59, 0.7)",
          borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
          flexWrap: "wrap",
          gap: 8,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: 14, fontWeight: 700, color: "#f8fafc" }}>
            {title || "Query Results"}
          </span>
          <span
            data-testid="row-count-badge"
            style={{
              fontSize: 11,
              fontWeight: 600,
              padding: "2px 8px",
              borderRadius: 10,
              background: "rgba(124, 58, 237, 0.2)",
              color: "#c084fc",
              border: "1px solid rgba(192, 132, 252, 0.25)",
            }}
          >
            {totalRows} {totalRows === 1 ? "row" : "rows"}
          </span>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          {/* Export CSV Button */}
          <button
            type="button"
            onClick={handleExport}
            data-testid="export-csv-button"
            style={{
              background: "rgba(255, 255, 255, 0.06)",
              border: "1px solid rgba(255, 255, 255, 0.12)",
              color: "#e2e8f0",
              fontSize: 12,
              fontWeight: 600,
              padding: "4px 10px",
              borderRadius: 6,
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: 6,
              transition: "all 0.15s ease",
            }}
          >
            <span>📥</span> Export CSV
          </button>
        </div>
      </div>

      {/* Scrollable Table Area */}
      <div style={{ overflowX: "auto", maxHeight: "460px" }}>
        <table
          data-testid="results-table"
          style={{
            width: "100%",
            borderCollapse: "collapse",
            textAlign: "left",
            fontSize: 13,
          }}
        >
          <thead>
            <tr
              style={{
                background: "rgba(15, 23, 42, 0.95)",
                borderBottom: "1px solid rgba(255, 255, 255, 0.1)",
                position: "sticky",
                top: 0,
                zIndex: 2,
              }}
            >
              {columns.map((col) => {
                const isSorted = sortColumn === col;
                return (
                  <th
                    key={col}
                    data-testid={`column-header-${col}`}
                    onClick={() => handleSort(col)}
                    style={{
                      padding: "10px 14px",
                      color: isSorted ? "#c084fc" : "#94a3b8",
                      fontWeight: 700,
                      letterSpacing: "0.3px",
                      cursor: "pointer",
                      userSelect: "none",
                      whiteSpace: "nowrap",
                      transition: "color 0.15s ease",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                      <span>{col}</span>
                      <span
                        data-testid={`sort-icon-${col}`}
                        style={{
                          fontSize: 10,
                          opacity: isSorted ? 1 : 0.4,
                          color: isSorted ? "#c084fc" : "#64748b",
                        }}
                      >
                        {isSorted ? (sortDirection === "asc" ? "▲" : "▼") : "⇅"}
                      </span>
                    </div>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {paginatedData.map((row, rowIdx) => (
              <tr
                key={rowIdx}
                data-testid={`table-row-${rowIdx}`}
                style={{
                  background: rowIdx % 2 === 0 ? "rgba(255, 255, 255, 0.015)" : "transparent",
                  borderBottom: "1px solid rgba(255, 255, 255, 0.04)",
                  transition: "background 0.15s ease",
                }}
              >
                {columns.map((col) => {
                  const val = row[col];
                  const formatted =
                    val === null || val === undefined
                      ? "-"
                      : typeof val === "object"
                      ? JSON.stringify(val)
                      : String(val);

                  return (
                    <td
                      key={col}
                      style={{
                        padding: "8px 14px",
                        color: "#e2e8f0",
                        whiteSpace: "nowrap",
                        maxWidth: 300,
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                      }}
                    >
                      {formatted}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      {totalPages > 1 && (
        <div
          data-testid="pagination-controls"
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "8px 16px",
            background: "rgba(30, 41, 59, 0.6)",
            borderTop: "1px solid rgba(255, 255, 255, 0.08)",
            fontSize: 12,
            color: "#94a3b8",
            flexWrap: "wrap",
            gap: 8,
          }}
        >
          <span data-testid="pagination-info">
            Showing {startRow}-{endRow} of {totalRows}
          </span>

          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <button
              type="button"
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={safeCurrentPage === 1}
              data-testid="prev-page-btn"
              style={{
                background: "rgba(255, 255, 255, 0.06)",
                border: "1px solid rgba(255, 255, 255, 0.12)",
                color: safeCurrentPage === 1 ? "#475569" : "#e2e8f0",
                fontSize: 11,
                padding: "4px 8px",
                borderRadius: 4,
                cursor: safeCurrentPage === 1 ? "not-allowed" : "pointer",
              }}
            >
              Previous
            </button>

            <span data-testid="page-indicator" style={{ padding: "0 4px", color: "#cbd5e1" }}>
              Page {safeCurrentPage} of {totalPages}
            </span>

            <button
              type="button"
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={safeCurrentPage === totalPages}
              data-testid="next-page-btn"
              style={{
                background: "rgba(255, 255, 255, 0.06)",
                border: "1px solid rgba(255, 255, 255, 0.12)",
                color: safeCurrentPage === totalPages ? "#475569" : "#e2e8f0",
                fontSize: 11,
                padding: "4px 8px",
                borderRadius: 4,
                cursor: safeCurrentPage === totalPages ? "not-allowed" : "pointer",
              }}
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default ResultsTable;
