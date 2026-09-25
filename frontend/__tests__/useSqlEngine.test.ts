import { renderHook, act } from "@testing-library/react";
import { useSqlEngine } from "../hooks/useSqlEngine";

describe("useSqlEngine Hook", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("executeSql returns results and updates hook state", async () => {
    const mockApiResponse = {
      success: true,
      language: "hi",
      language_name: "Hindi",
      sql: "SELECT * FROM customers WHERE city = 'Mumbai';",
      results: [
        { id: 1, name: "Ramesh Sharma", city: "Mumbai", balance: 55000 },
      ],
      summary: "Found 1 customer from Mumbai.",
      chart_type: "bar",
      chart_data: { type: "bar", labels: ["Mumbai"], series: [{ data: [55000] }] },
      count: 1,
      execution_time: 0.04,
    };

    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: jest.fn().mockResolvedValue(mockApiResponse),
    });

    const { result } = renderHook(() => useSqlEngine());

    let execResult: any;
    await act(async () => {
      execResult = await result.current.executeSql("Mumbai ke customers", "hi");
    });

    expect(execResult.success).toBe(true);
    expect(execResult.sql).toBe("SELECT * FROM customers WHERE city = 'Mumbai';");
    expect(result.current.sql).toBe("SELECT * FROM customers WHERE city = 'Mumbai';");
    expect(result.current.results.length).toBe(1);
    expect(result.current.summary).toBe("Found 1 customer from Mumbai.");
    expect(result.current.chartType).toBe("bar");
    expect(result.current.executionTime).toBe(0.04);
    expect(result.current.rowCount).toBe(1);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  test("exportCsv downloads CSV file via API endpoint or fallback", async () => {
    const mockBlob = new Blob(["id,name\n1,Alice"], { type: "text/csv" });
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      blob: jest.fn().mockResolvedValue(mockBlob),
    });

    // Mock URL.createObjectURL and document.createElement
    global.URL.createObjectURL = jest.fn().mockReturnValue("blob:http://localhost/test");
    global.URL.revokeObjectURL = jest.fn();

    const { result } = renderHook(() => useSqlEngine());

    const sampleResults = [{ id: 1, name: "Alice" }];
    await act(async () => {
      await result.current.exportCsv(sampleResults, "Show Alice", "SELECT * FROM users");
    });

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/sql/export"),
      expect.objectContaining({
        method: "POST",
      })
    );
  });

  test("error handling works when execution API fails", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 500,
      json: jest.fn().mockResolvedValue({ detail: "Database connection timed out" }),
    });

    const { result } = renderHook(() => useSqlEngine());

    let execResult: any;
    await act(async () => {
      execResult = await result.current.executeSql("Bad Query");
    });

    expect(execResult.success).toBe(false);
    expect(result.current.error).toContain("Database connection timed out");
    expect(result.current.isLoading).toBe(false);
  });

  test("getSchema fetches and updates schema state", async () => {
    const mockSchema = {
      tables: ["customers", "accounts"],
      columns: {
        customers: [{ name: "id", type: "INT" }, { name: "name", type: "TEXT" }],
      },
      foreign_keys: [],
      schema_context: "Tables: customers",
    };

    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: jest.fn().mockResolvedValue(mockSchema),
    });

    const { result } = renderHook(() => useSqlEngine());

    let schema: any;
    await act(async () => {
      schema = await result.current.getSchema();
    });

    expect(schema.tables).toEqual(["customers", "accounts"]);
    expect(result.current.schema?.tables).toContain("customers");
    expect(result.current.isLoading).toBe(false);
  });
});
