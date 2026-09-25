"use client";

import { useChat } from "@/hooks/useChat";
import { Sidebar } from "@/components/Sidebar";
import { Header } from "@/components/Header";
import { ChatMessage } from "@/components/ChatMessage";
import { TypingIndicator } from "@/components/TypingIndicator";
import { ChatInput } from "@/components/ChatInput";

const WELCOME_SUGGESTIONS = [
  "What can you help me with?",
  "Explain quantum computing simply",
  "Write a poem about the monsoon",
  "मला Python शिकायला मदत कर",
  "मुझे Machine Learning सिखाओ",
];

export default function Home() {
  const {
    sessions,
    activeSessionId,
    selectedLanguage,
    setSelectedLanguage,
    messages,
    isLoading,
    sendMessage,
    createNewSession,
    selectSession,
    deleteSession,
    renameSession,
    messagesEndRef,
  } = useChat();

  const isEmpty = messages.length === 0;

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

      {/* ── Main Chat Area ───────────────────────────────── */}
      <div
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
          background: "var(--bg-primary)",
        }}
      >
        {/* Header with Language Dropdown */}
        <Header
          isLoading={isLoading}
          selectedLanguage={selectedLanguage}
          onLanguageChange={setSelectedLanguage}
        />

        {/* Messages / Welcome screen */}
        <div
          id="chat-messages"
          style={{
            flex: 1,
            overflowY: "auto",
            overflowX: "hidden",
            padding: "24px 0 8px",
          }}
        >
          {isEmpty ? (
            /* Welcome Screen */
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
              {/* Logo */}
              <div
                style={{
                  width: 72,
                  height: 72,
                  borderRadius: 20,
                  background: "linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  boxShadow: "0 0 40px rgba(124,58,237,0.5), 0 0 80px rgba(124,58,237,0.15)",
                  fontSize: 32,
                  fontWeight: 800,
                  color: "#fff",
                  letterSpacing: "-2px",
                  animation: "pulse-ring 2.5s ease-out infinite",
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
                    letterSpacing: "-0.5px",
                  }}
                >
                  Hello! I&apos;m{" "}
                  <span className="gradient-text">MitraAI</span>
                </h1>
                <p style={{ fontSize: 16, color: "var(--text-secondary)", lineHeight: 1.7 }}>
                  Your intelligent multilingual assistant. I understand your language and respond with clarity in <b>English</b>, <b>हिंदी</b>, <b>मराठी</b>, and <b>Hinglish</b>.
                </p>
              </div>

              {/* Suggestion chips */}
              <div
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: 10,
                  justifyContent: "center",
                  maxWidth: 580,
                }}
              >
                {WELCOME_SUGGESTIONS.map((s) => (
                  <button
                    key={s}
                    onClick={() => sendMessage(s)}
                    className="glass glass-hover"
                    style={{
                      padding: "9px 16px",
                      borderRadius: 99,
                      fontSize: 13,
                      fontWeight: 500,
                      color: "var(--text-secondary)",
                      cursor: "pointer",
                      transition: "all 0.2s ease",
                      border: "1px solid var(--border-subtle)",
                    }}
                    onMouseEnter={(e) => {
                      (e.currentTarget as HTMLButtonElement).style.color = "var(--text-accent)";
                      (e.currentTarget as HTMLButtonElement).style.borderColor = "var(--border-accent)";
                    }}
                    onMouseLeave={(e) => {
                      (e.currentTarget as HTMLButtonElement).style.color = "var(--text-secondary)";
                      (e.currentTarget as HTMLButtonElement).style.borderColor = "var(--border-subtle)";
                    }}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            /* Messages list */
            <>
              {messages.map((msg) => (
                <ChatMessage key={msg.id} message={msg} />
              ))}
              {isLoading && !messages.some((m) => m.isStreaming) && <TypingIndicator />}
              <div ref={messagesEndRef} style={{ height: 8 }} />
            </>
          )}
        </div>

        {/* Chat Input */}
        <ChatInput onSend={sendMessage} isLoading={isLoading} />
      </div>
    </div>
  );
}
