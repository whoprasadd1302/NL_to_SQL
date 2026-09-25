"use client";

import React from "react";
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

  const isChatEmpty = messages.length === 0;

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
          isLoading={isLoading}
          selectedLanguage={selectedLanguage}
          onLanguageChange={setSelectedLanguage}
        />

        {/* ── Messages View Area ─────────────────────────── */}
        <div
          id="chat-messages"
          data-testid="chat-mode-view"
          style={{
            flex: 1,
            overflowY: "auto",
            overflowX: "hidden",
            padding: "20px 24px 12px",
          }}
        >
          {isChatEmpty ? (
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
              {/* Glowing Center Logo */}
              <div
                style={{
                  width: 68,
                  height: 68,
                  borderRadius: 20,
                  background: "linear-gradient(135deg, #7c3aed 0%, #6366f1 100%)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  boxShadow: "0 0 45px rgba(124, 58, 237, 0.6)",
                  fontSize: 32,
                  fontWeight: 800,
                  color: "#fff",
                  letterSpacing: "-1px",
                }}
              >
                M
              </div>

              <div style={{ maxWidth: 540 }}>
                <h1
                  style={{
                    fontSize: 32,
                    fontWeight: 700,
                    color: "#f8fafc",
                    marginBottom: 10,
                    letterSpacing: "-0.5px",
                  }}
                >
                  Hello! I&apos;m <span style={{ color: "#a855f7" }}>MitraAI</span>
                </h1>
                <p style={{ fontSize: 15, color: "#94a3b8", lineHeight: 1.6 }}>
                  Your intelligent multilingual assistant in <b>English</b>, <b>हिंदी</b>, <b>मराठी</b>,<br />
                  and <b>Hinglish</b>.
                </p>
              </div>

              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  gap: 10,
                  marginTop: 8,
                  maxWidth: 620,
                }}
              >
                {/* Row 1 */}
                <div style={{ display: "flex", gap: 10, flexWrap: "wrap", justifyContent: "center" }}>
                  <button
                    onClick={() => sendMessage("What can you help me with?")}
                    className="glass glass-hover"
                    style={{
                      padding: "9px 18px",
                      borderRadius: 99,
                      fontSize: 13,
                      fontWeight: 500,
                      color: "#cbd5e1",
                      background: "rgba(22, 27, 46, 0.75)",
                      border: "1px solid rgba(255, 255, 255, 0.1)",
                      cursor: "pointer",
                      transition: "all 0.2s ease",
                    }}
                  >
                    What can you help me with?
                  </button>
                  <button
                    onClick={() => sendMessage("Explain quantum computing simply")}
                    className="glass glass-hover"
                    style={{
                      padding: "9px 18px",
                      borderRadius: 99,
                      fontSize: 13,
                      fontWeight: 500,
                      color: "#cbd5e1",
                      background: "rgba(22, 27, 46, 0.75)",
                      border: "1px solid rgba(255, 255, 255, 0.1)",
                      cursor: "pointer",
                      transition: "all 0.2s ease",
                    }}
                  >
                    Explain quantum computing simply
                  </button>
                </div>

                {/* Row 2 */}
                <div style={{ display: "flex", gap: 10, flexWrap: "wrap", justifyContent: "center" }}>
                  <button
                    onClick={() => sendMessage("Write a poem about the monsoon")}
                    className="glass glass-hover"
                    style={{
                      padding: "9px 18px",
                      borderRadius: 99,
                      fontSize: 13,
                      fontWeight: 500,
                      color: "#cbd5e1",
                      background: "rgba(22, 27, 46, 0.75)",
                      border: "1px solid rgba(255, 255, 255, 0.1)",
                      cursor: "pointer",
                      transition: "all 0.2s ease",
                    }}
                  >
                    Write a poem about the monsoon
                  </button>
                  <button
                    onClick={() => sendMessage("मला Python शिकायला मदत कर")}
                    className="glass glass-hover"
                    style={{
                      padding: "9px 18px",
                      borderRadius: 99,
                      fontSize: 13,
                      fontWeight: 500,
                      color: "#cbd5e1",
                      background: "rgba(22, 27, 46, 0.75)",
                      border: "1px solid rgba(255, 255, 255, 0.1)",
                      cursor: "pointer",
                      transition: "all 0.2s ease",
                    }}
                  >
                    मला Python शिकायला मदत कर
                  </button>
                </div>

                {/* Row 3 */}
                <div style={{ display: "flex", gap: 10, flexWrap: "wrap", justifyContent: "center" }}>
                  <button
                    onClick={() => sendMessage("मुझे Machine Learning सिखाओ")}
                    className="glass glass-hover"
                    style={{
                      padding: "9px 18px",
                      borderRadius: 99,
                      fontSize: 13,
                      fontWeight: 500,
                      color: "#cbd5e1",
                      background: "rgba(22, 27, 46, 0.75)",
                      border: "1px solid rgba(255, 255, 255, 0.1)",
                      cursor: "pointer",
                      transition: "all 0.2s ease",
                    }}
                  >
                    मुझे Machine Learning सिखाओ
                  </button>
                </div>
              </div>
            </div>
          ) : (
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
        <ChatInput
          onSend={sendMessage}
          isLoading={isLoading}
          placeholder="Message MitraAI... (Enter to send, Shift+Enter for newline)"
        />
      </div>
    </div>
  );
}
