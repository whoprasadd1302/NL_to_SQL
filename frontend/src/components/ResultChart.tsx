"use client";

import React, { useState } from "react";

export interface ChartSeries {
  name?: string;
  data: number[];
}

export interface ChartData {
  type?: string;
  title?: string;
  value?: number | string;
  labels?: string[];
  series?: ChartSeries[];
  x_axis?: string;
  y_axis?: string;
  columns?: string[];
  rows?: Array<Record<string, any>>;
}

export interface ResultChartProps {
  chart_type?: string | null;
  chart_data?: ChartData | null;
  title?: string;
}

const PALETTE = [
  "#a855f7", // purple
  "#3b82f6", // blue
  "#10b981", // emerald
  "#f59e0b", // amber
  "#ec4899", // pink
  "#06b6d4", // cyan
  "#8b5cf6", // violet
  "#14b8a6", // teal
];

/**
 * Format numbers into compact readable format (e.g. 1.2K, 50.5M, ₹55,000).
 */
function formatNumber(val: number | string | undefined | null): string {
  if (val === undefined || val === null) return "0";
  const num = typeof val === "number" ? val : parseFloat(String(val));
  if (isNaN(num)) return String(val);

  if (Math.abs(num) >= 1_000_000) {
    return (num / 1_000_000).toFixed(1).replace(/\.0$/, "") + "M";
  }
  if (Math.abs(num) >= 10_000) {
    return num.toLocaleString();
  }
  return Number.isInteger(num) ? num.toString() : num.toFixed(2);
}

