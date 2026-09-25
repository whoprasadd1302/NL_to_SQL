"use client";

import { useState, useRef, useCallback, KeyboardEvent } from "react";

interface ChatInputProps {
  onSend: (text: string) => void;
  isLoading: boolean;
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

export function ChatInput({ onSend, isLoading }: ChatInputProps) {
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
        padding: "12px 16px 16px",
        background: "var(--bg-secondary)",
        borderTop: "1px solid var(--border-subtle)",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "flex-end",
          gap: 10,
          background: "var(--bg-elevated)",
          borderRadius: "var(--radius-xl)",
          border: `1px solid ${isFocused ? "var(--border-accent)" : "var(--border-subtle)"}`,
          padding: "10px 12px 10px 16px",
          transition: "border-color 0.2s ease",
          boxShadow: isFocused ? "0 0 0 3px rgba(124,58,237,0.12)" : "none",
        }}
      >
        <textarea
          ref={textareaRef}
          value={value}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          placeholder="Message MitraAI… (Enter to send, Shift+Enter for newline)"
          rows={1}
          disabled={isLoading}
          style={{
            flex: 1,
            minHeight: 24,
            maxHeight: 144,
            overflowY: "auto",
            background: "transparent",
            color: "var(--text-primary)",
            fontSize: 15,
            lineHeight: "24px",
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
            width: 38,
            height: 38,
            borderRadius: "50%",
            background: canSend
              ? "linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%)"
              : "var(--bg-glass)",
            border: `1px solid ${canSend ? "transparent" : "var(--border-subtle)"}`,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
            color: canSend ? "#fff" : "var(--text-muted)",
            transition: "all 0.2s ease",
            boxShadow: canSend ? "0 0 16px rgba(124,58,237,0.4)" : "none",
            transform: canSend ? "scale(1)" : "scale(0.9)",
            cursor: canSend ? "pointer" : "not-allowed",
          }}
        >
          {isLoading ? (
            <span
              style={{
                width: 16,
                height: 16,
                border: "2px solid rgba(255,255,255,0.3)",
                borderTopColor: "#fff",
                borderRadius: "50%",
                animation: "spin-slow 0.7s linear infinite",
                display: "block",
              }}
            />
          ) : (
            <SendIcon size={16} />
          )}
        </button>
      </div>

      <p
        style={{
          textAlign: "center",
          fontSize: 11,
          color: "var(--text-muted)",
          marginTop: 8,
        }}
      >
        MitraAI can make mistakes. Verify important information.
      </p>
    </div>
  );
}
