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


const AXIS_STYLE = {
  color: "#94a3b8",

  gridcolor:
    "rgba(148,163,184,0.12)",

  zerolinecolor:
    "rgba(148,163,184,0.18)",

  showbackground: true,

  backgroundcolor:
    "rgba(2,6,23,0.30)",
};


const CAMERA = {
  eye: {
    x: 1.45,
    y: -1.55,
    z: 1.0,
  },
};


export default function PinnLearningDynamics({
  data,
}: Props) {
  const convergence =
    data.pinn_convergence;


  if (
    !convergence.available ||
    convergence.epochs.length === 0
  ) {
    return null;
  }


  const epochs =
    convergence.epochs;


  const metrics =
    epochs.map(
      (epoch) => ({
        epoch,

        ...convergence.metrics[
          String(epoch)
        ],
      })
    );


  const globalMaxError =
    Math.max(
      ...metrics.map(
        (metric) =>
          metric.max_absolute_error
      )
    );


  const firstEpoch =
    epochs[0];

  const lastEpoch =
    epochs[
      epochs.length - 1
    ];


  const firstMetrics =
    convergence.metrics[
      String(firstEpoch)
    ];

  const lastMetrics =
    convergence.metrics[
      String(lastEpoch)
    ];


  const rmseChange =
    percentChange(
      firstMetrics.rmse,
      lastMetrics.rmse
    );


  const maeChange =
    percentChange(
      firstMetrics.mae,
      lastMetrics.mae
    );


  const maxErrorChange =
    percentChange(
      firstMetrics
        .max_absolute_error,

      lastMetrics
        .max_absolute_error
    );


  const improvement =
    convergence
      .improvement_surface;


  const improvementAbsMax =
    improvement
      ? matrixAbsoluteMax(
          improvement
        )
      : 0;


  const improvementStats =
    improvement
      ? classifyImprovement(
          improvement
        )
      : null;


  return (
    <section
      style={{
        display: "grid",
        gap: 16,
      }}
    >
      <header
        className="ql-card"
        style={{
          padding:
            "20px 22px",

          background:
            "radial-gradient(circle at 85% 0%, rgba(52,211,153,0.10), transparent 34%), radial-gradient(circle at 15% 100%, rgba(139,92,246,0.10), transparent 35%)",
        }}
      >
        <div
          style={{
            display: "flex",

            justifyContent:
              "space-between",

            gap: 30,

            flexWrap: "wrap",

            alignItems:
              "flex-end",
          }}
        >
          <div>
            <div
              style={{
                color:
                  "#34d399",

                fontSize: 10,

                fontWeight: 800,

                letterSpacing:
                  "0.16em",

                textTransform:
                  "uppercase",
              }}
            >
              Neural Solver Experiment
            </div>

            <h2
              style={{
                margin:
                  "6px 0 6px",

                fontSize: 23,
              }}
            >
              PINN Learning Dynamics
            </h2>

            <p
              style={{
                margin: 0,

                maxWidth: 760,

                color:
                  "#94a3b8",

                fontSize: 12,

                lineHeight: 1.6,
              }}
            >
              Evolution of the PINN V2
              pricing error across the
              full American-option state
              space as optimisation
              progresses from{" "}
              {firstEpoch.toLocaleString()}
              {" "}to{" "}
              {lastEpoch.toLocaleString()}
              {" "}epochs.
            </p>
          </div>


          <div
            style={{
              display: "flex",
              gap: 7,
              flexWrap: "wrap",
            }}
          >
            {epochs.map(
              (epoch) => (
                <span
                  key={epoch}
                  style={{
                    padding:
                      "6px 9px",

                    borderRadius: 999,

                    border:
                      "1px solid rgba(52,211,153,0.25)",

                    background:
                      "rgba(52,211,153,0.07)",

                    color:
                      "#6ee7b7",

                    fontSize: 9,

                    fontWeight: 800,

                    letterSpacing:
                      "0.08em",
                  }}
                >
                  {epoch.toLocaleString()}
                  {" "}EPOCHS
                </span>
              )
            )}
          </div>
        </div>
      </header>


      <SummaryStrip
        firstEpoch={firstEpoch}
        lastEpoch={lastEpoch}
        rmseChange={rmseChange}
        maeChange={maeChange}
        maxErrorChange={
          maxErrorChange
        }
        improvementStats={
          improvementStats
        }
      />


      <SectionHeading
        eyebrow="State-Space Evolution"
        title="Absolute Error Through Training"
        description={
          <>
            All four surfaces share the
            same colour range so their
            heights and intensities are
            directly comparable.
          </>
        }
      />


      <div
        style={{
          display: "grid",

          gridTemplateColumns:
            "repeat(auto-fit, minmax(270px, 1fr))",

          gap: 12,
        }}
      >
        {epochs.map(
          (epoch, index) => {
            const key =
              String(epoch);

            const metric =
              convergence.metrics[
                key
              ];

            return (
              <ErrorSurfaceCard
                key={epoch}
                number={String(
                  index + 1
                ).padStart(
                  2,
                  "0"
                )}
                epoch={epoch}
                x={data.grid.spot}
                y={
                  data.grid
                    .time_to_maturity
                }
                z={
                  convergence
                    .absolute_errors[
                    key
                  ]
                }
                globalMaxError={
                  globalMaxError
                }
                metric={metric}
              />
            );
          }
        )}
      </div>


      <SectionHeading
        eyebrow="Optimisation Diagnostics"
        title="Error Convergence"
        description={
          <>
            Training loss and pricing
            error measure different
            quantities. Their trajectories
            need not move together.
          </>
        }
      />


      <div
        style={{
          display: "grid",

          gridTemplateColumns:
            "minmax(0, 1.4fr) minmax(300px, 0.8fr)",

          gap: 12,
        }}
        className="pinn-dynamics-chart-grid"
      >
        <ErrorConvergenceChart
          metrics={metrics}
        />

        <LossConvergenceChart
          metrics={metrics}
        />
      </div>


      {improvement && (
        <>
          <SectionHeading
            eyebrow="Spatial Learning"
            title={`${firstEpoch.toLocaleString()} → ${lastEpoch.toLocaleString()} Epoch Improvement`}
            description={
              <>
                Positive regions improved
                with training. Negative
                regions deteriorated
                relative to the same
                Crank–Nicolson reference.
              </>
            }
          />


          <div
            style={{
              display: "grid",

              gridTemplateColumns:
                "minmax(0, 1.45fr) minmax(280px, 0.55fr)",

              gap: 12,
            }}
            className="pinn-improvement-grid"
          >
            <ImprovementSurface
              x={data.grid.spot}
              y={
                data.grid
                  .time_to_maturity
              }
              z={improvement}
              absoluteMax={
                improvementAbsMax
              }
              firstEpoch={
                firstEpoch
              }
              lastEpoch={
                lastEpoch
              }
            />

            <ImprovementInterpretation
              stats={
                improvementStats
              }
              firstEpoch={
                firstEpoch
              }
              lastEpoch={
                lastEpoch
              }
              firstMetrics={
                firstMetrics
              }
              lastMetrics={
                lastMetrics
              }
            />
          </div>
        </>
      )}
    </section>
  );
}


