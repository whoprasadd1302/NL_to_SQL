"use client";

interface HeaderProps {
  isLoading: boolean;
  selectedLanguage: string;
  onLanguageChange: (lang: string) => void;
}

const SUPPORTED_LANGUAGES = [
  { code: "Auto-Detect", label: "Auto-Detect" },
  { code: "English", label: "English" },
  { code: "Hindi (हिंदी)", label: "Hindi (हिंदी)" },
  { code: "Marathi (मराठी)", label: "Marathi (मराठी)" },
  { code: "Hinglish", label: "Hinglish" },
];

export function Header({ isLoading, selectedLanguage, onLanguageChange }: HeaderProps) {
  return (
    <header
      style={{
        height: 56,
        minHeight: 56,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "0 24px",
        background: "rgba(11, 13, 23, 0.8)",
        borderBottom: "1px solid rgba(255, 255, 255, 0.05)",
        backdropFilter: "blur(16px)",
        WebkitBackdropFilter: "blur(16px)",
      }}
    >
      {/* Left: Title & Subtitle */}
      <div style={{ display: "flex", flexDirection: "column" }}>
        <span
          style={{
            fontWeight: 700,
            fontSize: 15,
            color: "#f8fafc",
            letterSpacing: "-0.2px",
          }}
        >
          MitraAI
        </span>
        <span style={{ fontSize: 11, color: "#64748b", lineHeight: 1.2 }}>
          Multilingual AI Assistant
        </span>
      </div>

      {/* Right: Language Selector, Online Status & Model Pill */}
      <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
        {/* Language Dropdown */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 6,
          }}
        >
          <label
            htmlFor="language-select"
            style={{
              fontSize: 12,
              fontWeight: 500,
              color: "#94a3b8",
            }}
          >
            Language:
          </label>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              background: "rgba(22, 27, 46, 0.8)",
              border: "1px solid rgba(255, 255, 255, 0.1)",
              borderRadius: 20,
              padding: "3px 10px 3px 8px",
              gap: 4,
            }}
          >
            <span style={{ fontSize: 12 }}>🌐</span>
            <select
              id="language-select"
              value={selectedLanguage}
              onChange={(e) => onLanguageChange(e.target.value)}
              style={{
                background: "transparent",
                border: "none",
                color: "#e2e8f0",
                fontSize: 12,
                fontWeight: 500,
                outline: "none",
                cursor: "pointer",
                padding: "2px 0",
              }}
            >
              {SUPPORTED_LANGUAGES.map((lang) => (
                <option
                  key={lang.code}
                  value={lang.code}
                  style={{
                    background: "#111422",
                    color: "#f8fafc",
                  }}
                >
                  {lang.label}
                </option>
              ))}
            </select>
          </div>
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
                boxShadow: "0 0 8px rgba(34,197,94,0.7)",
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
            fontSize: 11,
            color: "#c084fc",
            background: "rgba(147, 51, 234, 0.15)",
            border: "1px solid rgba(168, 85, 247, 0.3)",
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
