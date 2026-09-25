import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { SqlDisplay } from "../components/SqlDisplay";

describe("SqlDisplay Component", () => {
  const sampleSql = "SELECT * FROM customers WHERE city = 'Mumbai';";

  test("renders SQL correctly", () => {
    render(
      <SqlDisplay
        sql={sampleSql}
        language="hi"
        language_name="Hindi"
        execution_time={0.05}
      />
    );

    // Verify SQL text is rendered
    expect(screen.getByTestId("sql-code")).toHaveTextContent("SELECT * FROM customers WHERE city = 'Mumbai';");

    // Verify execution time is displayed
    expect(screen.getByTestId("execution-time")).toHaveTextContent("50ms");
  });

  test("copy button works and updates feedback state", async () => {
    // Mock navigator.clipboard.writeText
    const mockWriteText = jest.fn().mockResolvedValue(undefined);
    Object.assign(navigator, {
      clipboard: {
        writeText: mockWriteText,
      },
    });

    render(<SqlDisplay sql={sampleSql} />);

    const copyButton = screen.getByTestId("copy-button");
    expect(copyButton).toHaveTextContent("Copy");

    fireEvent.click(copyButton);

    expect(mockWriteText).toHaveBeenCalledWith(sampleSql);
    expect(await screen.findByText("Copied!")).toBeInTheDocument();
  });

  test("language badge shows correct language", () => {
    const { rerender } = render(
      <SqlDisplay sql={sampleSql} language="hi" language_name="Hindi" />
    );

    expect(screen.getByTestId("language-badge")).toHaveTextContent("HI");

    rerender(<SqlDisplay sql={sampleSql} language="mr" language_name="Marathi" />);
    expect(screen.getByTestId("language-badge")).toHaveTextContent("MR");

    rerender(<SqlDisplay sql={sampleSql} language="en" language_name="English" />);
    expect(screen.getByTestId("language-badge")).toHaveTextContent("EN");
  });
});
