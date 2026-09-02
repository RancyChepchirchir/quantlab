"use client";

import dynamic from "next/dynamic";

import {
  AmericanSurfaceAtlasResult,
} from "@/lib/api/americanSurfaceAtlas";


const Plot = dynamic(
  () => import("react-plotly.js"),
  {
    ssr: false,
  }
);


type Props = {
  data: AmericanSurfaceAtlasResult;
};


type BoundaryDiagnostic =
  AmericanSurfaceAtlasResult[
    "pinn_convergence"
  ][
    "boundary_diagnostics"
  ][string];


export default function FreeBoundaryDifficulty({
  data,
}: Props) {
  const convergence =
    data.pinn_convergence;

  const epochs =
    convergence.epochs;

  const diagnostics =
    convergence.boundary_diagnostics;


  if (
    !convergence.available ||
    epochs.length === 0 ||
    Object.keys(
      diagnostics
    ).length === 0
  ) {
    return null;
  }


  const rows =
    epochs
      .map(
        (epoch) => ({
          epoch,

          diagnostic:
            diagnostics[
              String(epoch)
            ],
        })
      )
      .filter(
        (
          item
        ): item is {
          epoch: number;
          diagnostic:
            BoundaryDiagnostic;
        } =>
          Boolean(
            item.diagnostic
          )
      );


  if (
    rows.length === 0
  ) {
    return null;
  }


  const first =
    rows[0];

  const last =
    rows[
      rows.length - 1
    ];


  const lastRatio =
    last.diagnostic
      .near_to_away_mae_ratio;


  const interpretation =
    ratioInterpretation(
      lastRatio
    );


  return (
    <section
      style={{
        display: "grid",
        gap: 14,
      }}
    >
      <header
        className="ql-card"
        style={{
          padding:
            "20px 22px",

          background:
            "radial-gradient(circle at 90% 0%, rgba(244,63,94,0.10), transparent 34%), radial-gradient(circle at 12% 100%, rgba(34,211,238,0.08), transparent 36%)",
        }}
      >
        <div
          style={{
            display: "flex",

            justifyContent:
              "space-between",

            gap: 28,

            flexWrap:
              "wrap",

            alignItems:
              "flex-end",
          }}
        >
          <div>
            <div
              style={{
                color:
                  "#fb7185",

                fontSize: 9,

                fontWeight: 800,

                letterSpacing:
                  "0.15em",

                textTransform:
                  "uppercase",
              }}
            >
              American Exercise Geometry
            </div>

            <h2
              style={{
                margin:
                  "5px 0 6px",

                fontSize: 22,
              }}
            >
              Free-Boundary Difficulty
            </h2>

            <p
              style={{
                margin: 0,

                maxWidth: 760,

                color:
                  "#94a3b8",

                fontSize: 11,

                lineHeight: 1.65,
              }}
            >
              Tests whether the
              PINN pricing error is
              disproportionately
              concentrated near the
              estimated American
              stopping boundary.
            </p>
          </div>


          <div
            style={{
              padding:
                "9px 12px",

              borderRadius: 10,

              border:
                "1px solid rgba(244,63,94,0.22)",

              background:
                "rgba(244,63,94,0.06)",
            }}
          >
            <div
              style={{
                color:
                  "#64748b",

                fontSize: 8,

                letterSpacing:
                  "0.1em",

                textTransform:
                  "uppercase",
              }}
            >
              Boundary Band
            </div>

            <strong
              style={{
                display:
                  "block",

                marginTop: 3,

                color:
                  "#fecdd3",

                fontSize: 15,
              }}
            >
              ±
              {last.diagnostic
                .band_width
                .toFixed(2)}
            </strong>
          </div>
        </div>
      </header>


      <SummaryStrip
        first={first}
        last={last}
      />


      <div
        style={{
          display: "grid",

          gridTemplateColumns:
            "minmax(0, 1.35fr) minmax(280px, 0.65fr)",

          gap: 12,
        }}
        className="boundary-difficulty-grid"
      >
        <BoundaryRatioChart
          rows={rows}
        />

        <InterpretationCard
          ratio={lastRatio}
          interpretation={
            interpretation
          }
          diagnostic={
            last.diagnostic
          }
          epoch={
            last.epoch
          }
        />
      </div>


      <div
        style={{
          display: "grid",

          gridTemplateColumns:
            "repeat(auto-fit, minmax(220px, 1fr))",

          gap: 10,
        }}
      >
        {rows.map(
          ({
            epoch,
            diagnostic,
          }) => (
            <EpochDiagnosticCard
              key={epoch}
              epoch={epoch}
              diagnostic={
                diagnostic
              }
            />
          )
        )}
      </div>


      <WorstErrorLocations
        epoch={last.epoch}
        diagnostic={
          last.diagnostic
        }
      />


      <ResearchInterpretation
        first={first}
        last={last}
      />
    </section>
  );
}


