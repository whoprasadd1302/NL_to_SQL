"use client";

function Dot({ delay }: { delay: string }) {
  return (
    <span
      style={{
        display: "inline-block",
        width: 7,
        height: 7,
        borderRadius: "50%",
        background: "var(--accent-violet)",
        animation: "typingBlink 1.2s ease-in-out infinite",
        animationDelay: delay,
      }}
    />
  );
}

export function TypingIndicator() {
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
      {/* Avatar */}
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

      {/* Dots bubble */}
      <div
        className="glass"
        style={{
          padding: "14px 18px",
          borderRadius: "4px 18px 18px 18px",
          display: "flex",
          alignItems: "center",
          gap: 5,
        }}
      >
        <Dot delay="0s" />
        <Dot delay="0.2s" />
        <Dot delay="0.4s" />
      </div>
    </div>
  );
}
