import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { ResultsTable } from "../components/ResultsTable";

describe("ResultsTable Component", () => {
  const sampleData = [
    { id: 1, name: "Alice", city: "Mumbai", balance: 55000 },
    { id: 2, name: "Bob", city: "Pune", balance: 82000 },
    { id: 3, name: "Charlie", city: "Delhi", balance: 34000 },
  ];

  test("renders table with data and columns", () => {
    render(<ResultsTable data={sampleData} />);

    // Check table headers
    expect(screen.getByText("id")).toBeInTheDocument();
    expect(screen.getByText("name")).toBeInTheDocument();
    expect(screen.getByText("city")).toBeInTheDocument();
    expect(screen.getByText("balance")).toBeInTheDocument();

    // Check row data
    expect(screen.getByText("Alice")).toBeInTheDocument();
    expect(screen.getByText("Mumbai")).toBeInTheDocument();
    expect(screen.getByText("55000")).toBeInTheDocument();

    expect(screen.getByText("Bob")).toBeInTheDocument();
    expect(screen.getByText("Charlie")).toBeInTheDocument();

    // Check row count badge
    expect(screen.getByTestId("row-count-badge")).toHaveTextContent("3 rows");
  });

  test("sorting works ascending and descending", () => {
    render(<ResultsTable data={sampleData} />);

    const balanceHeader = screen.getByTestId("column-header-balance");

    // First click: ascending
    fireEvent.click(balanceHeader);
    let rows = screen.getAllByTestId(/^table-row-/);
    expect(rows[0]).toHaveTextContent("34000"); // Charlie (lowest balance)
    expect(rows[2]).toHaveTextContent("82000"); // Bob (highest balance)

    // Second click: descending
    fireEvent.click(balanceHeader);
    rows = screen.getAllByTestId(/^table-row-/);
    expect(rows[0]).toHaveTextContent("82000"); // Bob (highest)
    expect(rows[2]).toHaveTextContent("34000"); // Charlie (lowest)
  });

  test("pagination works for large datasets", () => {
    // Generate 60 rows
    const largeData = Array.from({ length: 60 }, (_, i) => ({
      id: i + 1,
      name: `User ${i + 1}`,
      score: i * 10,
    }));

    render(<ResultsTable data={largeData} pageSize={50} />);

    // Page 1 should show 50 rows
    expect(screen.getByText("Showing 1-50 of 60")).toBeInTheDocument();
    expect(screen.getByText("User 1")).toBeInTheDocument();
    expect(screen.getByText("User 50")).toBeInTheDocument();
    expect(screen.queryByText("User 51")).not.toBeInTheDocument();

    // Navigate to next page
    const nextBtn = screen.getByTestId("next-page-btn");
    fireEvent.click(nextBtn);

    // Page 2 should show remaining 10 rows
    expect(screen.getByText("Showing 51-60 of 60")).toBeInTheDocument();
    expect(screen.getByText("User 51")).toBeInTheDocument();
    expect(screen.getByText("User 60")).toBeInTheDocument();
    expect(screen.queryByText("User 1")).not.toBeInTheDocument();
  });

  test("empty state shows message", () => {
    render(<ResultsTable data={[]} />);

    expect(screen.getByTestId("results-table-empty")).toBeInTheDocument();
    expect(screen.getByText("No Results Found")).toBeInTheDocument();
    expect(screen.getByText(/The query returned 0 records/i)).toBeInTheDocument();
  });
});
