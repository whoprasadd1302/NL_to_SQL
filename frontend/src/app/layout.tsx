import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
  variable: "--font-inter",
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
    <html lang="en" className={`${inter.variable} h-full`}>
      <body className="h-full flex flex-col antialiased">{children}</body>
    </html>
  );
}