function SummaryStrip({
  first,
  last,
}: {
  first: {
    epoch: number;
    diagnostic:
      BoundaryDiagnostic;
  };

  last: {
    epoch: number;
    diagnostic:
      BoundaryDiagnostic;
  };
}) {
  const firstRatio =
    first.diagnostic
      .near_to_away_mae_ratio;

  const lastRatio =
    last.diagnostic
      .near_to_away_mae_ratio;


  const ratioChange =
    firstRatio !== null &&
    firstRatio !== 0 &&
    lastRatio !== null
      ? (
          (
            lastRatio
            - firstRatio
          )
          / firstRatio
        )
        * 100
      : null;


  const nearMae =
    last.diagnostic
      .near_boundary.mae;

  const awayMae =
    last.diagnostic
      .away_from_boundary.mae;


  const cards = [
    {
      label:
        `${first.epoch} Epoch Ratio`,

      value:
        formatNumber(
          firstRatio
        ),
    },

    {
      label:
        `${last.epoch} Epoch Ratio`,

      value:
        formatNumber(
          lastRatio
        ),
    },

    {
      label:
        "Ratio Change",

      value:
        ratioChange === null
          ? "—"
          : `${ratioChange > 0 ? "+" : ""}${ratioChange.toFixed(
              1
            )}%`,
    },

    {
      label:
        "Near-Boundary MAE",

      value:
        formatNumber(
          nearMae,
          6
        ),
    },

    {
      label:
        "Away MAE",

      value:
        formatNumber(
          awayMae,
          6
        ),
    },

    {
      label:
        "Boundary Band",

      value:
        `±${last.diagnostic.band_width.toFixed(
          2
        )}`,
    },
  ];


  return (
    <div
      style={{
        display: "grid",

        gridTemplateColumns:
          "repeat(auto-fit, minmax(135px, 1fr))",

        gap: 8,
      }}
    >
      {cards.map(
        (card) => (
          <div
            key={
              card.label
            }
            className="ql-card"
            style={{
              padding:
                "11px 13px",
            }}
          >
            <div
              style={{
                color:
                  "#64748b",

                fontSize: 8,

                textTransform:
                  "uppercase",

                letterSpacing:
                  "0.08em",
              }}
            >
              {card.label}
            </div>

            <div
              style={{
                marginTop: 4,

                color:
                  "#e2e8f0",

                fontSize: 13,

                fontWeight: 750,
              }}
            >
              {card.value}
            </div>
          </div>
        )
      )}
    </div>
  );
}


