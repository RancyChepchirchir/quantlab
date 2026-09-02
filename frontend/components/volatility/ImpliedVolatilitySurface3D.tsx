"use client";

import { useMemo } from "react";

import Surface3D from "@/components/charts/Surface3D";
import type { VolatilitySurfaceGrid } from "@/lib/api/volatility";

type ImpliedVolatilitySurface3DProps = {
  surfaceGrid: VolatilitySurfaceGrid;
};

export default function ImpliedVolatilitySurface3D({
  surfaceGrid,
}: ImpliedVolatilitySurface3DProps) {
  const surface = useMemo(() => {
    const strikes = [...surfaceGrid.strikes].sort((a, b) => a - b);
    const maturities = [...surfaceGrid.maturities].sort(
      (a, b) => a - b
    );

    const pointMap = new Map<string, number>();

    for (const point of surfaceGrid.points) {
      const key = `${point.strike}|${point.maturity}`;

      pointMap.set(
        key,
        point.implied_volatility_percent
      );
    }

    const z = maturities.map((maturity) =>
      strikes.map((strike) => {
        const key = `${strike}|${maturity}`;

        const value = pointMap.get(key);

        return value ?? Number.NaN;
      })
    );

    const finiteValues = z
      .flat()
      .filter((value) => Number.isFinite(value));

    const minIv =
      finiteValues.length > 0
        ? Math.min(...finiteValues)
        : null;

    const maxIv =
      finiteValues.length > 0
        ? Math.max(...finiteValues)
        : null;

    return {
      strikes,
      maturities,
      z,
      minIv,
      maxIv,
    };
  }, [surfaceGrid]);

  if (
    surface.strikes.length === 0 ||
    surface.maturities.length === 0
  ) {
    return (
      <div className="ql-card">
        <p className="ql-card-title">
          Implied Volatility Surface
        </p>

        <p className="ql-card-subtitle">
          No calibrated surface data is available.
        </p>
      </div>
    );
  }

  return (
    <section className="ql-chart-card">
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          gap: "1rem",
          marginBottom: "0.75rem",
          flexWrap: "wrap",
        }}
      >
        <div>
          <p className="ql-page-kicker">
            Market Geometry
          </p>

          <h2 className="ql-card-title">
            Implied Volatility Surface
          </h2>

          <p className="ql-card-subtitle">
            Interactive strike × maturity × implied-volatility
            geometry reconstructed from the calibrated grid.
          </p>
        </div>

        <div
          style={{
            display: "flex",
            gap: "0.75rem",
            flexWrap: "wrap",
          }}
        >
          <div className="ql-kpi">
            <div className="ql-kpi-label">
              Strikes
            </div>

            <div className="ql-kpi-value">
              {surface.strikes.length}
            </div>
          </div>

          <div className="ql-kpi">
            <div className="ql-kpi-label">
              Maturities
            </div>

            <div className="ql-kpi-value">
              {surface.maturities.length}
            </div>
          </div>

          <div className="ql-kpi">
            <div className="ql-kpi-label">
              IV Range
            </div>

            <div className="ql-kpi-value">
              {surface.minIv !== null &&
              surface.maxIv !== null
                ? `${surface.minIv.toFixed(
                    2
                  )}%–${surface.maxIv.toFixed(2)}%`
                : "—"}
            </div>
          </div>
        </div>
      </div>

      <Surface3D
        x={surface.strikes}
        y={surface.maturities}
        z={surface.z}
        xTitle="Strike K"
        yTitle="Maturity T"
        zTitle="Implied Volatility (%)"
        height={520}
        hoverTemplate={
          "Strike: %{x:.2f}<br>" +
          "Maturity: %{y:.4f} years<br>" +
          "Implied volatility: %{z:.2f}%<extra></extra>"
        }
      />

      <div className="ql-divider" />

      <p className="ql-card-subtitle">
        Each horizontal maturity slice corresponds to an implied-volatility
        smile. Moving across maturities reveals how the smile evolves through
        the term structure.
      </p>
    </section>
  );
}