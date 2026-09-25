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
      const codeLines: string[] = [];
      i++;
      while (i < lines.length && !lines[i].startsWith("```")) {
        codeLines.push(lines[i]);
        i++;
      }
      i++; // skip closing ```
      result.push(
        <CodeBlock key={i} lang={lang} code={codeLines.join("\n")} />
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

/** Renders a SQL query result as a styled table */
function SqlResultTable({ result }: { result: SqlResult }) {
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

  return (
    <div style={{ marginTop: 12, overflowX: "auto" }}>
      {/* Row count badge */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          marginBottom: 8,
        }}
      >
        <span
          style={{
            fontSize: 11,
            fontWeight: 600,
            color: "#a78bfa",
            background: "rgba(124,58,237,0.15)",
            border: "1px solid rgba(124,58,237,0.25)",
            padding: "2px 10px",
            borderRadius: 99,
            letterSpacing: 0.5,
          }}
        >
          📊 {result.row_count} row{result.row_count !== 1 ? "s" : ""} returned
        </span>
      </div>
      <div
        style={{
          borderRadius: 10,
          overflow: "hidden",
          border: "1px solid rgba(124,58,237,0.2)",
        }}
      >
        <table
          style={{
            width: "100%",
            borderCollapse: "collapse",
            fontSize: 13,
            fontFamily: "'Inter', sans-serif",
          }}
        >
          <thead>
            <tr
              style={{
                background: "rgba(124,58,237,0.18)",
              }}
            >
              {result.columns.map((col) => (
                <th
                  key={col}
                  style={{
                    padding: "9px 14px",
                    textAlign: "left",
                    fontWeight: 600,
                    color: "#c4b5fd",
                    fontSize: 12,
                    letterSpacing: 0.5,
                    textTransform: "uppercase",
                    borderBottom: "1px solid rgba(124,58,237,0.25)",
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
                      ? "rgba(255,255,255,0.02)"
                      : "rgba(255,255,255,0.04)",
                  transition: "background 0.15s",
                }}
                onMouseEnter={(e) => {
                  (e.currentTarget as HTMLTableRowElement).style.background =
                    "rgba(124,58,237,0.08)";
                }}
                onMouseLeave={(e) => {
                  (e.currentTarget as HTMLTableRowElement).style.background =
                    ri % 2 === 0
                      ? "rgba(255,255,255,0.02)"
                      : "rgba(255,255,255,0.04)";
                }}
              >
                {row.map((cell, ci) => (
                  <td
                    key={ci}
                    style={{
                      padding: "8px 14px",
                      color:
                        cell === null
                          ? "var(--text-muted)"
                          : "var(--text-primary)",
                      fontStyle: cell === null ? "italic" : "normal",
                      borderBottom: "1px solid rgba(255,255,255,0.04)",
                      maxWidth: 280,
                      overflow: "hidden",
                      textOverflow: "ellipsis",
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
          ) : (
            renderMarkdown(message.content)
          )}

          {/* Streaming cursor */}
          {message.isStreaming && (
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
          MitraAI {message.isStreaming ? "· typing…" : `· ${formatTime(message.timestamp)}`}
        </span>
      </div>
    </div>
  );
}