function BoundaryRatioChart({
  rows,
}: {
  rows: Array<{
    epoch: number;
    diagnostic:
      BoundaryDiagnostic;
  }>;
}) {
  const epochs =
    rows.map(
      (item) =>
        item.epoch
    );

  const ratios =
    rows.map(
      (item) =>
        item.diagnostic
          .near_to_away_mae_ratio
    );

  const nearMae =
    rows.map(
      (item) =>
        item.diagnostic
          .near_boundary.mae
    );

  const awayMae =
    rows.map(
      (item) =>
        item.diagnostic
          .away_from_boundary.mae
    );


  return (
    <article
      className="ql-card"
      style={{
        padding:
          "15px 17px 5px",
      }}
    >
      <div
        style={{
          color:
            "#22d3ee",

          fontSize: 8,

          fontWeight: 800,

          textTransform:
            "uppercase",

          letterSpacing:
            "0.12em",
        }}
      >
        Boundary Concentration
      </div>

      <h3
        style={{
          margin:
            "4px 0 0",

          fontSize: 15,
        }}
      >
        Near vs Away Error
        Through Training
      </h3>


      <Plot
        data={[
          {
            type:
              "scatter",

            mode:
              "lines+markers",

            x: epochs,

            y:
              ratios,

            name:
              "Near / Away MAE",

            yaxis:
              "y",

            line: {
              width: 3,
            },

            marker: {
              size: 8,
            },

            hovertemplate:
              "Epoch=%{x}<br>" +
              "Ratio=%{y:.4f}" +
              "<extra></extra>",
          },

          {
            type:
              "scatter",

            mode:
              "lines+markers",

            x: epochs,

            y:
              nearMae,

            name:
              "Near MAE",

            yaxis:
              "y2",

            line: {
              width: 2,
            },

            marker: {
              size: 6,
            },
          },

          {
            type:
              "scatter",

            mode:
              "lines+markers",

            x: epochs,

            y:
              awayMae,

            name:
              "Away MAE",

            yaxis:
              "y2",

            line: {
              width: 2,

              dash:
                "dot",
            },

            marker: {
              size: 6,
            },
          },
        ]}
        layout={{
          autosize: true,

          height: 350,

          margin: {
            l: 62,
            r: 65,
            t: 38,
            b: 55,
          },

          paper_bgcolor:
            "rgba(0,0,0,0)",

          plot_bgcolor:
            "rgba(0,0,0,0)",

          font: {
            color:
              "#cbd5e1",

            size: 9,
          },

          xaxis: {
            title: {
              text:
                "Training Epoch",
            },

            gridcolor:
              "rgba(148,163,184,0.10)",
          },

          yaxis: {
            title: {
              text:
                "MAE Ratio",
            },

            gridcolor:
              "rgba(148,163,184,0.10)",
          },

          yaxis2: {
            title: {
              text:
                "Absolute Error",
            },

            overlaying:
              "y",

            side:
              "right",

            showgrid:
              false,
          },

          shapes: [
            {
              type:
                "line",

              x0:
                Math.min(
                  ...epochs
                ),

              x1:
                Math.max(
                  ...epochs
                ),

              y0: 1,

              y1: 1,

              line: {
                width: 1,

                dash:
                  "dot",

                color:
                  "rgba(148,163,184,0.55)",
              },
            },
          ],

          annotations: [
            {
              x:
                Math.max(
                  ...epochs
                ),

              y: 1,

              text:
                "equal-error threshold",

              showarrow:
                false,

              xanchor:
                "right",

              yshift: 11,

              font: {
                size: 8,

                color:
                  "#64748b",
              },
            },
          ],

          legend: {
            orientation:
              "h",

            x: 0,

            y: 1.15,
          },
        }}
        config={{
          responsive: true,

          displaylogo: false,
        }}
        style={{
          width: "100%",
        }}
      />
    </article>
  );
}


function InterpretationCard({
  ratio,
  interpretation,
  diagnostic,
  epoch,
}: {
  ratio: number | null;

  interpretation: {
    title: string;
    text: string;
  };

  diagnostic:
    BoundaryDiagnostic;

  epoch: number;
}) {
  return (
    <article
      className="ql-card"
      style={{
        padding:
          "18px 19px",
      }}
    >
      <div
        style={{
          color:
            "#fb7185",

          fontSize: 8,

          fontWeight: 800,

          letterSpacing:
            "0.12em",

          textTransform:
            "uppercase",
        }}
      >
        {epoch.toLocaleString()}
        {" "}Epoch Interpretation
      </div>

      <div
        style={{
          margin:
            "14px 0 4px",

          fontSize: 38,

          lineHeight: 1,

          fontWeight: 850,

          color:
            "#f8fafc",
        }}
      >
        {ratio === null
          ? "—"
          : ratio.toFixed(
              3
            )}
        <span
          style={{
            marginLeft: 6,

            fontSize: 12,

            color:
              "#64748b",
          }}
        >
          ×
        </span>
      </div>

      <div
        style={{
          marginBottom: 13,

          color:
            "#cbd5e1",

          fontSize: 13,

          fontWeight: 750,
        }}
      >
        {interpretation.title}
      </div>

      <p
        style={{
          margin: 0,

          color:
            "#64748b",

          fontSize: 11,

          lineHeight: 1.7,
        }}
      >
        {interpretation.text}
      </p>


      <div
        style={{
          height: 1,

          margin:
            "17px 0",

          background:
            "rgba(148,163,184,0.10)",
        }}
      />


      <MetricRow
        label=
          "Near samples"
        value={
          diagnostic
            .near_boundary
            .count
            .toLocaleString()
        }
      />

      <MetricRow
        label=
          "Away samples"
        value={
          diagnostic
            .away_from_boundary
            .count
            .toLocaleString()
        }
      />

      <MetricRow
        label=
          "Near max error"
        value={
          formatNumber(
            diagnostic
              .near_boundary
              .max_absolute_error,
            6
          )
        }
      />

      <MetricRow
        label=
          "Away max error"
        value={
          formatNumber(
            diagnostic
              .away_from_boundary
              .max_absolute_error,
            6
          )
        }
      />
    </article>
  );
}