/* -------------------------------------------------------------------------- */
/* 1. Number Card Component                                                   */
/* -------------------------------------------------------------------------- */
function NumberCard({ data, title }: { data: ChartData; title?: string }) {
  const displayTitle = title || data.title || "Total";
  const value = data.value !== undefined ? data.value : 0;

  return (
    <div
      data-testid="number-card-container"
      className="glass"
      style={{
        padding: "24px 28px",
        borderRadius: 14,
        background: "linear-gradient(135deg, rgba(30, 27, 75, 0.7) 0%, rgba(15, 23, 42, 0.85) 100%)",
        border: "1px solid rgba(168, 85, 247, 0.3)",
        boxShadow: "0 8px 32px rgba(124, 58, 237, 0.15)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        textAlign: "center",
        maxWidth: 360,
        margin: "12px auto",
      }}
    >
      <span
        style={{
          fontSize: 13,
          fontWeight: 600,
          color: "#c084fc",
          textTransform: "uppercase",
          letterSpacing: "1px",
          marginBottom: 6,
        }}
      >
        {displayTitle.replace(/_/g, " ")}
      </span>
      <div
        data-testid="number-card-value"
        style={{
          fontSize: 38,
          fontWeight: 800,
          background: "linear-gradient(135deg, #ffffff 0%, #e2e8f0 50%, #c084fc 100%)",
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent",
          letterSpacing: "-1px",
          lineHeight: 1.2,
        }}
      >
        {formatNumber(value)}
      </div>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* 2. Bar Chart Component                                                     */
/* -------------------------------------------------------------------------- */
function BarChart({ data, title }: { data: ChartData; title?: string }) {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  const labels = data.labels || [];
  const seriesData = data.series?.[0]?.data || [];

  if (labels.length === 0 || seriesData.length === 0) return null;

  const maxVal = Math.max(...seriesData, 1);
  const chartHeight = 220;
  const barWidth = Math.max(16, Math.min(48, Math.floor(400 / labels.length) - 10));

  return (
    <div
      data-testid="bar-chart-container"
      className="glass"
      style={{
        padding: "16px 20px",
        borderRadius: 12,
        background: "rgba(15, 23, 42, 0.8)",
        border: "1px solid rgba(139, 92, 246, 0.25)",
        margin: "12px 0",
      }}
    >
      {title && (
        <div style={{ fontSize: 14, fontWeight: 700, color: "#f1f5f9", marginBottom: 14 }}>
          {title}
        </div>
      )}

      {/* SVG Bar Chart */}
      <div style={{ width: "100%", overflowX: "auto" }}>
        <svg
          viewBox={`0 0 ${Math.max(500, labels.length * 70)} ${chartHeight + 60}`}
          style={{ width: "100%", height: "260px", minWidth: "450px" }}
        >
          <defs>
            <linearGradient id="barGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#c084fc" />
              <stop offset="100%" stopColor="#6366f1" />
            </linearGradient>
            <linearGradient id="barGradHover" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#f472b6" />
              <stop offset="100%" stopColor="#a855f7" />
            </linearGradient>
          </defs>

          {/* Grid lines */}
          {[0, 0.25, 0.5, 0.75, 1].map((pct, idx) => {
            const y = chartHeight * (1 - pct) + 20;
            const gridVal = (maxVal * pct);
            return (
              <g key={idx}>
                <line
                  x1="50"
                  y1={y}
                  x2={Math.max(500, labels.length * 70) - 20}
                  y2={y}
                  stroke="rgba(255,255,255,0.08)"
                  strokeDasharray="4 4"
                />
                <text x="40" y={y + 4} fill="#64748b" fontSize="10" textAnchor="end">
                  {formatNumber(gridVal)}
                </text>
              </g>
            );
          })}

          {/* Bars */}
          {labels.map((label, idx) => {
            const val = seriesData[idx] ?? 0;
            const barHeight = Math.max(4, (val / maxVal) * chartHeight);
            const x = 70 + idx * Math.max(65, (400 / labels.length));
            const y = chartHeight - barHeight + 20;
            const isHovered = hoveredIdx === idx;

            return (
              <g
                key={idx}
                onMouseEnter={() => setHoveredIdx(idx)}
                onMouseLeave={() => setHoveredIdx(null)}
                style={{ cursor: "pointer" }}
              >
                <rect
                  x={x - barWidth / 2}
                  y={y}
                  width={barWidth}
                  height={barHeight}
                  rx="4"
                  fill={isHovered ? "url(#barGradHover)" : "url(#barGrad)"}
                  filter={isHovered ? "drop-shadow(0 0 8px rgba(192, 132, 252, 0.6))" : undefined}
                />

                {/* Value on top of bar if hovered */}
                {isHovered && (
                  <text
                    x={x}
                    y={y - 6}
                    fill="#f8fafc"
                    fontSize="11"
                    fontWeight="700"
                    textAnchor="middle"
                  >
                    {formatNumber(val)}
                  </text>
                )}

                {/* X Axis Label */}
                <text
                  x={x}
                  y={chartHeight + 40}
                  fill={isHovered ? "#c084fc" : "#94a3b8"}
                  fontSize="11"
                  fontWeight={isHovered ? "700" : "500"}
                  textAnchor="middle"
                >
                  {label.length > 10 ? label.slice(0, 9) + "…" : label}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* 3. Line Chart Component                                                    */
/* -------------------------------------------------------------------------- */
function LineChart({ data, title }: { data: ChartData; title?: string }) {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  const labels = data.labels || [];
  const seriesData = data.series?.[0]?.data || [];

  if (labels.length === 0 || seriesData.length === 0) return null;

  const maxVal = Math.max(...seriesData, 1);
  const minVal = Math.min(...seriesData, 0);
  const range = maxVal - minVal || 1;
  const chartHeight = 200;
  const totalWidth = Math.max(500, labels.length * 70);

  const points = labels.map((_, idx) => {
    const val = seriesData[idx] ?? 0;
    const x = 70 + idx * ((totalWidth - 120) / Math.max(1, labels.length - 1));
    const y = chartHeight - ((val - minVal) / range) * (chartHeight - 40) + 20;
    return { x, y, val };
  });

  const pathD = points.reduce((acc, p, idx) => (idx === 0 ? `M ${p.x} ${p.y}` : `${acc} L ${p.x} ${p.y}`), "");
  const areaD = `${pathD} L ${points[points.length - 1].x} ${chartHeight + 20} L ${points[0].x} ${chartHeight + 20} Z`;

  return (
    <div
      data-testid="line-chart-container"
      className="glass"
      style={{
        padding: "16px 20px",
        borderRadius: 12,
        background: "rgba(15, 23, 42, 0.8)",
        border: "1px solid rgba(139, 92, 246, 0.25)",
        margin: "12px 0",
      }}
    >
      {title && (
        <div style={{ fontSize: 14, fontWeight: 700, color: "#f1f5f9", marginBottom: 14 }}>
          {title}
        </div>
      )}

      <div style={{ width: "100%", overflowX: "auto" }}>
        <svg viewBox={`0 0 ${totalWidth} ${chartHeight + 60}`} style={{ width: "100%", height: "260px", minWidth: "450px" }}>
          <defs>
            <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="rgba(192, 132, 252, 0.4)" />
              <stop offset="100%" stopColor="rgba(99, 102, 241, 0.0)" />
            </linearGradient>
          </defs>

          {/* Area under line */}
          <path d={areaD} fill="url(#areaGrad)" />

          {/* Line path */}
          <path d={pathD} fill="none" stroke="#c084fc" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />

          {/* Points */}
          {points.map((p, idx) => {
            const isHovered = hoveredIdx === idx;
            return (
              <g
                key={idx}
                onMouseEnter={() => setHoveredIdx(idx)}
                onMouseLeave={() => setHoveredIdx(null)}
                style={{ cursor: "pointer" }}
              >
                <circle
                  cx={p.x}
                  cy={p.y}
                  r={isHovered ? 6 : 4}
                  fill={isHovered ? "#f472b6" : "#c084fc"}
                  stroke="#ffffff"
                  strokeWidth={isHovered ? 2 : 1.5}
                />

                {isHovered && (
                  <text x={p.x} y={p.y - 10} fill="#f8fafc" fontSize="11" fontWeight="700" textAnchor="middle">
                    {formatNumber(p.val)}
                  </text>
                )}

                <text x={p.x} y={chartHeight + 40} fill={isHovered ? "#c084fc" : "#94a3b8"} fontSize="11" textAnchor="middle">
                  {labels[idx]}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* 4. Pie / Donut Chart Component                                             */
/* -------------------------------------------------------------------------- */
function PieChart({ data, title }: { data: ChartData; title?: string }) {
  const labels = data.labels || [];
  const seriesData = data.series?.[0]?.data || [];

  if (labels.length === 0 || seriesData.length === 0) return null;

  const total = seriesData.reduce((acc, curr) => acc + curr, 0) || 1;
  const radius = 70;
  const centerX = 90;
  const centerY = 90;

  let cumulativeAngle = 0;
  const slices = seriesData.map((val, idx) => {
    const fraction = val / total;
    const angle = fraction * 2 * Math.PI;
    const startAngle = cumulativeAngle;
    const endAngle = cumulativeAngle + angle;
    cumulativeAngle = endAngle;

    const x1 = centerX + radius * Math.cos(startAngle);
    const y1 = centerY + radius * Math.sin(startAngle);
    const x2 = centerX + radius * Math.cos(endAngle);
    const y2 = centerY + radius * Math.sin(endAngle);
    const largeArc = angle > Math.PI ? 1 : 0;

    const pathData =
      fraction >= 0.999
        ? `M ${centerX} ${centerY - radius} A ${radius} ${radius} 0 1 1 ${centerX - 0.01} ${centerY - radius} Z`
        : `M ${centerX} ${centerY} L ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2} Z`;

    return {
      pathData,
      color: PALETTE[idx % PALETTE.length],
      label: labels[idx] || `Item ${idx + 1}`,
      value: val,
      percentage: ((val / total) * 100).toFixed(1),
    };
  });

  return (
    <div
      data-testid="pie-chart-container"
      className="glass"
      style={{
        padding: "16px 20px",
        borderRadius: 12,
        background: "rgba(15, 23, 42, 0.8)",
        border: "1px solid rgba(139, 92, 246, 0.25)",
        margin: "12px 0",
      }}
    >
      {title && (
        <div style={{ fontSize: 14, fontWeight: 700, color: "#f1f5f9", marginBottom: 14 }}>
          {title}
        </div>
      )}

      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-around", flexWrap: "wrap", gap: 20 }}>
        <svg width="180" height="180" viewBox="0 0 180 180">
          {slices.map((slice, idx) => (
            <path key={idx} d={slice.pathData} fill={slice.color} stroke="rgba(15, 23, 42, 0.8)" strokeWidth="2" />
          ))}
        </svg>

        {/* Legend */}
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          {slices.map((slice, idx) => (
            <div key={idx} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12 }}>
              <span
                style={{
                  width: 10,
                  height: 10,
                  borderRadius: 2,
                  backgroundColor: slice.color,
                  display: "inline-block",
                }}
              />
              <span style={{ color: "#e2e8f0", fontWeight: 500 }}>{slice.label}</span>
              <span style={{ color: "#94a3b8" }}>({slice.percentage}%)</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Main ResultChart Export                                                    */
/* -------------------------------------------------------------------------- */
export function ResultChart({ chart_type, chart_data, title }: ResultChartProps) {
  if (!chart_type || !chart_data) {
    return null;
  }

  const normalizedType = chart_type.toLowerCase().trim();

  switch (normalizedType) {
    case "number_card":
      return <NumberCard data={chart_data} title={title} />;
    case "bar":
      return <BarChart data={chart_data} title={title} />;
    case "line":
      return <LineChart data={chart_data} title={title} />;
    case "pie":
      return <PieChart data={chart_data} title={title} />;
    default:
      // When chart_type is "table" or unrecognized, do not render a chart
      return null;
  }
}

export default ResultChart;
