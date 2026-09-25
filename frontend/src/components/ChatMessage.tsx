"use client";

import { useState } from "react";
import type { Message, SqlResult } from "@/types/chat";

interface ChatMessageProps {
  message: Message;
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function MitraAvatar() {
  return (
    <div
      style={{
        width: 34,
        height: 34,
        borderRadius: "50%",
        background: "linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexShrink: 0,
        fontSize: 14,
        fontWeight: 700,
        color: "#fff",
        boxShadow: "0 0 12px rgba(124,58,237,0.4)",
        letterSpacing: "-0.5px",
      }}
    >
      M
    </div>
  );
}

/** Minimal markdown renderer – handles code blocks, inline code, bold, italic, bullet lists */
function renderMarkdown(text: string): React.ReactNode[] {
  const lines = text.split("\n");
  const result: React.ReactNode[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // ── Fenced code block ─────────────────────────────────────────────
    const codeMatch = line.match(/^```(\w*)$/);
    if (codeMatch) {
      const lang = codeMatch[1] || "";
      const blockStart = i; // capture start index for stable key
      const codeLines: string[] = [];
      i++;
      while (i < lines.length && !lines[i].startsWith("```")) {
        codeLines.push(lines[i]);
        i++;
      }
      i++; // skip closing ```
      result.push(
        <CodeBlock key={`code-${blockStart}`} lang={lang} code={codeLines.join("\n")} />
      );
      continue;
    }

    // ── Heading (##) ──────────────────────────────────────────────────
    const h2 = line.match(/^##\s+(.*)/);
    if (h2) {
      result.push(
        <p key={i} style={{ fontWeight: 700, fontSize: 15, color: "var(--text-accent)", marginBottom: 4, marginTop: 8 }}>
          {renderInline(h2[1])}
        </p>
      );
      i++;
      continue;
    }

    const h3 = line.match(/^###\s+(.*)/);
    if (h3) {
      result.push(
        <p key={i} style={{ fontWeight: 600, fontSize: 14, color: "var(--text-accent)", marginBottom: 3, marginTop: 6 }}>
          {renderInline(h3[1])}
        </p>
      );
      i++;
      continue;
    }

    // ── Bullet list ────────────────────────────────────────────────────
    if (line.match(/^[-*•]\s+/)) {
      const items: string[] = [];
      while (i < lines.length && lines[i].match(/^[-*•]\s+/)) {
        items.push(lines[i].replace(/^[-*•]\s+/, ""));
        i++;
      }
      result.push(
        <ul key={i} style={{ paddingLeft: 20, marginBottom: 4, listStyleType: "disc" }}>
          {items.map((item, idx) => (
            <li key={idx} style={{ marginBottom: 2, color: "var(--text-primary)" }}>
              {renderInline(item)}
            </li>
          ))}
        </ul>
      );
      continue;
    }

    // ── Blank line → spacer ──────────────────────────────────────────
    if (line.trim() === "") {
      result.push(<div key={i} style={{ height: 8 }} />);
      i++;
      continue;
    }

    // ── Normal paragraph ─────────────────────────────────────────────
    result.push(
      <p key={i} style={{ marginBottom: 4, lineHeight: 1.7 }}>
        {renderInline(line)}
      </p>
    );
    i++;
  }

  return result;
}

/** Inline formatting: **bold**, *italic*, `code` */
function renderInline(text: string): React.ReactNode {
  const parts = text.split(/(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i}>{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return (
        <code
          key={i}
          style={{
            background: "rgba(124,58,237,0.18)",
            color: "#c4b5fd",
            padding: "1px 6px",
            borderRadius: 4,
            fontSize: "0.88em",
            fontFamily: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace",
          }}
        >
          {part.slice(1, -1)}
        </code>
      );
    }
    if (part.startsWith("*") && part.endsWith("*")) {
      return <em key={i}>{part.slice(1, -1)}</em>;
    }
    return part;
  });
}

/** Syntax-highlighted code block with copy button */
function CodeBlock({ lang, code }: { lang: string; code: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code).catch(() => {});
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      style={{
        margin: "10px 0",
        borderRadius: 10,
        overflow: "hidden",
        border: "1px solid rgba(124,58,237,0.25)",
        background: "#0d0f1a",
      }}
    >
      {/* Header row */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "6px 14px",
          background: "rgba(124,58,237,0.15)",
          borderBottom: "1px solid rgba(124,58,237,0.15)",
        }}
      >
        <span
          style={{
            fontSize: 11,
            fontWeight: 600,
            color: "#a78bfa",
            textTransform: "uppercase",
            letterSpacing: 1,
            fontFamily: "monospace",
          }}
        >
          {lang || "code"}
        </span>
        <button
          onClick={handleCopy}
          style={{
            fontSize: 11,
            color: copied ? "#4ade80" : "#94a3b8",
            background: "none",
            border: "none",
            cursor: "pointer",
            padding: "2px 8px",
            borderRadius: 4,
            transition: "color 0.2s",
          }}
        >
          {copied ? "✓ Copied" : "Copy"}
        </button>
      </div>
      {/* Code */}
      <pre
        style={{
          margin: 0,
          padding: "14px 16px",
          overflowX: "auto",
          fontSize: 13,
          lineHeight: 1.6,
          color: "#e2e8f0",
          fontFamily: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace",
          whiteSpace: "pre",
        }}
      >
        {code}
      </pre>
    </div>
  );
}