function SummaryStrip({
  firstEpoch,
  lastEpoch,
  rmseChange,
  maeChange,
  maxErrorChange,
  improvementStats,
}: {
  firstEpoch: number;
  lastEpoch: number;
  rmseChange: number | null;
  maeChange: number | null;
  maxErrorChange:
    number | null;
  improvementStats:
    ImprovementStats | null;
}) {
  const items = [
    {
      label: "Training Window",
      value:
        `${firstEpoch.toLocaleString()} → ${lastEpoch.toLocaleString()}`,
    },

    {
      label: "RMSE Change",
      value:
        formatPercentChange(
          rmseChange
        ),
    },

    {
      label: "MAE Change",
      value:
        formatPercentChange(
          maeChange
        ),
    },

    {
      label: "Max Error Change",
      value:
        formatPercentChange(
          maxErrorChange
        ),
    },

    {
      label: "Grid Improved",
      value:
        improvementStats
          ? `${improvementStats.improvedPercent.toFixed(
              1
            )}%`
          : "—",
    },

    {
      label: "Grid Worsened",
      value:
        improvementStats
          ? `${improvementStats.worsenedPercent.toFixed(
              1
            )}%`
          : "—",
    },
  ];


  return (
    <div
      style={{
        display: "grid",

        gridTemplateColumns:
          "repeat(auto-fit, minmax(140px, 1fr))",

        gap: 8,
      }}
    >
      {items.map(
        (item) => (
          <div
            key={item.label}
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
                  "0.1em",

                marginBottom: 4,
              }}
            >
              {item.label}
            </div>

            <div
              style={{
                color:
                  "#e2e8f0",

                fontSize: 13,

                fontWeight: 750,
              }}
            >
              {item.value}
            </div>
          </div>
        )
      )}
    </div>
  );
}


