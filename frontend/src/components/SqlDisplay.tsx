"use client";

import React, { useState } from "react";

export interface SqlDisplayProps {
  sql: string;
  language?: string;
  language_name?: string;
  execution_time?: number;
  initialCollapsed?: boolean;
}

/**
 * Normalizes language string into a clean uppercase badge label.
 */
function getLanguageBadgeLabel(lang?: string, langName?: string): string {
  const target = (langName || lang || "en").toLowerCase();
  if (target.includes("hi") || target.includes("hindi") || target.includes("हिंदी")) {
    return "HI";
  }
  if (target.includes("mr") || target.includes("marathi") || target.includes("मराठी")) {
    return "MR";
  }
  if (target.includes("hinglish")) {
    return "HINGLISH";
  }
  return "EN";
}

/**
 * Highlights SQL syntax keywords, numbers, strings, and operators into formatted JSX elements.
 */
function highlightSql(sqlText: string): React.ReactNode {
  if (!sqlText) return null;

  const SQL_KEYWORDS = new Set([
    "SELECT", "FROM", "WHERE", "JOIN", "LEFT", "RIGHT", "INNER", "OUTER", "CROSS", "FULL",
    "ON", "GROUP", "BY", "ORDER", "HAVING", "LIMIT", "OFFSET", "AND", "OR", "NOT", "IN",
    "IS", "NULL", "LIKE", "ILIKE", "AS", "ASC", "DESC", "UNION", "ALL", "EXISTS",
    "CASE", "WHEN", "THEN", "ELSE", "END", "INSERT", "INTO", "VALUES", "UPDATE", "SET",
    "DELETE", "CREATE", "TABLE", "DROP", "ALTER", "DISTINCT"
  ]);

  const SQL_FUNCTIONS = new Set([
    "COUNT", "SUM", "AVG", "MIN", "MAX", "COALESCE", "ROUND", "LOWER", "UPPER", "SUBSTR",
    "LENGTH", "DATE", "STRFTIME", "CAST", "IFNULL"
  ]);

  // Regex tokenizer for SQL: strings, numbers, identifiers/words, punctuation
  const tokenRegex = /('(?:''|[^'])*'|"(?:""|[^"])*"|`(?:``|[^`])*`|\b\d+(?:\.\d+)?\b|\b[A-Za-z_][A-Za-z0-9_]*\b|--.*|\/\*[\s\S]*?\*\/|[^\s\A-Za-z0-9_])/g;

  const parts: React.ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = tokenRegex.exec(sqlText)) !== null) {
    const token = match[0];
    const index = match.index;

    // Push preceding whitespace
    if (index > lastIndex) {
      parts.push(sqlText.slice(lastIndex, index));
    }
    lastIndex = tokenRegex.lastIndex;

    const upperToken = token.toUpperCase();

    if (token.startsWith("'") || token.startsWith('"') || token.startsWith("`")) {
      // String literals
      parts.push(
        <span key={index} style={{ color: "#a5f3fc" }}>
          {token}
        </span>
      );
    } else if (/^\d+(?:\.\d+)?$/.test(token)) {
      // Numbers
      parts.push(
        <span key={index} style={{ color: "#fde047" }}>
          {token}
        </span>
      );
    } else if (SQL_KEYWORDS.has(upperToken)) {
      // SQL Keywords
      parts.push(
        <span key={index} style={{ color: "#c084fc", fontWeight: 700 }}>
          {token}
        </span>
      );
    } else if (SQL_FUNCTIONS.has(upperToken)) {
      // SQL Functions
      parts.push(
        <span key={index} style={{ color: "#38bdf8", fontWeight: 600 }}>
          {token}
        </span>
      );
    } else if (token.startsWith("--") || token.startsWith("/*")) {
      // Comments
      parts.push(
        <span key={index} style={{ color: "#64748b", fontStyle: "italic" }}>
          {token}
        </span>
      );
    } else {
      // Regular identifiers and operators
      parts.push(<span key={index}>{token}</span>);
    }
  }

  if (lastIndex < sqlText.length) {
    parts.push(sqlText.slice(lastIndex));
  }

  return parts;
}

