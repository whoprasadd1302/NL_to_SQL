"use client";

import React, { useState } from "react";
import { useChat } from "@/hooks/useChat";
import { useSqlEngine } from "@/hooks/useSqlEngine";
import { Sidebar } from "@/components/Sidebar";
import { Header } from "@/components/Header";
import { ChatMessage } from "@/components/ChatMessage";
import { TypingIndicator } from "@/components/TypingIndicator";
import { ChatInput } from "@/components/ChatInput";
import { SqlDisplay } from "@/components/SqlDisplay";
import { ResultsTable } from "@/components/ResultsTable";
import { ResultChart } from "@/components/ResultChart";

const WELCOME_SUGGESTIONS_CHAT = [
  "What can you help me with?",
  "Explain quantum computing simply",
  "Write a poem about the monsoon",
  "मला Python शिकायला मदत कर",
  "मुझे Machine Learning सिखाओ",
];

const WELCOME_SUGGESTIONS_SQL = [
  "Mumbai ke customers dikhao",
  "What is the total balance of all savings accounts?",
  "सर्व Savings खात्यांची एकूण शिल्लक किती आहे?",
  "List customers with active loans",
  "Top 5 accounts with highest balance",
];

export default function Home() {
  const [mode, setMode] = useState<"chat" | "sql">("chat");

  // Chat Hook
  const {
    sessions,
    activeSessionId,
    selectedLanguage,
    setSelectedLanguage,
    messages,
    isLoading: isChatLoading,
    sendMessage,
    createNewSession,
    selectSession,
    deleteSession,
    renameSession,
    messagesEndRef,
  } = useChat();

  // SQL Engine Hook
  const sqlEngine = useSqlEngine();

  const handleSend = async (queryText: string) => {
    if (mode === "chat") {
      sendMessage(queryText);
    } else {
      await sqlEngine.executeSql(queryText, selectedLanguage, undefined, activeSessionId);
    }
  };

  const isCurrentLoading = mode === "chat" ? isChatLoading : sqlEngine.isLoading;
  const isChatEmpty = messages.length === 0;
  const isSqlEmpty = !sqlEngine.sql && !sqlEngine.isLoading && sqlEngine.results.length === 0 && !sqlEngine.error;

  return (
    <div
      style={{
        display: "flex",
        height: "100vh",
        width: "100vw",
        overflow: "hidden",
        background: "var(--bg-primary)",
      }}
    >
      {/* ── Sidebar ─────────────────────────────────────── */}
      <Sidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onNewChat={createNewSession}
        onSelectSession={selectSession}
        onDeleteSession={deleteSession}
        onRenameSession={renameSession}
      />

      {/* ── Main Workspace Area ─────────────────────────── */}
      <div
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
          background: "var(--bg-primary)",
        }}
      >
        {/* Top Header Bar */}
        <Header
          isLoading={isCurrentLoading}
          selectedLanguage={selectedLanguage}
          onLanguageChange={setSelectedLanguage}
        />

        {/* Mode Switcher Pill Banner */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "8px 24px",
            background: "rgba(15, 23, 42, 0.6)",
            borderBottom: "1px solid rgba(255, 255, 255, 0.06)",
          }}
        >
          {/* Mode Switcher Buttons */}
          <div
            data-testid="mode-toggle-container"
            style={{
              display: "flex",
              alignItems: "center",
              background: "rgba(30, 41, 59, 0.7)",
              borderRadius: 20,
              padding: "3px",
              border: "1px solid rgba(255, 255, 255, 0.1)",
              gap: 4,
            }}
          >
            <button
              type="button"
              data-testid="mode-chat-btn"
              onClick={() => setMode("chat")}
              style={{
                padding: "5px 16px",
                borderRadius: 16,
                fontSize: 13,
                fontWeight: 600,
                border: "none",
                cursor: "pointer",
                transition: "all 0.2s ease",
                background: mode === "chat" ? "linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%)" : "transparent",
                color: mode === "chat" ? "#ffffff" : "#94a3b8",
                boxShadow: mode === "chat" ? "0 2px 10px rgba(124, 58, 237, 0.4)" : "none",
              }}
            >
              💬 Chat Mode
            </button>
            <button
              type="button"
              data-testid="mode-sql-btn"
              onClick={() => setMode("sql")}
              style={{
                padding: "5px 16px",
                borderRadius: 16,
                fontSize: 13,
                fontWeight: 600,
                border: "none",
                cursor: "pointer",
                transition: "all 0.2s ease",
                background: mode === "sql" ? "linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%)" : "transparent",
                color: mode === "sql" ? "#ffffff" : "#94a3b8",
                boxShadow: mode === "sql" ? "0 2px 10px rgba(124, 58, 237, 0.4)" : "none",
              }}
            >
              ⚡ Text-to-SQL
            </button>
          </div>

          {/* Mode Info Badge */}
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            {mode === "sql" && (
              <span
                data-testid="sql-db-badge"
                style={{
                  fontSize: 12,
                  color: "#38bdf8",
                  background: "rgba(56, 189, 248, 0.1)",
                  border: "1px solid rgba(56, 189, 248, 0.25)",
                  borderRadius: 12,
                  padding: "2px 10px",
                  fontWeight: 500,
                }}
              >
                🗄️ SQLite Banking DB (Read-Only)
              </span>
            )}
          </div>
        </div>

        {/* ── Content View Area (Chat or SQL) ──────────────── */}
        <div
          id="chat-messages"
          data-testid={mode === "chat" ? "chat-mode-view" : "sql-mode-view"}
          style={{
            flex: 1,
            overflowY: "auto",
            overflowX: "hidden",
            padding: "20px 24px 8px",
          }}
        >
          {mode === "chat" ? (
            /* ────────────────── CHAT MODE ────────────────── */
            isChatEmpty ? (
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  justifyContent: "center",
                  height: "100%",
                  padding: "0 32px",
                  gap: 24,
                  textAlign: "center",
                }}
              >
                <div
                  style={{
                    width: 72,
                    height: 72,
                    borderRadius: 20,
                    background: "linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    boxShadow: "0 0 40px rgba(124,58,237,0.5)",
                    fontSize: 32,
                    fontWeight: 800,
                    color: "#fff",
                  }}
                >
                  M
                </div>

                <div style={{ maxWidth: 480 }}>
                  <h1
                    style={{
                      fontSize: 32,
                      fontWeight: 700,
                      color: "var(--text-primary)",
                      marginBottom: 10,
                    }}
                  >
                    Hello! I&apos;m <span className="gradient-text">MitraAI</span>
                  </h1>
                  <p style={{ fontSize: 16, color: "var(--text-secondary)", lineHeight: 1.7 }}>
                    Your intelligent multilingual assistant in <b>English</b>, <b>हिंदी</b>, <b>मराठी</b>, and <b>Hinglish</b>.
                  </p>
                </div>

                <div
                  style={{
                    display: "flex",
                    flexWrap: "wrap",
                    gap: 10,
                    justifyContent: "center",
                    maxWidth: 580,
                  }}
                >
                  {WELCOME_SUGGESTIONS_CHAT.map((s) => (
                    <button
                      key={s}
                      onClick={() => handleSend(s)}
                      className="glass glass-hover"
                      style={{
                        padding: "9px 16px",
                        borderRadius: 99,
                        fontSize: 13,
                        fontWeight: 500,
                        color: "var(--text-secondary)",
                        cursor: "pointer",
                        border: "1px solid var(--border-subtle)",
                      }}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <>
                {messages.map((msg) => (
                  <ChatMessage key={msg.id} message={msg} />
                ))}
                {isChatLoading && !messages.some((m) => m.isStreaming) && <TypingIndicator />}
                <div ref={messagesEndRef} style={{ height: 8 }} />
              </>
            )
          ) : (
            /* ────────────────── SQL MODE ────────────────── */
            isSqlEmpty ? (
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  justifyContent: "center",
                  height: "100%",
                  padding: "0 32px",
                  gap: 20,
                  textAlign: "center",
                }}
              >
                <div
                  style={{
                    width: 68,
                    height: 68,
                    borderRadius: 18,
                    background: "linear-gradient(135deg, #0ea5e9 0%, #7c3aed 100%)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: 28,
                    boxShadow: "0 0 30px rgba(14, 165, 233, 0.4)",
                  }}
                >
                  ⚡
                </div>

                <div style={{ maxWidth: 520 }}>
                  <h1 style={{ fontSize: 26, fontWeight: 700, color: "#f8fafc", marginBottom: 8 }}>
                    Text-to-SQL Analytics
                  </h1>
                  <p style={{ fontSize: 14, color: "var(--text-secondary)", lineHeight: 1.6 }}>
                    Ask questions in natural language (English, Hindi, Marathi, or Hinglish) and get instant SQL queries, data summaries, interactive charts, and tables.
                  </p>
                </div>

                <div
                  style={{
                    display: "flex",
                    flexWrap: "wrap",
                    gap: 10,
                    justifyContent: "center",
                    maxWidth: 620,
                  }}
                >
                  {WELCOME_SUGGESTIONS_SQL.map((s) => (
                    <button
                      key={s}
                      onClick={() => handleSend(s)}
                      className="glass glass-hover"
                      style={{
                        padding: "8px 16px",
                        borderRadius: 99,
                        fontSize: 13,
                        fontWeight: 500,
                        color: "var(--text-secondary)",
                        cursor: "pointer",
                        border: "1px solid rgba(139, 92, 246, 0.3)",
                      }}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div
                style={{
                  maxWidth: 960,
                  margin: "0 auto",
                  display: "flex",
                  flexDirection: "column",
                  gap: 14,
                }}
              >
                {/* Error Banner */}
                {sqlEngine.error && (
                  <div
                    data-testid="sql-error-banner"
                    style={{
                      background: "rgba(239, 68, 68, 0.15)",
                      border: "1px solid rgba(239, 68, 68, 0.4)",
                      borderRadius: 10,
                      padding: "12px 16px",
                      color: "#fca5a5",
                      fontSize: 14,
                    }}
                  >
                    ⚠️ {sqlEngine.error}
                  </div>
                )}

                {/* Natural Language Summary */}
                {sqlEngine.summary && (
                  <div
                    data-testid="sql-summary-card"
                    className="glass"
                    style={{
                      padding: "14px 18px",
                      borderRadius: 10,
                      background: "linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%)",
                      border: "1px solid rgba(124, 58, 237, 0.25)",
                      color: "#f8fafc",
                      fontSize: 14,
                      lineHeight: 1.6,
                      display: "flex",
                      alignItems: "center",
                      gap: 10,
                    }}
                  >
                    <span style={{ fontSize: 18 }}>💡</span>
                    <span>{sqlEngine.summary}</span>
                  </div>
                )}

                {/* SQL Code Display */}
                {sqlEngine.sql && (
                  <SqlDisplay
                    sql={sqlEngine.sql}
                    language={sqlEngine.language}
                    language_name={sqlEngine.languageName}
                    execution_time={sqlEngine.executionTime ?? undefined}
                  />
                )}

                {/* Visualization Chart */}
                {sqlEngine.chartType && (
                  <ResultChart
                    chart_type={sqlEngine.chartType}
                    chart_data={sqlEngine.chartData}
                    title="Data Visualization"
                  />
                )}

                {/* Results Table */}
                {sqlEngine.results && sqlEngine.results.length > 0 && (
                  <ResultsTable
                    data={sqlEngine.results}
                    onExportCsv={() => sqlEngine.exportCsv()}
                  />
                )}

                {sqlEngine.isLoading && <TypingIndicator />}
              </div>
            )
          )}
        </div>

        {/* Shared Chat / SQL Input */}
        <ChatInput
          onSend={handleSend}
          isLoading={isCurrentLoading}
          placeholder={
            mode === "sql"
              ? "Ask a database question (e.g., 'Mumbai ke customers dikhao')..."
              : "Ask me anything in English, Hindi, Marathi, or Hinglish..."
          }
        />
      </div>
    </div>
  );
}
