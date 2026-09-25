"use client";

interface HeaderProps {
  isLoading: boolean;
  selectedLanguage: string;
  onLanguageChange: (lang: string) => void;
}

const SUPPORTED_LANGUAGES = [
  { code: "Auto-Detect", label: "🌐 Auto-Detect" },
  { code: "English", label: "🇬🇧 English" },
  { code: "Hindi (हिंदी)", label: "🇮🇳 Hindi (हिंदी)" },
  { code: "Marathi (मराठी)", label: "🚩 Marathi (मराठी)" },
  { code: "Hinglish", label: "💬 Hinglish" },
];

export function Header({ isLoading, selectedLanguage, onLanguageChange }: HeaderProps) {
  return (
    <header
      style={{
        height: "var(--header-height)",
        minHeight: "var(--header-height)",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "0 20px",
        background: "var(--bg-secondary)",
        borderBottom: "1px solid var(--border-subtle)",
        backdropFilter: "blur(12px)",
        WebkitBackdropFilter: "blur(12px)",
      }}
    >
      {/* Left: Title & Logo */}
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <div style={{ display: "flex", flexDirection: "column" }}>
          <span
            style={{
              fontWeight: 700,
              fontSize: 16,
              color: "var(--text-primary)",
              letterSpacing: "-0.3px",
            }}
          >
            MitraAI
          </span>
          <span style={{ fontSize: 11, color: "var(--text-muted)", lineHeight: 1 }}>
            Multilingual AI Assistant
          </span>
        </div>
      </div>

      {/* Center / Right: Language Selector & Status */}
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        {/* Language Dropdown */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 6,
            background: "var(--bg-glass)",
            border: "1px solid var(--border-medium)",
            borderRadius: "var(--radius-md)",
            padding: "4px 10px",
            transition: "all 0.2s ease",
          }}
        >
          <label
            htmlFor="language-select"
            style={{
              fontSize: 12,
              fontWeight: 500,
              color: "var(--text-secondary)",
              cursor: "pointer",
            }}
          >
            Language:
          </label>
          <select
            id="language-select"
            value={selectedLanguage}
            onChange={(e) => onLanguageChange(e.target.value)}
            style={{
              background: "transparent",
              border: "none",
              color: "var(--text-primary)",
              fontSize: 12,
              fontWeight: 600,
              outline: "none",
              cursor: "pointer",
              padding: "2px 4px",
            }}
          >
            {SUPPORTED_LANGUAGES.map((lang) => (
              <option
                key={lang.code}
                value={lang.code}
                style={{
                  background: "#18181b",
                  color: "#f4f4f5",
                }}
              >
                {lang.label}
              </option>
            ))}
          </select>
        </div>

        {/* Status Indicator */}
        {isLoading ? (
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <span
              style={{
                width: 7,
                height: 7,
                borderRadius: "50%",
                background: "#f59e0b",
                animation: "pulse-ring 1.2s ease-out infinite",
                display: "block",
              }}
            />
            <span style={{ fontSize: 12, color: "#f59e0b", fontWeight: 500 }}>
              Thinking…
            </span>
          </div>
        ) : (
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <span
              style={{
                width: 7,
                height: 7,
                borderRadius: "50%",
                background: "#22c55e",
                display: "block",
                boxShadow: "0 0 6px rgba(34,197,94,0.6)",
              }}
            />
            <span style={{ fontSize: 12, color: "#22c55e", fontWeight: 500 }}>
              Online
            </span>
          </div>
        )}

        {/* Model badge */}
        <div
          style={{
            fontSize: 12,
            color: "var(--text-accent)",
            background: "rgba(124,58,237,0.12)",
            border: "1px solid rgba(124,58,237,0.25)",
            borderRadius: 99,
            padding: "3px 10px",
            fontWeight: 500,
          }}
        >
          qwen3:8b
        </div>
      </div>
    </header>
  );
}