function EpochDiagnosticCard({
  epoch,
  diagnostic,
}: {
  epoch: number;

  diagnostic:
    BoundaryDiagnostic;
}) {
  const ratio =
    diagnostic
      .near_to_away_mae_ratio;


  return (
    <article
      className="ql-card"
      style={{
        padding:
          "14px 15px",
      }}
    >
      <div
        style={{
          display: "flex",

          justifyContent:
            "space-between",

          gap: 12,

          alignItems:
            "baseline",
        }}
      >
        <div>
          <div
            style={{
              color:
                "#a78bfa",

              fontSize: 8,

              fontWeight: 800,

              letterSpacing:
                "0.1em",

              textTransform:
                "uppercase",
            }}
          >
            Snapshot
          </div>

          <strong
            style={{
              display:
                "block",

              marginTop: 3,

              fontSize: 15,
            }}
          >
            {epoch.toLocaleString()}
            {" "}epochs
          </strong>
        </div>

        <div
          style={{
            color:
              ratio !== null &&
              ratio > 1
                ? "#fb7185"
                : "#34d399",

            fontSize: 18,

            fontWeight: 800,
          }}
        >
          {ratio === null
            ? "—"
            : ratio.toFixed(
                2
              )}
          ×
        </div>
      </div>


      <div
        style={{
          height: 1,

          margin:
            "12px 0",

          background:
            "rgba(148,163,184,0.08)",
        }}
      />


      <MetricRow
        label="Near MAE"
        value={
          formatNumber(
            diagnostic
              .near_boundary.mae,
            6
          )
        }
      />

      <MetricRow
        label="Away MAE"
        value={
          formatNumber(
            diagnostic
              .away_from_boundary
              .mae,
            6
          )
        }
      />

      <MetricRow
        label="Near RMSE"
        value={
          formatNumber(
            diagnostic
              .near_boundary
              .rmse,
            6
          )
        }
      />
    </article>
  );
}


function WorstErrorLocations({
  epoch,
  diagnostic,
}: {
  epoch: number;

  diagnostic:
    BoundaryDiagnostic;
}) {
  return (
    <div
      style={{
        display: "grid",

        gridTemplateColumns:
          "repeat(auto-fit, minmax(280px, 1fr))",

        gap: 10,
      }}
    >
      <LocationCard
        eyebrow="Worst Near Boundary"
        title={`${epoch.toLocaleString()} Epoch PINN`}
        location={
          diagnostic
            .worst_near_boundary
        }
      />

      <LocationCard
        eyebrow="Worst Away From Boundary"
        title={`${epoch.toLocaleString()} Epoch PINN`}
        location={
          diagnostic
            .worst_away_from_boundary
        }
      />
    </div>
  );
}


function LocationCard({
  eyebrow,
  title,
  location,
}: {
  eyebrow: string;
  title: string;

  location:
    BoundaryDiagnostic[
      "worst_near_boundary"
    ];
}) {
  return (
    <article
      className="ql-card"
      style={{
        padding:
          "15px 17px",
      }}
    >
      <div
        style={{
          color:
            "#22d3ee",

          fontSize: 8,

          fontWeight: 800,

          letterSpacing:
            "0.11em",

          textTransform:
            "uppercase",
        }}
      >
        {eyebrow}
      </div>

      <h3
        style={{
          margin:
            "4px 0 12px",

          fontSize: 14,
        }}
      >
        {title}
      </h3>


      {location ? (
        <div
          style={{
            display: "grid",

            gridTemplateColumns:
              "repeat(3, 1fr)",

            gap: 8,
          }}
        >
          <Coordinate
            label="Spot"
            value={
              location.spot
                .toFixed(2)
            }
          />

          <Coordinate
            label="τ"
            value={
              location
                .time_to_maturity
                .toFixed(3)
            }
          />

          <Coordinate
            label="Boundary"
            value={
              location
                .boundary_spot
                .toFixed(2)
            }
          />

          <Coordinate
            label="Distance"
            value={
              location
                .distance_to_boundary
                .toFixed(3)
            }
          />

          <Coordinate
            label="|Error|"
            value={
              location
                .absolute_error
                .toFixed(6)
            }
          />
        </div>
      ) : (
        <span
          style={{
            color:
              "#64748b",

            fontSize: 11,
          }}
        >
          No valid location.
        </span>
      )}
    </article>
  );
}


