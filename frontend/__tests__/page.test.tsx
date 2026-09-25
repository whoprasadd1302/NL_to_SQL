import React from "react";
import { render, screen, fireEvent, act } from "@testing-library/react";
import Home from "../app/page";

// Mock useChat and useSqlEngine hooks
jest.mock("@/hooks/useChat", () => ({
  useChat: jest.fn(() => ({
    sessions: [{ id: "default", title: "New Chat", message_count: 1 }],
    activeSessionId: "default",
    selectedLanguage: "English",
    setSelectedLanguage: jest.fn(),
    messages: [
      { id: "msg_1", role: "user", content: "Hello MitraAI", timestamp: new Date() },
      { id: "msg_2", role: "assistant", content: "Hello! How can I help you?", timestamp: new Date() },
    ],
    isLoading: false,
    sendMessage: jest.fn(),
    createNewSession: jest.fn(),
    selectSession: jest.fn(),
    deleteSession: jest.fn(),
    renameSession: jest.fn(),
    messagesEndRef: { current: null },
  })),
}));

const mockExecuteSql = jest.fn();
const mockExportCsv = jest.fn();

jest.mock("@/hooks/useSqlEngine", () => ({
  useSqlEngine: jest.fn(() => ({
    isLoading: false,
    isStreaming: false,
    error: null,
    sql: "SELECT * FROM customers WHERE city = 'Mumbai';",
    results: [
      { id: 1, name: "Ramesh Sharma", city: "Mumbai", balance: 55000 },
    ],
    summary: "Found 1 customer in Mumbai.",
    chartType: "bar",
    chartData: {
      type: "bar",
      labels: ["Mumbai"],
      series: [{ name: "balance", data: [55000] }],
    },
    schema: null,
    executionTime: 0.05,
    rowCount: 1,
    language: "hi",
    languageName: "Hindi",
    executeSql: mockExecuteSql,
    generateSql: jest.fn(),
    exportCsv: mockExportCsv,
    getSchema: jest.fn(),
    reset: jest.fn(),
  })),
}));

describe("Home Page with Mode Switcher", () => {
  test("Chat mode shows conversation messages", () => {
    render(<Home />);

    // Check Chat mode view
    expect(screen.getByTestId("chat-mode-view")).toBeInTheDocument();
    expect(screen.getByText("Hello MitraAI")).toBeInTheDocument();
    expect(screen.getByText("Hello! How can I help you?")).toBeInTheDocument();
  });

  test("mode toggle switches between Chat and SQL modes", () => {
    render(<Home />);

    const sqlModeBtn = screen.getByTestId("mode-sql-btn");
    const chatModeBtn = screen.getByTestId("mode-chat-btn");

    // Click SQL Mode
    fireEvent.click(sqlModeBtn);
    expect(screen.getByTestId("sql-mode-view")).toBeInTheDocument();
    expect(screen.getByTestId("sql-db-badge")).toHaveTextContent("SQLite Banking DB");

    // Click Chat Mode
    fireEvent.click(chatModeBtn);
    expect(screen.getByTestId("chat-mode-view")).toBeInTheDocument();
  });

  test("SQL mode displays SqlDisplay, ResultChart, ResultsTable and summary", () => {
    render(<Home />);

    // Switch to SQL mode
    const sqlModeBtn = screen.getByTestId("mode-sql-btn");
    fireEvent.click(sqlModeBtn);

    // Verify SqlDisplay
    expect(screen.getByTestId("sql-display")).toBeInTheDocument();
    expect(screen.getByTestId("sql-code")).toHaveTextContent("SELECT * FROM customers WHERE city = 'Mumbai';");

    // Verify Summary
    expect(screen.getByTestId("sql-summary-card")).toHaveTextContent("Found 1 customer in Mumbai.");

    // Verify ResultChart
    expect(screen.getByTestId("bar-chart-container")).toBeInTheDocument();

    // Verify ResultsTable
    expect(screen.getByTestId("results-table-container")).toBeInTheDocument();
    expect(screen.getByText("Ramesh Sharma")).toBeInTheDocument();
  });
});
