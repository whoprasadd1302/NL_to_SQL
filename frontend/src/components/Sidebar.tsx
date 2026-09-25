"use client";

import { useState } from "react";
import type { ChatSession } from "@/types/chat";

interface SidebarProps {
  sessions: ChatSession[];
  activeSessionId: string;
  onNewChat: () => void;
  onSelectSession: (sessionId: string) => void;
  onDeleteSession: (sessionId: string) => void;
  onRenameSession: (sessionId: string, newTitle: string) => void;
}

const PlusIcon = () => (
  <svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5} strokeLinecap="round">
    <line x1="12" y1="5" x2="12" y2="19" />
    <line x1="5" y1="12" x2="19" y2="12" />
  </svg>
);

const ChatIcon = () => (
  <svg width={15} height={15} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
  </svg>
);

const TrashIcon = () => (
  <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
    <polyline points="3 6 5 6 21 6" />
    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
  </svg>
);

const EditIcon = () => (
  <svg width={13} height={13} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
  </svg>
);

const CpuIcon = () => (
  <svg width={13} height={13} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
    <rect x="4" y="4" width="16" height="16" rx="2" />
    <rect x="9" y="9" width="6" height="6" />
    <line x1="9" y1="1" x2="9" y2="4" /><line x1="15" y1="1" x2="15" y2="4" />
    <line x1="9" y1="20" x2="9" y2="23" /><line x1="15" y1="20" x2="15" y2="23" />
    <line x1="20" y1="9" x2="23" y2="9" /><line x1="20" y1="14" x2="23" y2="14" />
    <line x1="1" y1="9" x2="4" y2="9" /><line x1="1" y1="14" x2="4" y2="14" />
  </svg>
);