function Coordinate({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div>
      <div
        style={{
          color:
            "#64748b",

          fontSize: 7,

          letterSpacing:
            "0.08em",

          textTransform:
            "uppercase",
        }}
      >
        {label}
      </div>

      <div
        style={{
          marginTop: 3,

          color:
            "#e2e8f0",

          fontSize: 11,

          fontWeight: 700,
        }}
      >
        {value}
      </div>
    </div>
  );
}


function ResearchInterpretation({
  first,
  last,
}: {
  first: {
    epoch: number;
    diagnostic:
      BoundaryDiagnostic;
  };

  last: {
    epoch: number;
    diagnostic:
      BoundaryDiagnostic;
  };
}) {
  const start =
    first.diagnostic
      .near_to_away_mae_ratio;

  const end =
    last.diagnostic
      .near_to_away_mae_ratio;


  return (
    <article
      className="ql-card"
      style={{
        padding:
          "17px 19px",

        borderLeft:
          "3px solid rgba(139,92,246,0.65)",
      }}
    >
      <div
        style={{
          color:
            "#a78bfa",

          fontSize: 8,

          fontWeight: 800,

          letterSpacing:
            "0.12em",

          textTransform:
            "uppercase",
        }}
      >
        Research Question
      </div>

      <p
        style={{
          margin:
            "7px 0 0",

          color:
            "#94a3b8",

          fontSize: 11,

          lineHeight: 1.75,
        }}
      >
        Does the PINN exhibit
        disproportionately larger
        pricing error near the
        estimated American stopping
        boundary? The diagnostic uses
        the same CN reference and the
        same state-space mesh across
        every training checkpoint.
        The near/away ratio moves from{" "}
        <strong
          style={{
            color:
              "#e2e8f0",
          }}
        >
          {formatNumber(
            start
          )}
        </strong>
        {" "}at{" "}
        {first.epoch.toLocaleString()}
        {" "}epochs to{" "}
        <strong
          style={{
            color:
              "#e2e8f0",
          }}
        >
          {formatNumber(
            end
          )}
        </strong>
        {" "}at{" "}
        {last.epoch.toLocaleString()}
        {" "}epochs. A ratio above one
        supports boundary-localized
        difficulty; a ratio below one
        indicates that larger average
        errors lie elsewhere in the
        state space.
      </p>
    </article>
  );
}


function MetricRow({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div
      style={{
        display: "flex",

        justifyContent:
          "space-between",

        gap: 16,

        padding:
          "6px 0",

        borderBottom:
          "1px solid rgba(148,163,184,0.05)",
      }}
    >
      <span
        style={{
          color:
            "#64748b",

          fontSize: 9,
        }}
      >
        {label}
      </span>

      <strong
        style={{
          color:
            "#e2e8f0",

          fontSize: 10,
        }}
      >
        {value}
      </strong>
    </div>
  );
}


function ratioInterpretation(
  ratio: number | null
) {
  if (ratio === null) {
    return {
      title:
        "Insufficient comparison",

      text:
        "The current grid does not contain enough valid near- and away-boundary observations to form a stable ratio.",
    };
  }

  if (ratio > 1.25) {
    return {
      title:
        "Boundary-localized difficulty",

      text:
        "Average PINN error is materially larger inside the stopping-boundary band than elsewhere. This supports the hypothesis that the free-boundary region is especially difficult for the neural solver.",
    };
  }

  if (ratio > 1.05) {
    return {
      title:
        "Moderate boundary concentration",

      text:
        "The PINN shows somewhat larger average error near the stopping boundary, although the effect is not extreme.",
    };
  }

  if (ratio >= 0.95) {
    return {
      title:
        "Little boundary concentration",

      text:
        "Near-boundary and away-from-boundary errors are of similar magnitude on this experiment.",
    };
  }

  return {
    title:
      "Error concentrated elsewhere",

    text:
      "Average error is lower near the estimated stopping boundary than away from it. The dominant PINN difficulty therefore lies elsewhere in the state space.",
  };
}


function formatNumber(
  value: number | null,
  digits = 3
) {
  if (
    value === null ||
    !Number.isFinite(
      value
    )
  ) {
    return "—";
  }

  return value.toFixed(
    digits
  );
}