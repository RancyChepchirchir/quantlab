type VolatilityKpiStripProps = {
  inputCount: number;
  calibratedCount: number;
  rejectedCount: number;

  minIv: number | null;
  maxIv: number | null;
  atmIv: number | null;

  ssviRmse: number | null;
};

type KpiItemProps = {
  label: string;
  value: string;
  detail?: string;
  accent?: "default" | "positive" | "warning" | "info";
};

function KpiItem({
  label,
  value,
  detail,
  accent = "default",
}: KpiItemProps) {
  const accentClass =
    accent === "positive"
      ? "ql-positive"
      : accent === "warning"
        ? "ql-negative"
        : accent === "info"
          ? "ql-info"
          : "ql-accent";

  return (
    <div className="ql-kpi">
      <div className="ql-kpi-label">
        {label}
      </div>

      <div
        className={`ql-kpi-value ${accentClass}`}
      >
        {value}
      </div>

      {detail && (
        <div className="ql-kpi-detail">
          {detail}
        </div>
      )}
    </div>
  );
}

export default function VolatilityKpiStrip({
  inputCount,
  calibratedCount,
  rejectedCount,
  minIv,
  maxIv,
  atmIv,
  ssviRmse,
}: VolatilityKpiStripProps) {
  const successRate =
    inputCount > 0
      ? (calibratedCount / inputCount) * 100
      : null;

  const ivRange =
    minIv !== null && maxIv !== null
      ? `${minIv.toFixed(2)}%–${maxIv.toFixed(2)}%`
      : "—";

  const atmIvDisplay =
    atmIv !== null
      ? `${atmIv.toFixed(2)}%`
      : "—";

  const ssviRmseDisplay =
    ssviRmse !== null
      ? ssviRmse.toExponential(2)
      : "—";

  return (
    <section
      className="ql-kpi-grid"
      style={{
        marginBottom: "1.5rem",
      }}
    >
      <KpiItem
        label="Input Quotes"
        value={inputCount.toString()}
        detail="Submitted to calibration"
        accent="info"
      />

      <KpiItem
        label="Calibrated"
        value={calibratedCount.toString()}
        detail="Valid implied volatilities"
        accent="positive"
      />

      <KpiItem
        label="Rejected"
        value={rejectedCount.toString()}
        detail="Failed inversion / validation"
        accent={
          rejectedCount > 0
            ? "warning"
            : "positive"
        }
      />

      <KpiItem
        label="Success Rate"
        value={
          successRate !== null
            ? `${successRate.toFixed(1)}%`
            : "—"
        }
        detail="Calibration efficiency"
        accent={
          successRate !== null &&
          successRate >= 90
            ? "positive"
            : "default"
        }
      />

      <KpiItem
        label="ATM IV"
        value={atmIvDisplay}
        detail="Nearest calibrated strike"
      />

      <KpiItem
        label="IV Range"
        value={ivRange}
        detail="Observed calibrated range"
      />

      <KpiItem
        label="SSVI RMSE"
        value={ssviRmseDisplay}
        detail="Cross-maturity fit error"
        accent="info"
      />
    </section>
  );
}