export function SqlDisplay({
  sql,
  language,
  language_name,
  execution_time,
  initialCollapsed = false,
}: SqlDisplayProps) {
  const [isCollapsed, setIsCollapsed] = useState(initialCollapsed);
  const [copied, setCopied] = useState(false);

  const badgeLabel = getLanguageBadgeLabel(language, language_name);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(sql);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy SQL: ", err);
    }
  };

  const formattedTime =
    typeof execution_time === "number"
      ? execution_time < 1
        ? `${(execution_time * 1000).toFixed(0)}ms`
        : `${execution_time.toFixed(2)}s`
      : null;

  return (
    <div
      className="glass"
      data-testid="sql-display"
      style={{
        borderRadius: 12,
        overflow: "hidden",
        border: "1px solid rgba(139, 92, 246, 0.25)",
        background: "rgba(15, 23, 42, 0.75)",
        backdropFilter: "blur(12px)",
        boxShadow: "0 8px 32px rgba(0, 0, 0, 0.37)",
        margin: "12px 0",
        transition: "all 0.2s ease-in-out",
      }}
    >
      {/* Header bar */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "8px 14px",
          background: "rgba(30, 41, 59, 0.6)",
          borderBottom: isCollapsed ? "none" : "1px solid rgba(255, 255, 255, 0.08)",
          userSelect: "none",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          {/* Toggle collapse button */}
          <button
            type="button"
            onClick={() => setIsCollapsed(!isCollapsed)}
            style={{
              background: "none",
              border: "none",
              color: "var(--text-muted, #94a3b8)",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: 6,
              fontSize: 12,
              fontWeight: 600,
              padding: "4px 6px",
              borderRadius: 4,
              transition: "color 0.15s ease",
            }}
            aria-expanded={!isCollapsed}
            aria-label={isCollapsed ? "Expand SQL" : "Collapse SQL"}
          >
            <span
              style={{
                transform: isCollapsed ? "rotate(-90deg)" : "rotate(0deg)",
                transition: "transform 0.2s ease",
                display: "inline-block",
                fontSize: 10,
              }}
            >
              ▼
            </span>
            <span>Generated SQL</span>
          </button>

          {/* Language Badge */}
          <span
            data-testid="language-badge"
            style={{
              fontSize: 10,
              fontWeight: 700,
              letterSpacing: "0.5px",
              padding: "2px 8px",
              borderRadius: 12,
              background: "linear-gradient(135deg, rgba(124, 58, 237, 0.3) 0%, rgba(79, 70, 229, 0.3) 100%)",
              color: "#c084fc",
              border: "1px solid rgba(192, 132, 252, 0.3)",
              textTransform: "uppercase",
            }}
          >
            {badgeLabel}
          </span>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          {/* Execution Time */}
          {formattedTime && (
            <span
              data-testid="execution-time"
              style={{
                fontSize: 11,
                color: "#10b981",
                display: "flex",
                alignItems: "center",
                gap: 4,
                fontWeight: 500,
              }}
            >
              <span>⚡</span> {formattedTime}
            </span>
          )}

          {/* Copy Button */}
          <button
            type="button"
            onClick={handleCopy}
            data-testid="copy-button"
            style={{
              background: copied ? "rgba(16, 185, 129, 0.2)" : "rgba(255, 255, 255, 0.06)",
              border: copied ? "1px solid rgba(16, 185, 129, 0.4)" : "1px solid rgba(255, 255, 255, 0.12)",
              color: copied ? "#34d399" : "#cbd5e1",
              fontSize: 11,
              fontWeight: 600,
              padding: "4px 10px",
              borderRadius: 6,
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: 4,
              transition: "all 0.15s ease",
            }}
          >
            {copied ? (
              <>
                <span>✓</span> Copied!
              </>
            ) : (
              <>
                <span>📋</span> Copy
              </>
            )}
          </button>
        </div>
      </div>

      {/* Code Block Content */}
      {!isCollapsed && (
        <div
          data-testid="sql-code-container"
          style={{
            padding: "12px 16px",
            overflowX: "auto",
            fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
            fontSize: 13,
            lineHeight: 1.6,
            color: "#e2e8f0",
            backgroundColor: "rgba(15, 23, 42, 0.9)",
          }}
        >
          <pre style={{ margin: 0, whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
            <code data-testid="sql-code">{highlightSql(sql)}</code>
          </pre>
        </div>
      )}
    </div>
  );
}

export default SqlDisplay;