function ErrorSurfaceCard({
  number,
  epoch,
  x,
  y,
  z,
  globalMaxError,
  metric,
}: {
  number: string;
  epoch: number;
  x: number[];
  y: number[];
  z: number[][];
  globalMaxError: number;

  metric: {
    mae: number;
    rmse: number;
    max_absolute_error:
      number;
    training_loss: number;
    elapsed_training_seconds:
      number;
    inference_seconds: number;
  };
}) {
  return (
    <article
      className="ql-card"
      style={{
        overflow: "hidden",

        position: "relative",
      }}
    >
      <div
        style={{
          position: "absolute",

          top: 11,
          right: 13,

          fontSize: 24,

          fontWeight: 900,

          color:
            "rgba(148,163,184,0.14)",

          zIndex: 2,
        }}
      >
        {number}
      </div>


      <div
        style={{
          padding:
            "14px 16px 0",
        }}
      >
        <div
          style={{
            color:
              "#34d399",

            fontSize: 8,

            fontWeight: 800,

            letterSpacing:
              "0.13em",

            textTransform:
              "uppercase",
          }}
        >
          Training Snapshot
        </div>

        <h3
          style={{
            margin:
              "4px 0 2px",

            fontSize: 15,
          }}
        >
          {epoch.toLocaleString()}
          {" "}Epochs
        </h3>

        <code
          style={{
            color:
              "#64748b",

            fontSize: 9,
          }}
        >
          |Vθ − VCN|
        </code>
      </div>


      <Plot
        data={[
          {
            type: "surface",

            x,
            y,
            z,

            colorscale:
              "Magma",

            cmin: 0,

            cmax:
              globalMaxError,

            showscale: false,

            contours: {
              z: {
                show: true,

                usecolormap:
                  true,

                project: {
                  z: true,
                },
              },
            },

            hovertemplate:
              "S=%{x:.2f}<br>" +
              "τ=%{y:.3f}<br>" +
              "|Error|=%{z:.6f}" +
              "<extra></extra>",
          },
        ]}
        layout={{
          autosize: true,

          height: 305,

          margin: {
            l: 0,
            r: 0,
            t: 2,
            b: 0,
          },

          paper_bgcolor:
            "rgba(0,0,0,0)",

          font: {
            color:
              "#cbd5e1",

            size: 8,
          },

          scene: {
            xaxis: {
              ...AXIS_STYLE,

              title: {
                text: "S",
              },
            },

            yaxis: {
              ...AXIS_STYLE,

              title: {
                text: "τ",
              },
            },

            zaxis: {
              ...AXIS_STYLE,

              title: {
                text: "|E|",
              },

              range: [
                0,
                globalMaxError,
              ],
            },

            camera: CAMERA,

            aspectratio: {
              x: 1.3,
              y: 1,
              z: 0.8,
            },
          },
        }}
        config={{
          responsive: true,

          displaylogo: false,

          scrollZoom: true,
        }}
        style={{
          width: "100%",
        }}
      />


      <div
        style={{
          display: "grid",

          gridTemplateColumns:
            "repeat(3, 1fr)",

          borderTop:
            "1px solid rgba(148,163,184,0.08)",
        }}
      >
        <MiniMetric
          label="MAE"
          value={
            metric.mae
          }
        />

        <MiniMetric
          label="RMSE"
          value={
            metric.rmse
          }
        />

        <MiniMetric
          label="MAX"
          value={
            metric
              .max_absolute_error
          }
        />
      </div>
    </article>
  );
}