export function Sidebar({
  sessions,
  activeSessionId,
  onNewChat,
  onSelectSession,
  onDeleteSession,
  onRenameSession,
}: SidebarProps) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");

  const handleStartRename = (session: ChatSession, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingId(session.id);
    setEditTitle(session.title);
  };

  const handleSaveRename = (sessionId: string) => {
    if (editTitle.trim()) {
      onRenameSession(sessionId, editTitle.trim());
    }
    setEditingId(null);
  };

  return (
    <aside
      style={{
        width: 250,
        minWidth: 250,
        height: "100%",
        background: "rgba(10, 12, 22, 0.95)",
        borderRight: "1px solid rgba(255, 255, 255, 0.05)",
        display: "flex",
        flexDirection: "column",
        padding: "16px 12px",
        gap: 0,
      }}
    >
      {/* Branding */}
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 18, paddingLeft: 4 }}>
        <div
          style={{
            width: 38,
            height: 38,
            borderRadius: 12,
            background: "linear-gradient(135deg, #7c3aed 0%, #6366f1 100%)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 18,
            fontWeight: 800,
            color: "#fff",
            boxShadow: "0 0 20px rgba(124, 58, 237, 0.4)",
            letterSpacing: "-0.5px",
          }}
        >
          M
        </div>
        <div>
          <p style={{ fontWeight: 700, fontSize: 15, color: "#f8fafc", letterSpacing: "-0.2px" }}>
            MitraAI
          </p>
          <p style={{ fontSize: 11, color: "#64748b" }}>Multilingual Assistant</p>
        </div>
      </div>

      {/* New Chat button */}
      <button
        id="new-chat-button"
        onClick={onNewChat}
        style={{
          width: "100%",
          display: "flex",
          alignItems: "center",
          gap: 8,
          padding: "9px 14px",
          borderRadius: 12,
          background: "rgba(30, 27, 58, 0.7)",
          border: "1px solid rgba(124, 58, 237, 0.35)",
          color: "#f1f5f9",
          fontSize: 13,
          fontWeight: 600,
          transition: "all 0.2s ease",
          cursor: "pointer",
          marginBottom: 18,
        }}
        onMouseEnter={(e) => {
          (e.currentTarget as HTMLButtonElement).style.borderColor = "rgba(139, 92, 246, 0.6)";
          (e.currentTarget as HTMLButtonElement).style.background = "rgba(42, 36, 78, 0.85)";
        }}
        onMouseLeave={(e) => {
          (e.currentTarget as HTMLButtonElement).style.borderColor = "rgba(124, 58, 237, 0.35)";
          (e.currentTarget as HTMLButtonElement).style.background = "rgba(30, 27, 58, 0.7)";
        }}
      >
        <PlusIcon />
        New Chat
      </button>

      {/* Section Header */}
      <div
        style={{
          fontSize: 11,
          fontWeight: 600,
          textTransform: "uppercase",
          letterSpacing: "0.8px",
          color: "#475569",
          paddingLeft: 6,
          marginBottom: 8,
        }}
      >
        Recent Conversations
      </div>

      {/* Sessions list */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          display: "flex",
          flexDirection: "column",
          gap: 4,
          paddingRight: 2,
        }}
      >
        {sessions.length === 0 ? (
          <div style={{ padding: "12px 6px", fontSize: 13, color: "var(--text-muted)" }}>
            No history yet
          </div>
        ) : (
          sessions.map((session) => {
            const isActive = session.id === activeSessionId;
            const isEditing = editingId === session.id;

            return (
              <div
                key={session.id}
                onClick={() => onSelectSession(session.id)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  padding: "9px 12px",
                  borderRadius: "var(--radius-md)",
                  background: isActive
                    ? "rgba(124,58,237,0.15)"
                    : "transparent",
                  border: isActive
                    ? "1px solid rgba(124,58,237,0.3)"
                    : "1px solid transparent",
                  color: isActive ? "var(--text-primary)" : "var(--text-secondary)",
                  fontSize: 13,
                  fontWeight: isActive ? 600 : 400,
                  cursor: "pointer",
                  transition: "all 0.15s ease",
                  position: "relative",
                }}
                className="session-item-row"
              >
                <ChatIcon />

                {isEditing ? (
                  <input
                    type="text"
                    value={editTitle}
                    onChange={(e) => setEditTitle(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") handleSaveRename(session.id);
                      if (e.key === "Escape") setEditingId(null);
                    }}
                    onBlur={() => handleSaveRename(session.id)}
                    autoFocus
                    onClick={(e) => e.stopPropagation()}
                    style={{
                      flex: 1,
                      background: "var(--bg-primary)",
                      border: "1px solid var(--border-accent)",
                      borderRadius: 4,
                      color: "var(--text-primary)",
                      fontSize: 13,
                      padding: "2px 6px",
                      outline: "none",
                    }}
                  />
                ) : (
                  <span
                    style={{
                      flex: 1,
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {session.title || "New Chat"}
                  </span>
                )}

                {!isEditing && (
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 4,
                    }}
                    onClick={(e) => e.stopPropagation()}
                  >
                    <button
                      onClick={(e) => handleStartRename(session, e)}
                      title="Rename chat"
                      style={{
                        background: "transparent",
                        border: "none",
                        color: "var(--text-muted)",
                        cursor: "pointer",
                        padding: 3,
                        borderRadius: 4,
                        display: "flex",
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.color = "var(--text-primary)")}
                      onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-muted)")}
                    >
                      <EditIcon />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteSession(session.id);
                      }}
                      title="Delete chat"
                      style={{
                        background: "transparent",
                        border: "none",
                        color: "var(--text-muted)",
                        cursor: "pointer",
                        padding: 3,
                        borderRadius: 4,
                        display: "flex",
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.color = "#ef4444")}
                      onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-muted)")}
                    >
                      <TrashIcon />
                    </button>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Footer */}
      <div
        style={{
          padding: "12px 8px 0",
          borderTop: "1px solid var(--border-subtle)",
          marginTop: 12,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4 }}>
          <CpuIcon />
          <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
            qwen3:8b via Ollama
          </span>
        </div>
        <div
          style={{
            fontSize: 11,
            color: "var(--text-muted)",
            lineHeight: 1.5,
          }}
        >
          PostgreSQL Chat History
        </div>
      </div>
    </aside>
  );
}
