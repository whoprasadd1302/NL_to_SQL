"use client";

import type { Message } from "@/types/chat";

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
      <div style={{ maxWidth: "75%", display: "flex", flexDirection: "column", gap: 4 }}>
        <div
          className="glass"
          style={{
            padding: "12px 16px",
            borderRadius: "4px 18px 18px 18px",
            fontSize: 15,
            lineHeight: 1.7,
            color: message.isError ? "#f87171" : "var(--text-primary)",
            wordBreak: "break-word",
            whiteSpace: "pre-wrap",
          }}
        >
          {message.content}
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
        </div>
        <span style={{ fontSize: 11, color: "var(--text-muted)", paddingLeft: 4 }}>
          MitraAI {message.isStreaming ? "· typing…" : `· ${formatTime(message.timestamp)}`}
        </span>
      </div>
    </div>
  );
}
