import React from "react";
import { render, screen } from "@testing-library/react";
import { ResultChart } from "../components/ResultChart";

describe("ResultChart Component", () => {
  test("bar chart renders with labels and values", () => {
    const chartData = {
      type: "bar",
      x_axis: "city",
      y_axis: "total_balance",
      labels: ["Mumbai", "Pune", "Delhi"],
      series: [
        {
          name: "total_balance",
          data: [55000, 82000, 34000],
        },
      ],
    };

    render(<ResultChart chart_type="bar" chart_data={chartData} title="Balance by City" />);

    expect(screen.getByTestId("bar-chart-container")).toBeInTheDocument();
    expect(screen.getByText("Balance by City")).toBeInTheDocument();
    expect(screen.getByText("Mumbai")).toBeInTheDocument();
    expect(screen.getByText("Pune")).toBeInTheDocument();
    expect(screen.getByText("Delhi")).toBeInTheDocument();
  });

  test("number card renders metric value and title", () => {
    const chartData = {
      type: "number_card",
      title: "total_customers",
      value: 1250,
    };

    render(<ResultChart chart_type="number_card" chart_data={chartData} />);

    expect(screen.getByTestId("number-card-container")).toBeInTheDocument();
    expect(screen.getByText("TOTAL CUSTOMERS")).toBeInTheDocument();
    expect(screen.getByTestId("number-card-value")).toHaveTextContent("1,250");
  });

  test("line chart renders correctly", () => {
    const chartData = {
      type: "line",
      labels: ["Jan", "Feb", "Mar"],
      series: [
        {
          name: "revenue",
          data: [1000, 2500, 3200],
        },
      ],
    };

    render(<ResultChart chart_type="line" chart_data={chartData} title="Revenue Trend" />);

    expect(screen.getByTestId("line-chart-container")).toBeInTheDocument();
    expect(screen.getByText("Revenue Trend")).toBeInTheDocument();
    expect(screen.getByText("Jan")).toBeInTheDocument();
  });

  test("empty or invalid chart_type shows nothing", () => {
    const { container: emptyTypeContainer } = render(
      <ResultChart chart_type={null} chart_data={{ value: 42 }} />
    );
    expect(emptyTypeContainer).toBeEmptyDOMElement();

    const { container: emptyDataContainer } = render(
      <ResultChart chart_type="bar" chart_data={null} />
    );
    expect(emptyDataContainer).toBeEmptyDOMElement();

    const { container: tableTypeContainer } = render(
      <ResultChart chart_type="table" chart_data={{ type: "table" }} />
    );
    expect(tableTypeContainer).toBeEmptyDOMElement();
  });
});
