"use client";

import { useState, useRef, useCallback, KeyboardEvent } from "react";

interface ChatInputProps {
  onSend: (text: string) => void;
  isLoading: boolean;
  placeholder?: string;
}

const SendIcon = ({ size = 18 }: { size?: number }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth={2.2}
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <line x1="22" y1="2" x2="11" y2="13" />
    <polygon points="22 2 15 22 11 13 2 9 22 2" />
  </svg>
);

export function ChatInput({ onSend, isLoading, placeholder }: ChatInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [isFocused, setIsFocused] = useState(false);

  const adjustHeight = useCallback(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    const maxHeight = 5 * 24 + 24; // ~6 rows
    ta.style.height = Math.min(ta.scrollHeight, maxHeight) + "px";
  }, []);

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      setValue(e.target.value);
      adjustHeight();
    },
    [adjustHeight]
  );

  const handleSend = useCallback(() => {
    const trimmed = value.trim();
    if (!trimmed || isLoading) return;
    onSend(trimmed);
    setValue("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }, [value, isLoading, onSend]);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend]
  );

  const canSend = value.trim().length > 0 && !isLoading;

  return (
    <div
      style={{
        padding: "10px 24px 14px",
        background: "transparent",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 12,
          background: "rgba(16, 20, 36, 0.85)",
          borderRadius: 28,
          border: `1px solid ${isFocused ? "rgba(139, 92, 246, 0.5)" : "rgba(255, 255, 255, 0.08)"}`,
          padding: "8px 14px 8px 20px",
          transition: "all 0.2s ease",
          boxShadow: isFocused ? "0 0 16px rgba(124, 58, 237, 0.2)" : "0 4px 20px rgba(0, 0, 0, 0.25)",
        }}
      >
        <textarea
          ref={textareaRef}
          value={value}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          placeholder={placeholder ?? "Message MitraAI... (Enter to send, Shift+Enter for newline)"}
          rows={1}
          disabled={isLoading}
          style={{
            flex: 1,
            minHeight: 24,
            maxHeight: 120,
            overflowY: "auto",
            background: "transparent",
            color: "#f8fafc",
            fontSize: 14,
            lineHeight: "22px",
            resize: "none",
            outline: "none",
            border: "none",
            fontFamily: "inherit",
            padding: 0,
          }}
          id="chat-input"
        />

        {/* Send button */}
        <button
          id="send-button"
          onClick={handleSend}
          disabled={!canSend}
          title="Send message"
          style={{
            width: 34,
            height: 34,
            borderRadius: "50%",
            background: canSend
              ? "linear-gradient(135deg, #7c3aed 0%, #6366f1 100%)"
              : "rgba(255, 255, 255, 0.04)",
            border: `1px solid ${canSend ? "transparent" : "rgba(255, 255, 255, 0.06)"}`,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
            color: canSend ? "#fff" : "#475569",
            transition: "all 0.2s ease",
            boxShadow: canSend ? "0 0 12px rgba(124, 58, 237, 0.5)" : "none",
            cursor: canSend ? "pointer" : "not-allowed",
          }}
        >
          {isLoading ? (
            <span
              style={{
                width: 14,
                height: 14,
                border: "2px solid rgba(255,255,255,0.3)",
                borderTopColor: "#fff",
                borderRadius: "50%",
                animation: "spin-slow 0.7s linear infinite",
                display: "block",
              }}
            />
          ) : (
            <SendIcon size={14} />
          )}
        </button>
      </div>

      <p
        style={{
          textAlign: "center",
          fontSize: 11,
          color: "#475569",
          marginTop: 8,
        }}
      >
        MitraAI can make mistakes. Verify important information.
      </p>
    </div>
  );
}
