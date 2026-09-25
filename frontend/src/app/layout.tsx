import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "MitraAI – Multilingual AI Assistant",
  description:
    "MitraAI is an intelligent multilingual conversational AI assistant powered by Ollama and qwen3:8b. Chat in any language and get accurate, clear answers.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className} style={{ margin: 0, padding: 0, height: "100%", width: "100%", overflow: "hidden", background: "#080911" }}>
        {children}
      </body>
    </html>
  );
}