function MiniMetric({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  return (
    <div
      style={{
        padding:
          "8px 10px",

        textAlign: "center",
      }}
    >
      <div
        style={{
          color:
            "#64748b",

          fontSize: 7,

          letterSpacing:
            "0.08em",
        }}
      >
        {label}
      </div>

      <div
        style={{
          color:
            "#cbd5e1",

          marginTop: 2,

          fontSize: 10,

          fontWeight: 700,
        }}
      >
        {value.toFixed(5)}
      </div>
    </div>
  );
}


function ErrorConvergenceChart({
  metrics,
}: {
  metrics: MetricPoint[];
}) {
  return (
    <article
      className="ql-card"
      style={{
        padding:
          "14px 16px 4px",
      }}
    >
      <ChartTitle
        eyebrow="Pricing Error"
        title="CN-Referenced Convergence"
      />

      <Plot
        data={[
          {
            type: "scatter",

            mode:
              "lines+markers",

            x:
              metrics.map(
                (item) =>
                  item.epoch
              ),

            y:
              metrics.map(
                (item) =>
                  item.rmse
              ),

            name: "RMSE",

            line: {
              width: 3,
            },

            marker: {
              size: 7,
            },
          },

          {
            type: "scatter",

            mode:
              "lines+markers",

            x:
              metrics.map(
                (item) =>
                  item.epoch
              ),

            y:
              metrics.map(
                (item) =>
                  item.mae
              ),

            name: "MAE",

            line: {
              width: 3,
            },

            marker: {
              size: 7,
            },
          },

          {
            type: "scatter",

            mode:
              "lines+markers",

            x:
              metrics.map(
                (item) =>
                  item.epoch
              ),

            y:
              metrics.map(
                (item) =>
                  item
                    .max_absolute_error
              ),

            name:
              "Max |Error|",

            line: {
              width: 2,
              dash: "dot",
            },

            marker: {
              size: 6,
            },
          },
        ]}
        layout={{
          autosize: true,

          height: 330,

          margin: {
            l: 62,
            r: 20,
            t: 30,
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
                "Pricing Error",
            },

            gridcolor:
              "rgba(148,163,184,0.10)",
          },

          legend: {
            orientation: "h",

            x: 0,
            y: 1.12,
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


function LossConvergenceChart({
  metrics,
}: {
  metrics: MetricPoint[];
}) {
  return (
    <article
      className="ql-card"
      style={{
        padding:
          "14px 16px 4px",
      }}
    >
      <ChartTitle
        eyebrow="Optimisation"
        title="Training Objective"
      />

      <Plot
        data={[
          {
            type: "scatter",

            mode:
              "lines+markers",

            x:
              metrics.map(
                (item) =>
                  item.epoch
              ),

            y:
              metrics.map(
                (item) =>
                  item
                    .training_loss
              ),

            name:
              "Training Loss",

            line: {
              width: 3,
            },

            marker: {
              size: 7,
            },

            hovertemplate:
              "Epoch=%{x}<br>" +
              "Loss=%{y:.6e}" +
              "<extra></extra>",
          },
        ]}
        layout={{
          autosize: true,

          height: 330,

          margin: {
            l: 62,
            r: 20,
            t: 30,
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
                "Composite Loss",
            },

            type: "log",

            gridcolor:
              "rgba(148,163,184,0.10)",
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


function ImprovementSurface({
  x,
  y,
  z,
  absoluteMax,
  firstEpoch,
  lastEpoch,
}: {
  x: number[];
  y: number[];
  z: number[][];
  absoluteMax: number;
  firstEpoch: number;
  lastEpoch: number;
}) {
  return (
    <article
      className="ql-card"
      style={{
        overflow: "hidden",
      }}
    >
      <div
        style={{
          padding:
            "15px 18px 0",
        }}
      >
        <div
          style={{
            color:
              "#22d3ee",

            fontSize: 9,

            fontWeight: 800,

            letterSpacing:
              "0.14em",

            textTransform:
              "uppercase",
          }}
        >
          Improvement Field
        </div>

        <h3
          style={{
            margin:
              "4px 0 3px",

            fontSize: 16,
          }}
        >
          Where Did Training Help?
        </h3>

        <code
          style={{
            color:
              "#64748b",

            fontSize: 9,
          }}
        >
          |E{firstEpoch}| −
          |E{lastEpoch}|
        </code>
      </div>


      <Plot
        data={[
          {
            type: "surface",

            x,
            y,
            z,

            colorscale:
              "RdBu",

            reversescale: false,

            cmin:
              -absoluteMax,

            cmax:
              absoluteMax,

            colorbar: {
              title: {
                text:
                  "Improvement",
              },

              thickness: 10,
            },

            contours: {
              z: {
                show: true,

                project: {
                  z: true,
                },
              },
            },

            hovertemplate:
              "S=%{x:.2f}<br>" +
              "τ=%{y:.3f}<br>" +
              "Improvement=%{z:.6f}" +
              "<extra></extra>",
          },
        ]}
        layout={{
          autosize: true,

          height: 430,

          margin: {
            l: 0,
            r: 0,
            t: 4,
            b: 0,
          },

          paper_bgcolor:
            "rgba(0,0,0,0)",

          font: {
            color:
              "#cbd5e1",

            size: 9,
          },

          scene: {
            xaxis: {
              ...AXIS_STYLE,

              title: {
                text: "Spot S",
              },
            },

            yaxis: {
              ...AXIS_STYLE,

              title: {
                text: "τ",
              },
            },

            zaxis: {
              ...AXIS_STYLE,

              title: {
                text:
                  "Δ |Error|",
              },
            },

            camera: CAMERA,

            aspectratio: {
              x: 1.35,
              y: 1,
              z: 0.8,
            },
          },
        }}
        config={{
          responsive: true,

          displaylogo: false,

          scrollZoom: true,
        }}
        style={{
          width: "100%",
        }}
      />
    </article>
  );
}


function ImprovementInterpretation({
  stats,
  firstEpoch,
  lastEpoch,
  firstMetrics,
  lastMetrics,
}: {
  stats:
    ImprovementStats | null;

  firstEpoch: number;
  lastEpoch: number;

  firstMetrics:
    Omit<MetricPoint, "epoch">;

  lastMetrics:
    Omit<MetricPoint, "epoch">;
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
            "#a78bfa",

          fontSize: 9,

          fontWeight: 800,

          letterSpacing:
            "0.13em",

          textTransform:
            "uppercase",
        }}
      >
        Interpretation
      </div>

      <h3
        style={{
          margin:
            "6px 0 14px",

          fontSize: 17,
        }}
      >
        Spatial Learning
        Summary
      </h3>


      <StatRow
        label="Improved nodes"
        value={
          stats
            ? `${stats.improvedPercent.toFixed(
                1
              )}%`
            : "—"
        }
      />

      <StatRow
        label="Worsened nodes"
        value={
          stats
            ? `${stats.worsenedPercent.toFixed(
                1
              )}%`
            : "—"
        }
      />

      <StatRow
        label="Near unchanged"
        value={
          stats
            ? `${stats.unchangedPercent.toFixed(
                1
              )}%`
            : "—"
        }
      />


      <div
        style={{
          height: 1,

          background:
            "rgba(148,163,184,0.10)",

          margin:
            "14px 0",
        }}
      />


      <StatRow
        label={`${firstEpoch} RMSE`}
        value={
          firstMetrics.rmse.toFixed(
            6
          )
        }
      />

      <StatRow
        label={`${lastEpoch} RMSE`}
        value={
          lastMetrics.rmse.toFixed(
            6
          )
        }
      />


      <p
        style={{
          margin:
            "17px 0 0",

          color:
            "#64748b",

          fontSize: 11,

          lineHeight: 1.65,
        }}
      >
        A positive improvement
        value means the later
        network is closer to the
        CN reference at that
        state-space location.
        Negative values reveal
        local deterioration even
        when global error metrics
        improve.
      </p>
    </article>
  );
}


function StatRow({
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

        gap: 20,

        padding:
          "7px 0",

        borderBottom:
          "1px solid rgba(148,163,184,0.06)",
      }}
    >
      <span
        style={{
          color:
            "#64748b",

          fontSize: 10,
        }}
      >
        {label}
      </span>

      <strong
        style={{
          color:
            "#e2e8f0",

          fontSize: 11,
        }}
      >
        {value}
      </strong>
    </div>
  );
}


function ChartTitle({
  eyebrow,
  title,
}: {
  eyebrow: string;
  title: string;
}) {
  return (
    <div>
      <div
        style={{
          color:
            "#22d3ee",

          fontSize: 8,

          fontWeight: 800,

          letterSpacing:
            "0.12em",

          textTransform:
            "uppercase",
        }}
      >
        {eyebrow}
      </div>

      <h3
        style={{
          margin:
            "3px 0 0",

          fontSize: 14,
        }}
      >
        {title}
      </h3>
    </div>
  );
}


function SectionHeading({
  eyebrow,
  title,
  description,
}: {
  eyebrow: string;
  title: string;
  description:
    React.ReactNode;
}) {
  return (
    <div
      style={{
        display: "flex",

        justifyContent:
          "space-between",

        alignItems:
          "flex-end",

        gap: 28,

        flexWrap: "wrap",

        padding:
          "12px 2px 0",
      }}
    >
      <div>
        <div
          style={{
            color:
              "#8b5cf6",

            fontSize: 9,

            fontWeight: 800,

            letterSpacing:
              "0.14em",

            textTransform:
              "uppercase",
          }}
        >
          {eyebrow}
        </div>

        <h2
          style={{
            margin:
              "4px 0 0",

            fontSize: 19,
          }}
        >
          {title}
        </h2>
      </div>

      <p
        style={{
          margin: 0,

          maxWidth: 530,

          color:
            "#64748b",

          fontSize: 11,

          lineHeight: 1.55,
        }}
      >
        {description}
      </p>
    </div>
  );
}


type MetricPoint = {
  epoch: number;
  mae: number;
  rmse: number;
  max_absolute_error:
    number;
  training_loss: number;
  elapsed_training_seconds:
    number;
  inference_seconds: number;
};


type ImprovementStats = {
  improvedPercent: number;
  worsenedPercent: number;
  unchangedPercent: number;
};


function percentChange(
  start: number,
  end: number
) {
  if (
    !Number.isFinite(start) ||
    start === 0
  ) {
    return null;
  }

  return (
    ((end - start) / start)
    * 100
  );
}


function formatPercentChange(
  value: number | null
) {
  if (value === null) {
    return "—";
  }

  const sign =
    value > 0 ? "+" : "";

  return (
    `${sign}${value.toFixed(1)}%`
  );
}


function matrixAbsoluteMax(
  matrix: number[][]
) {
  let maximum = 0;

  for (
    const row of matrix
  ) {
    for (
      const value of row
    ) {
      maximum = Math.max(
        maximum,
        Math.abs(value)
      );
    }
  }

  return maximum;
}


function classifyImprovement(
  matrix: number[][],
  tolerance = 1e-8
): ImprovementStats {
  let improved = 0;
  let worsened = 0;
  let unchanged = 0;
  let total = 0;

  for (
    const row of matrix
  ) {
    for (
      const value of row
    ) {
      total += 1;

      if (
        value > tolerance
      ) {
        improved += 1;
      } else if (
        value < -tolerance
      ) {
        worsened += 1;
      } else {
        unchanged += 1;
      }
    }
  }

  if (total === 0) {
    return {
      improvedPercent: 0,
      worsenedPercent: 0,
      unchangedPercent: 0,
    };
  }

  return {
    improvedPercent:
      (improved / total)
      * 100,

    worsenedPercent:
      (worsened / total)
      * 100,

    unchangedPercent:
      (unchanged / total)
      * 100,
  };
}