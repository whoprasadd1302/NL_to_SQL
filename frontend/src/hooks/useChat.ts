"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import type { Message, ChatSession, ChatState } from "@/types/chat";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

function generateId(): string {
  return `msg_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
}

const DEFAULT_SESSION: ChatSession = {
  id: "default",
  title: "New Chat",
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  message_count: 0,
};

export function useChat() {
  const [sessions, setSessions] = useState<ChatSession[]>([DEFAULT_SESSION]);
  const [activeSessionId, setActiveSessionId] = useState<string>("default");
  const [selectedLanguage, setSelectedLanguage] = useState<string>("Auto-Detect");
  const [state, setState] = useState<ChatState>({
    messages: [],
    isLoading: false,
    error: null,
  });

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, 50);
  }, []);

  // Fetch all sessions from backend
  const fetchSessions = useCallback(async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/sessions`);
      if (!res.ok) return;
      const data = await res.json();
      if (Array.isArray(data) && data.length > 0) {
        setSessions(data);
      }
    } catch (e) {
      console.warn("Could not fetch sessions from backend:", e);
    }
  }, []);

  // Fetch messages for active session
  const fetchHistory = useCallback(async (sessionId: string) => {
    try {
      const res = await fetch(`${BACKEND_URL}/history?session_id=${sessionId}`);
      if (!res.ok) return;
      const data = await res.json();
      if (Array.isArray(data)) {
        const loadedMessages: Message[] = data.map((m: any) => ({
          id: m.id || generateId(),
          role: m.role,
          content: m.content,
          timestamp: m.timestamp ? new Date(m.timestamp) : new Date(),
        }));
        setState({
          messages: loadedMessages,
          isLoading: false,
          error: null,
        });
        scrollToBottom();
      }
    } catch (e) {
      console.warn("Could not load history for session:", sessionId, e);
    }
  }, [scrollToBottom]);

  // Initial load of sessions
  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  // Load history whenever activeSessionId changes
  useEffect(() => {
    if (activeSessionId) {
      fetchHistory(activeSessionId);
    }
  }, [activeSessionId, fetchHistory]);

  const createNewSession = useCallback(async () => {
    const tempId = `sess_${Date.now()}`;
    const newSession: ChatSession = {
      id: tempId,
      title: "New Chat",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      message_count: 0,
    };

    // Immediate optimistic update
    setSessions((prev) => [newSession, ...prev.filter((s) => s.id !== "default" || s.message_count > 0)]);
    setActiveSessionId(tempId);
    setState({ messages: [], isLoading: false, error: null });

    try {
      const res = await fetch(`${BACKEND_URL}/sessions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: "New Chat" }),
      });
      if (res.ok) {
        const serverSession: ChatSession = await res.json();
        setSessions((prev) =>
          prev.map((s) => (s.id === tempId ? serverSession : s))
        );
        setActiveSessionId(serverSession.id);
      }
    } catch (e) {
      console.warn("Could not sync new session to backend:", e);
    }
  }, []);

  const selectSession = useCallback((sessionId: string) => {
    setActiveSessionId(sessionId);
  }, []);

  const deleteSession = useCallback(
    async (sessionId: string) => {
      // Optimistic delete
      setSessions((prev) => {
        const filtered = prev.filter((s) => s.id !== sessionId);
        if (filtered.length === 0) {
          const fresh = { ...DEFAULT_SESSION, id: `sess_${Date.now()}` };
          setActiveSessionId(fresh.id);
          setState({ messages: [], isLoading: false, error: null });
          return [fresh];
        }
        if (activeSessionId === sessionId) {
          setActiveSessionId(filtered[0].id);
        }
        return filtered;
      });

      try {
        await fetch(`${BACKEND_URL}/sessions/${sessionId}`, {
          method: "DELETE",
        });
      } catch (e) {
        console.warn("Failed to delete session from backend:", e);
      }
    },
    [activeSessionId]
  );

  const renameSession = useCallback(
    async (sessionId: string, newTitle: string) => {
      if (!newTitle.trim()) return;

      // Optimistic rename
      setSessions((prev) =>
        prev.map((s) => (s.id === sessionId ? { ...s, title: newTitle.trim() } : s))
      );

      try {
        await fetch(`${BACKEND_URL}/sessions/${sessionId}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ title: newTitle.trim() }),
        });
      } catch (e) {
        console.warn("Failed to sync renamed session title:", e);
      }
    },
    []
  );

  const sendMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed) return;

      const currentSessionId = activeSessionId;

      const userMessage: Message = {
        id: generateId(),
        role: "user",
        content: trimmed,
        timestamp: new Date(),
      };

      // Optimistically update session title if it's currently "New Chat"
      setSessions((prev) =>
        prev.map((s) => {
          if (s.id === currentSessionId && (s.title === "New Chat" || !s.title)) {
            const shortTitle = trimmed.length > 30 ? trimmed.slice(0, 30) + "..." : trimmed;
            return { ...s, title: shortTitle, message_count: (s.message_count || 0) + 1 };
          }
          if (s.id === currentSessionId) {
            return { ...s, message_count: (s.message_count || 0) + 1 };
          }
          return s;
        })
      );

      setState((prev) => ({
        ...prev,
        messages: [...prev.messages, userMessage],
        isLoading: true,
        error: null,
      }));

      scrollToBottom();

      try {
        const assistantId = generateId();
        const initialAssistantMsg: Message = {
          id: assistantId,
          role: "assistant",
          content: "",
          timestamp: new Date(),
          isStreaming: true,
        };

        setState((prev) => ({
          ...prev,
          messages: [...prev.messages, initialAssistantMsg],
        }));

        const response = await fetch(`${BACKEND_URL}/chat/stream`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message: trimmed,
            session_id: currentSessionId,
            target_language: selectedLanguage,
          }),
        });

        if (!response.ok || !response.body) {
          // Fallback to non-streaming /chat
          const fallbackRes = await fetch(`${BACKEND_URL}/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              message: trimmed,
              session_id: currentSessionId,
              target_language: selectedLanguage,
            }),
          });

          if (!fallbackRes.ok) {
            const err = await fallbackRes.json().catch(() => ({}));
            throw new Error(err.detail || `Server error: ${fallbackRes.status}`);
          }

          const data = await fallbackRes.json();
          setState((prev) => ({
            ...prev,
            messages: prev.messages.map((m) =>
              m.id === assistantId
                ? { ...m, content: data.response, isStreaming: false, sqlResult: data.sql_result ?? null }
                : m
            ),
            isLoading: false,
          }));
          scrollToBottom();
          fetchSessions();
          return;
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

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
                  setState((prev) => ({
                    ...prev,
                    messages: prev.messages.map((m) =>
                      m.id === assistantId
                        ? { ...m, content: m.content + data.token }
                        : m
                    ),
                  }));
                  scrollToBottom();
                } else if (data.sql_result) {
                  setState((prev) => ({
                    ...prev,
                    messages: prev.messages.map((m) =>
                      m.id === assistantId
                        ? { ...m, sqlResult: data.sql_result }
                        : m
                    ),
                  }));
                } else if (data.done) {
                  setState((prev) => ({
                    ...prev,
                    messages: prev.messages.map((m) =>
                      m.id === assistantId ? { ...m, isStreaming: false } : m
                    ),
                    isLoading: false,
                  }));
                } else if (data.error) {
                  throw new Error(data.error);
                }
              } catch (e) {
                // Ignore chunk parse errors
              }
            }
          }
        }

        setState((prev) => ({
          ...prev,
          messages: prev.messages.map((m) =>
            m.id === assistantId ? { ...m, isStreaming: false } : m
          ),
          isLoading: false,
          error: null,
        }));

        fetchSessions();
      } catch (err) {
        const errorMessage: Message = {
          id: generateId(),
          role: "assistant",
          content:
            "⚠️ Could not reach the backend. Make sure the FastAPI backend is running on http://localhost:8000.",
          timestamp: new Date(),
          isError: true,
        };

        setState((prev) => ({
          ...prev,
          messages: prev.messages
            .filter((m) => m.content.length > 0 || !m.isStreaming)
            .concat(errorMessage),
          isLoading: false,
          error: err instanceof Error ? err.message : "Unknown error",
        }));
      }

      scrollToBottom();
    },
    [activeSessionId, selectedLanguage, scrollToBottom, fetchSessions]
  );

  const clearMessages = useCallback(async () => {
    setState({ messages: [], isLoading: false, error: null });
    try {
      await fetch(`${BACKEND_URL}/history?session_id=${activeSessionId}`, {
        method: "DELETE",
      });
      fetchSessions();
    } catch (e) {
      console.warn("Failed to clear chat history in backend:", e);
    }
  }, [activeSessionId, fetchSessions]);

  return {
    sessions,
    activeSessionId,
    selectedLanguage,
    setSelectedLanguage,
    messages: state.messages,
    isLoading: state.isLoading,
    error: state.error,
    sendMessage,
    createNewSession,
    selectSession,
    deleteSession,
    renameSession,
    clearMessages,
    messagesEndRef,
  };
}
