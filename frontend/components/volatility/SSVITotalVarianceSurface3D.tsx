"use client";

import { useMemo } from "react";

import Surface3D from "@/components/charts/Surface3D";
import type { SSVISurface } from "@/lib/api/volatility";

type SSVITotalVarianceSurface3DProps = {
  ssviSurface: SSVISurface;
};

export default function SSVITotalVarianceSurface3D({
  ssviSurface,
}: SSVITotalVarianceSurface3DProps) {
  const surface = useMemo(() => {
    if (
      !ssviSurface.available ||
      !ssviSurface.parameters ||
      ssviSurface.points.length === 0
    ) {
      return null;
    }

    const maturities = Array.from(
      new Set(
        ssviSurface.points.map(
          (point) => point.maturity
        )
      )
    ).sort((a, b) => a - b);

    const logMoneynessValues = Array.from(
      new Set(
        ssviSurface.points.map(
          (point) =>
            point.log_forward_moneyness
        )
      )
    ).sort((a, b) => a - b);

    /*
     * SSVI points may not necessarily form a perfectly rectangular
     * (k, T) grid. We therefore reconstruct the matrix using the
     * exact backend coordinates and leave unavailable cells as NaN.
     */
    const pointMap = new Map<
      string,
      number
    >();

    for (const point of ssviSurface.points) {
      const key =
        `${point.log_forward_moneyness}|${point.maturity}`;

      pointMap.set(
        key,
        point.fitted_total_variance
      );
    }

    const z = maturities.map(
      (maturity) =>
        logMoneynessValues.map(
          (logMoneyness) => {
            const key =
              `${logMoneyness}|${maturity}`;

            return (
              pointMap.get(key) ??
              Number.NaN
            );
          }
        )
    );

    const finiteValues = z
      .flat()
      .filter((value) =>
        Number.isFinite(value)
      );

    return {
      maturities,
      logMoneynessValues,
      z,

      minTotalVariance:
        finiteValues.length > 0
          ? Math.min(...finiteValues)
          : null,

      maxTotalVariance:
        finiteValues.length > 0
          ? Math.max(...finiteValues)
          : null,

      parameters:
        ssviSurface.parameters,
    };
  }, [ssviSurface]);

  if (!surface) {
    return (
      <section className="ql-chart-card">
        <p className="ql-page-kicker">
          Parametric Surface
        </p>

        <h2 className="ql-card-title">
          SSVI Total Variance
        </h2>

        <p className="ql-card-subtitle">
          A fitted SSVI surface is not available
          for the current calibration.
        </p>
      </section>
    );
  }

  const {
    parameters,
  } = surface;

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
            Parametric Geometry
          </p>

          <h2 className="ql-card-title">
            SSVI Total Variance Surface
          </h2>

          <p className="ql-card-subtitle">
            Shared cross-maturity model in
            forward log-moneyness space.
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
              η
            </div>

            <div className="ql-kpi-value">
              {parameters.eta.toFixed(4)}
            </div>
          </div>

          <div className="ql-kpi">
            <div className="ql-kpi-label">
              ρ
            </div>

            <div className="ql-kpi-value">
              {parameters.rho.toFixed(4)}
            </div>
          </div>

          <div className="ql-kpi">
            <div className="ql-kpi-label">
              γ
            </div>

            <div className="ql-kpi-value">
              {parameters.gamma.toFixed(4)}
            </div>
          </div>

          <div className="ql-kpi">
            <div className="ql-kpi-label">
              RMSE
            </div>

            <div className="ql-kpi-value">
              {parameters.rmse.toExponential(2)}
            </div>
          </div>
        </div>
      </div>

      <Surface3D
        x={surface.logMoneynessValues}
        y={surface.maturities}
        z={surface.z}
        xTitle="Log-forward moneyness k"
        yTitle="Maturity T"
        zTitle="Total Variance w"
        height={520}
        hoverTemplate={
          "k: %{x:.4f}<br>" +
          "Maturity: %{y:.4f} years<br>" +
          "Total variance: %{z:.6f}<extra></extra>"
        }
      />

      <div className="ql-divider" />

      <p className="ql-card-subtitle">
        SSVI models total implied variance rather
        than volatility directly. The centre of
        the surface corresponds approximately to
        ATM forward moneyness, while movement
        away from k = 0 exposes the fitted smile
        geometry.
      </p>
    </section>
  );
}