/** Renders a SQL query result as a styled table with 10-12 row vertical scroll and horizontal scroll for all columns */
function SqlResultTable({ result }: { result: SqlResult }) {
  const [downloading, setDownloading] = useState(false);

  if (!result.success) {
    return (
      <div
        style={{
          marginTop: 10,
          padding: "10px 14px",
          borderRadius: 8,
          background: "rgba(239,68,68,0.08)",
          border: "1px solid rgba(239,68,68,0.25)",
          color: "#f87171",
          fontSize: 13,
        }}
      >
        ⚠️ SQL Error: {result.error}
      </div>
    );
  }

  if (!result.columns || result.columns.length === 0) {
    return (
      <div style={{ marginTop: 10, fontSize: 13, color: "var(--text-muted)" }}>
        Query executed — no data returned.
      </div>
    );
  }

  const handleExportCsv = () => {
    setDownloading(true);
    try {
      const headers = result.columns.join(",");
      const csvRows = result.rows.map((row) =>
        row
          .map((val) => {
            if (val === null || val === undefined) return '""';
            const str = String(val).replace(/"/g, '""');
            return `"${str}"`;
          })
          .join(",")
      );
      const csvContent = "data:text/csv;charset=utf-8," + [headers, ...csvRows].join("\n");
      const encodedUri = encodeURI(csvContent);
      const link = document.createElement("a");
      link.setAttribute("href", encodedUri);
      link.setAttribute("download", `query_results_${Date.now()}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (e) {
      console.error("Failed to export CSV:", e);
    } finally {
      setTimeout(() => setDownloading(false), 1200);
    }
  };

  return (
    <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 8 }}>
      {/* Table control bar */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: 8,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span
            style={{
              fontSize: 11,
              fontWeight: 600,
              color: "#a78bfa",
              background: "rgba(124,58,237,0.15)",
              border: "1px solid rgba(124,58,237,0.25)",
              padding: "3px 10px",
              borderRadius: 99,
              letterSpacing: 0.5,
            }}
          >
            {result.truncated
              ? `📊 Showing ${result.fetched_count ?? result.rows.length} of ${result.row_count.toLocaleString()} rows • ${result.columns.length} columns`
              : `📊 ${result.row_count} row${result.row_count !== 1 ? "s" : ""} • ${result.columns.length} columns`}
          </span>
          {result.truncated && (
            <span style={{ fontSize: 11, color: "#f59e0b" }}>
              ⚠️ Results limited to {result.fetched_count ?? 100} rows
            </span>
          )}
          {!result.truncated && result.rows.length > 10 && (
            <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
              (scroll to view all {result.rows.length} rows)
            </span>
          )}
        </div>

        <button
          onClick={handleExportCsv}
          style={{
            fontSize: 11,
            fontWeight: 500,
            color: downloading ? "#4ade80" : "#a78bfa",
            background: "rgba(124,58,237,0.12)",
            border: "1px solid rgba(124,58,237,0.3)",
            padding: "3px 10px",
            borderRadius: 6,
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            gap: 4,
            transition: "all 0.2s ease",
          }}
          onMouseEnter={(e) => {
            (e.currentTarget as HTMLButtonElement).style.background = "rgba(124,58,237,0.25)";
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLButtonElement).style.background = "rgba(124,58,237,0.12)";
          }}
        >
          {downloading ? "✓ Exported" : "📥 Export CSV"}
        </button>
      </div>

      {/* Scrollable table container (10-12 rows height max, with sticky header and horizontal scroll) */}
      <div
        style={{
          borderRadius: 10,
          maxHeight: "390px",
          overflowY: "auto",
          overflowX: "auto",
          border: "1px solid rgba(124,58,237,0.25)",
          background: "#0c0e18",
          boxShadow: "0 4px 20px rgba(0,0,0,0.35)",
        }}
      >
        <table
          style={{
            width: "100%",
            minWidth: "max-content",
            borderCollapse: "separate",
            borderSpacing: 0,
            fontSize: 13,
            fontFamily: "'Inter', sans-serif",
          }}
        >
          <thead>
            <tr>
              <th
                style={{
                  position: "sticky",
                  top: 0,
                  zIndex: 10,
                  padding: "10px 14px",
                  textAlign: "center",
                  fontWeight: 600,
                  color: "#94a3b8",
                  fontSize: 11,
                  background: "#161828",
                  borderBottom: "2px solid rgba(124,58,237,0.35)",
                  width: 48,
                }}
              >
                #
              </th>
              {result.columns.map((col) => (
                <th
                  key={col}
                  style={{
                    position: "sticky",
                    top: 0,
                    zIndex: 10,
                    padding: "10px 16px",
                    textAlign: "left",
                    fontWeight: 600,
                    color: "#c4b5fd",
                    fontSize: 12,
                    letterSpacing: 0.5,
                    textTransform: "uppercase",
                    background: "#161828",
                    borderBottom: "2px solid rgba(124,58,237,0.35)",
                    whiteSpace: "nowrap",
                  }}
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {result.rows.map((row, ri) => (
              <tr
                key={ri}
                style={{
                  background:
                    ri % 2 === 0
                      ? "rgba(255,255,255,0.015)"
                      : "rgba(255,255,255,0.04)",
                  transition: "background 0.15s ease",
                }}
                onMouseEnter={(e) => {
                  (e.currentTarget as HTMLTableRowElement).style.background =
                    "rgba(124,58,237,0.12)";
                }}
                onMouseLeave={(e) => {
                  (e.currentTarget as HTMLTableRowElement).style.background =
                    ri % 2 === 0
                      ? "rgba(255,255,255,0.015)"
                      : "rgba(255,255,255,0.04)";
                }}
              >
                {/* Row index */}
                <td
                  style={{
                    padding: "8px 12px",
                    textAlign: "center",
                    color: "var(--text-muted)",
                    fontSize: 11,
                    borderBottom: "1px solid rgba(255,255,255,0.04)",
                    userSelect: "none",
                  }}
                >
                  {ri + 1}
                </td>
                {/* Data cells */}
                {row.map((cell, ci) => (
                  <td
                    key={ci}
                    style={{
                      padding: "8px 16px",
                      color:
                        cell === null
                          ? "var(--text-muted)"
                          : "var(--text-primary)",
                      fontStyle: cell === null ? "italic" : "normal",
                      borderBottom: "1px solid rgba(255,255,255,0.04)",
                      whiteSpace: "nowrap",
                    }}
                    title={cell === null ? "NULL" : String(cell)}
                  >
                    {cell === null ? "NULL" : String(cell)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <div
        className="animate-fade-slide-up"
        style={{
          display: "flex",
          justifyContent: "flex-end",
          marginBottom: 16,
          padding: "0 16px",
        }}
      >
        <div style={{ maxWidth: "70%", display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 4 }}>
          <div
            style={{
              background: "linear-gradient(135deg, #7c3aed 0%, #5b21b6 100%)",
              color: "#fff",
              padding: "12px 16px",
              borderRadius: "18px 18px 4px 18px",
              fontSize: 15,
              lineHeight: 1.6,
              boxShadow: "0 4px 24px rgba(124,58,237,0.3)",
              wordBreak: "break-word",
              whiteSpace: "pre-wrap",
            }}
          >
            {message.content}
          </div>
          <span style={{ fontSize: 11, color: "var(--text-muted)", paddingRight: 4 }}>
            {formatTime(message.timestamp)}
          </span>
        </div>
      </div>
    );
  }

  return (
    <div
      className="animate-fade-slide-up"
      style={{
        display: "flex",
        alignItems: "flex-start",
        gap: 10,
        marginBottom: 16,
        padding: "0 16px",
      }}
    >
      <MitraAvatar />
      <div style={{ maxWidth: "82%", display: "flex", flexDirection: "column", gap: 4 }}>
        <div
          className="glass"
          style={{
            padding: "12px 16px",
            borderRadius: "4px 18px 18px 18px",
            fontSize: 15,
            lineHeight: 1.7,
            color: message.isError ? "#f87171" : "var(--text-primary)",
            wordBreak: "break-word",
          }}
        >
          {/* Rendered markdown content */}
          {message.isError ? (
            <p>{message.content}</p>
          ) : message.content ? (
            renderMarkdown(message.content)
          ) : message.isStreaming ? (
            <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "2px 0" }}>
              <span style={{ fontSize: 13, color: "var(--text-secondary)" }}>Thinking</span>
              <div style={{ display: "flex", gap: 4 }}>
                <span style={{ width: 5, height: 5, borderRadius: "50%", background: "#a855f7", display: "inline-block", animation: "typingBlink 1.2s infinite ease-in-out" }} />
                <span style={{ width: 5, height: 5, borderRadius: "50%", background: "#a855f7", display: "inline-block", animation: "typingBlink 1.2s infinite ease-in-out 0.2s" }} />
                <span style={{ width: 5, height: 5, borderRadius: "50%", background: "#a855f7", display: "inline-block", animation: "typingBlink 1.2s infinite ease-in-out 0.4s" }} />
              </div>
            </div>
          ) : null}

          {/* Streaming cursor */}
          {message.isStreaming && message.content && (
            <span
              style={{
                display: "inline-block",
                width: 6,
                height: 14,
                marginLeft: 4,
                backgroundColor: "var(--accent-purple)",
                borderRadius: 2,
                verticalAlign: "middle",
                animation: "typingBlink 0.8s infinite ease-in-out",
              }}
            />
          )}

          {/* SQL Results Table */}
          {message.sqlResult && (
            <SqlResultTable result={message.sqlResult} />
          )}
        </div>
        <span style={{ fontSize: 11, color: "var(--text-muted)", paddingLeft: 4 }}>
          MitraAI {message.isStreaming ? "· thinking…" : `· ${formatTime(message.timestamp)}`}
        </span>
      </div>
    </div>
  );
}
