"use client";

import {
  useState,
} from "react";

import dynamic from "next/dynamic";

import type {
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

type EpochKey =
  | "500"
  | "1000"
  | "2000"
  | "4000";

type ScaleMode =
  | "linear"
  | "log";

const EPOCHS: EpochKey[] = [
  "500",
  "1000",
  "2000",
  "4000",
];

const LOG_EPSILON = 1e-6;

const CAMERA = {
  eye: {
    x: 1.45,
    y: 1.45,
    z: 1.15,
  },
};


function nearestIndex(
  values: number[],
  target: number
) {
  let bestIndex = 0;
  let bestDistance = Infinity;

  values.forEach(
    (value, index) => {
      const distance =
        Math.abs(
          value - target
        );

      if (
        distance <
        bestDistance
      ) {
        bestDistance =
          distance;

        bestIndex =
          index;
      }
    }
  );

  return bestIndex;
}


function finiteMaximum(
  matrices: number[][][]
) {
  let maximum =
    -Infinity;

  matrices.forEach(
    (matrix) => {
      matrix.forEach(
        (row) => {
          row.forEach(
            (value) => {
              if (
                Number.isFinite(
                  value
                )
              ) {
                maximum =
                  Math.max(
                    maximum,
                    value
                  );
              }
            }
          );
        }
      );
    }
  );

  return Number.isFinite(
    maximum
  )
    ? maximum
    : 0;
}


function finiteMinimum(
  matrices: number[][][]
) {
  let minimum =
    Infinity;

  matrices.forEach(
    (matrix) => {
      matrix.forEach(
        (row) => {
          row.forEach(
            (value) => {
              if (
                Number.isFinite(
                  value
                )
              ) {
                minimum =
                  Math.min(
                    minimum,
                    value
                  );
              }
            }
          );
        }
      );
    }
  );

  return Number.isFinite(
    minimum
  )
    ? minimum
    : 0;
}


function percentile(
  values: number[],
  probability: number
) {
  if (
    values.length === 0
  ) {
    return 0;
  }

  const sorted = [
    ...values,
  ].sort(
    (a, b) => a - b
  );

  const position =
    probability *
    (sorted.length - 1);

  const lower =
    Math.floor(
      position
    );

  const upper =
    Math.ceil(
      position
    );

  if (
    lower === upper
  ) {
    return sorted[
      lower
    ];
  }

  const weight =
    position - lower;

  return (
    sorted[lower] *
      (1 - weight) +
    sorted[upper] *
      weight
  );
}


function collectFinite(
  matrices: number[][][]
) {
  const values: number[] =
    [];

  matrices.forEach(
    (matrix) => {
      matrix.forEach(
        (row) => {
          row.forEach(
            (value) => {
              if (
                Number.isFinite(
                  value
                )
              ) {
                values.push(
                  value
                );
              }
            }
          );
        }
      );
    }
  );

  return values;
}


function transformError(
  value: number,
  scaleMode: ScaleMode
) {
  if (
    scaleMode === "log"
  ) {
    return Math.log10(
      Math.max(
        value,
        LOG_EPSILON
      )
    );
  }

  return value;
}


export default function PinnErrorEvolutionAtlas({
  data,
}: Props) {
  const convergence =
    data.pinn_convergence;

  const [
    scaleMode,
    setScaleMode,
  ] =
    useState<ScaleMode>(
      "linear"
    );

  if (
    !convergence.available
  ) {
    return null;
  }

  const availableEpochs =
    EPOCHS.filter(
      (epoch) =>
        convergence
          .absolute_errors[
          epoch
        ] !== undefined
    );

  if (
    availableEpochs.length ===
    0
  ) {
    return null;
  }

  const spotGrid =
    data.grid.spot;

  const tauGrid =
    data.grid
      .time_to_maturity;

  const rawSurfaces =
    availableEpochs.map(
      (epoch) =>
        convergence
          .absolute_errors[
          epoch
        ]
    );

  /*
   * The underlying numerical data
   * always remain in ordinary
   * absolute-error units.
   *
   * Only the displayed z-coordinate
   * is transformed in log mode.
   */
  const displaySurfaces =
    rawSurfaces.map(
      (surface) =>
        surface.map(
          (row) =>
            row.map(
              (value) =>
                transformError(
                  value,
                  scaleMode
                )
            )
        )
    );

  /*
   * Preserve the true uncapped
   * maximum from the raw experiment
   * for reporting.
   */
  const actualMaximum =
    finiteMaximum(
      rawSurfaces
    );

  const finiteValues =
    collectFinite(
      displaySurfaces
    );

  /*
   * Shared robust display limits.
   *
   * Linear:
   *   lower = 0
   *   upper = pooled Q97.5
   *
   * Log:
   *   lower = pooled Q2.5
   *   upper = pooled Q97.5
   *
   * Every epoch therefore uses
   * exactly the same visual scale
   * within the selected mode.
   */
  const robustMaximum =
    percentile(
      finiteValues,
      0.975
    );

  const robustMinimum =
    scaleMode === "log"
      ? percentile(
          finiteValues,
          0.025
        )
      : 0;

  const fallbackMinimum =
    finiteMinimum(
      displaySurfaces
    );

  const fallbackMaximum =
    finiteMaximum(
      displaySurfaces
    );

  const displayMinimum =
    Number.isFinite(
      robustMinimum
    )
      ? robustMinimum
      : fallbackMinimum;

  const displayMaximum =
    robustMaximum >
    displayMinimum
      ? robustMaximum
      : fallbackMaximum;

  const safeDisplayMaximum =
    displayMaximum >
    displayMinimum
      ? displayMaximum
      : displayMinimum +
        1e-6;

  const boundary =
    data.exercise_boundary.filter(
      (point) =>
        point.spot !== null &&
        Number.isFinite(
          point.spot
        ) &&
        Number.isFinite(
          point
            .time_to_maturity
        )
    );

  const firstEpoch =
    availableEpochs[0];

  const lastEpoch =
    availableEpochs[
      availableEpochs.length -
        1
    ];

  const firstMetrics =
    convergence.metrics[
      firstEpoch
    ];

  const lastMetrics =
    convergence.metrics[
      lastEpoch
    ];

  const rmseReduction =
    firstMetrics &&
    lastMetrics &&
    firstMetrics.rmse > 0
      ? 100 *
        (
          1 -
          lastMetrics.rmse /
            firstMetrics.rmse
        )
      : null;

  const scaleLabel =
    scaleMode === "log"
      ? "log₁₀|PINN − CN|"
      : "|PINN − CN|";

  const colorLabel =
    scaleMode === "log"
      ? "log₁₀|E|"
      : "|Error|";

  return (
    <section
      className="research-panel"
    >
      <div
        className="research-panel-header"
      >
        <div>
          <div
            className="research-eyebrow"
          >
            PINN TRAINING
            TOPOGRAPHY
          </div>

          <h2>
            PINN Error-Evolution
            Atlas
          </h2>

          <p>
            Absolute pricing error
            relative to the projected
            Crank–Nicolson reference
            across the state-time
            domain.
          </p>
        </div>

        <div
          style={{
            display: "flex",
            gap: 6,
            padding: 4,
            borderRadius: 12,
            border:
              "1px solid rgba(148,163,184,0.14)",
            background:
              "rgba(15,23,42,0.55)",
          }}
        >
          <ScaleButton
            active={
              scaleMode ===
              "linear"
            }
            onClick={() =>
              setScaleMode(
                "linear"
              )
            }
          >
            Linear Error
          </ScaleButton>

          <ScaleButton
            active={
              scaleMode ===
              "log"
            }
            onClick={() =>
              setScaleMode(
                "log"
              )
            }
          >
            Log₁₀ Error
          </ScaleButton>
        </div>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns:
            "repeat(auto-fit, minmax(180px, 1fr))",
          gap: "12px",
          marginBottom:
            "18px",
        }}
      >
        <MetricCard
          label="Training Window"
          value={`${Number(
            firstEpoch
          ).toLocaleString()} → ${Number(
            lastEpoch
          ).toLocaleString()}`}
          note="epochs"
        />

        <MetricCard
          label="Initial RMSE"
          value={
            firstMetrics
              ? firstMetrics
                  .rmse
                  .toFixed(
                    4
                  )
              : "—"
          }
          note="vs projected CN"
        />

        <MetricCard
          label="Final RMSE"
          value={
            lastMetrics
              ? lastMetrics
                  .rmse
                  .toFixed(
                    4
                  )
              : "—"
          }
          note="vs projected CN"
        />

        <MetricCard
          label="RMSE Reduction"
          value={
            rmseReduction !==
            null
              ? `${rmseReduction.toFixed(
                  1
                )}%`
              : "—"
          }
          note="training trajectory"
        />
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns:
            "repeat(2, minmax(0, 1fr))",
          gap: "16px",
        }}
        className="pinn-error-evolution-grid"
      >
        {availableEpochs.map(
          (
            epoch,
            epochIndex
          ) => {
            const rawErrorSurface =
              convergence
                .absolute_errors[
                epoch
              ];

            const errorSurface =
              displaySurfaces[
                epochIndex
              ];

            const metrics =
              convergence.metrics[
                epoch
              ];

            const boundaryTau:
              number[] = [];

            const boundarySpot:
              number[] = [];

            const boundaryError:
              number[] = [];

            const boundaryRawError:
              number[] = [];

            boundary.forEach(
              (point) => {
                if (
                  point.spot ===
                  null
                ) {
                  return;
                }

                const tauIndex =
                  nearestIndex(
                    tauGrid,
                    point
                      .time_to_maturity
                  );

                const spotIndex =
                  nearestIndex(
                    spotGrid,
                    point.spot
                  );

                const rawError =
                  rawErrorSurface[
                    tauIndex
                  ]?.[
                    spotIndex
                  ];

                if (
                  rawError ===
                    undefined ||
                  !Number.isFinite(
                    rawError
                  )
                ) {
                  return;
                }

                const displayError =
                  transformError(
                    rawError,
                    scaleMode
                  );

                boundaryTau.push(
                  point
                    .time_to_maturity
                );

                boundarySpot.push(
                  point.spot
                );

                boundaryError.push(
                  displayError
                );

                boundaryRawError.push(
                  rawError
                );
              }
            );

            return (
              <div
                key={epoch}
                style={{
                  border:
                    "1px solid rgba(148, 163, 184, 0.14)",
                  borderRadius:
                    "18px",
                  overflow:
                    "hidden",
                  background:
                    "rgba(4, 9, 20, 0.58)",
                }}
              >
                <div
                  style={{
                    padding:
                      "14px 16px 4px",
                  }}
                >
                  <div
                    style={{
                      display:
                        "flex",
                      alignItems:
                        "baseline",
                      justifyContent:
                        "space-between",
                      gap: "10px",
                    }}
                  >
                    <h3
                      style={{
                        margin: 0,
                        fontSize:
                          "0.98rem",
                      }}
                    >
                      {Number(
                        epoch
                      ).toLocaleString()}{" "}
                      Epochs
                    </h3>

                    <span
                      style={{
                        fontSize:
                          "0.72rem",
                        opacity:
                          0.65,
                      }}
                    >
                      {scaleLabel}
                    </span>
                  </div>

                  {metrics && (
                    <div
                      style={{
                        display:
                          "flex",
                        gap: "12px",
                        flexWrap:
                          "wrap",
                        marginTop:
                          "6px",
                        fontSize:
                          "0.72rem",
                        opacity:
                          0.72,
                      }}
                    >
                      <span>
                        MAE{" "}
                        {metrics.mae.toFixed(
                          4
                        )}
                      </span>

                      <span>
                        RMSE{" "}
                        {metrics.rmse.toFixed(
                          4
                        )}
                      </span>

                      <span>
                        Max{" "}
                        {metrics.max_absolute_error.toFixed(
                          4
                        )}
                      </span>
                    </div>
                  )}
                </div>

                <Plot
                  data={[
                    {
                      type:
                        "surface",

                      x: spotGrid,
                      y: tauGrid,
                      z: errorSurface,

                      cmin:
                        displayMinimum,

                      cmax:
                        safeDisplayMaximum,

                      colorscale:
                        "Turbo",

                      colorbar: {
                        title: {
                          text:
                            colorLabel,
                        },

                        thickness:
                          10,

                        len:
                          0.58,
                      },

                      contours: {
                        z: {
                          show:
                            true,

                          usecolormap:
                            true,

                          project: {
                            z: true,
                          },
                        },
                      },

                      customdata:
                        rawErrorSurface,

                      hovertemplate:
                        scaleMode ===
                        "log"
                          ? [
                              "S=%{x:.2f}",
                              "τ=%{y:.3f}",
                              "log₁₀|E|=%{z:.4f}",
                              "|E|=%{customdata:.6f}",
                              "<extra></extra>",
                            ].join(
                              "<br>"
                            )
                          : [
                              "S=%{x:.2f}",
                              "τ=%{y:.3f}",
                              "|E|=%{z:.6f}",
                              "<extra></extra>",
                            ].join(
                              "<br>"
                            ),
                    },

                    {
                      type:
                        "scatter3d",

                      mode:
                        "lines+markers",

                      x:
                        boundarySpot,

                      y:
                        boundaryTau,

                      z:
                        boundaryError,

                      customdata:
                        boundaryRawError,

                      line: {
                        width: 7,
                      },

                      marker: {
                        size: 2,
                      },

                      name:
                        "Free boundary",

                      hovertemplate:
                        scaleMode ===
                        "log"
                          ? [
                              "S*=%{x:.2f}",
                              "τ=%{y:.3f}",
                              "log₁₀|E|=%{z:.4f}",
                              "|E|=%{customdata:.6f}",
                              "<extra>Free boundary</extra>",
                            ].join(
                              "<br>"
                            )
                          : [
                              "S*=%{x:.2f}",
                              "τ=%{y:.3f}",
                              "|E|=%{z:.6f}",
                              "<extra>Free boundary</extra>",
                            ].join(
                              "<br>"
                            ),
                    },
                  ]}
                  layout={{
                    autosize:
                      true,

                    height:
                      430,

                    margin: {
                      l: 0,
                      r: 0,
                      b: 0,
                      t: 8,
                    },

                    paper_bgcolor:
                      "rgba(0,0,0,0)",

                    plot_bgcolor:
                      "rgba(0,0,0,0)",

                    font: {
                      color:
                        "#cbd5e1",
                      size: 10,
                    },

                    showlegend:
                      false,

                    scene: {
                      camera:
                        CAMERA,

                      xaxis: {
                        title:
                          "Spot S",

                        gridcolor:
                          "rgba(148,163,184,0.12)",

                        zerolinecolor:
                          "rgba(148,163,184,0.18)",
                      },

                      yaxis: {
                        title:
                          "Time to maturity τ",

                        gridcolor:
                          "rgba(148,163,184,0.12)",

                        zerolinecolor:
                          "rgba(148,163,184,0.18)",
                      },

                      zaxis: {
                        title:
                          scaleLabel,

                        range: [
                          displayMinimum,
                          safeDisplayMaximum,
                        ],

                        gridcolor:
                          "rgba(148,163,184,0.12)",

                        zerolinecolor:
                          "rgba(148,163,184,0.18)",
                      },

                      aspectmode:
                        "manual",

                      aspectratio: {
                        x: 1.25,
                        y: 1,
                        z: 0.72,
                      },
                    },
                  }}
                  config={{
                    responsive:
                      true,

                    displaylogo:
                      false,

                    scrollZoom:
                      true,

                    toImageButtonOptions:
                      {
                        format:
                          "png",

                        filename:
                          `quantlab-pinn-error-${epoch}-${scaleMode}`,
                      },
                  }}
                  style={{
                    width:
                      "100%",

                    height:
                      "430px",
                  }}
                  useResizeHandler
                />
              </div>
            );
          }
        )}
      </div>

      <div
        style={{
          marginTop:
            "16px",

          padding:
            "14px 16px",

          borderRadius:
            "14px",

          border:
            "1px solid rgba(148, 163, 184, 0.12)",

          background:
            "rgba(15, 23, 42, 0.38)",

          fontSize:
            "0.82rem",

          lineHeight:
            1.6,

          opacity:
            0.82,
        }}
      >
        <strong>
          Reading the atlas.
        </strong>{" "}

        {scaleMode ===
        "linear" ? (
          <>
            All panels use the
            same state-time
            coordinates, camera
            orientation and
            robust common absolute
            error scale. The early
            PINN error is spatially
            broad, while training
            progressively suppresses
            large regions of the
            domain. By the final
            checkpoint the remaining
            pricing discrepancy is
            much more localized,
            including structure
            around the numerically
            estimated American
            exercise boundary. The
            displayed common scale
            is capped at the pooled
            97.5th percentile so
            extreme early-training
            residuals do not
            visually flatten the
            converged surface.
          </>
        ) : (
          <>
            The logarithmic view
            displays{" "}
            <strong>
              log₁₀|PINN − CN|
            </strong>{" "}
            using a common robust
            scale across all four
            checkpoints. This
            reveals orders of
            magnitude that are
            compressed in the
            linear view and makes
            late-stage residual
            geometry easier to
            inspect. Values are
            floored at{" "}
            <strong>
              {LOG_EPSILON}
            </strong>{" "}
            before the logarithm
            is taken; the underlying
            pricing errors and
            reported MAE/RMSE
            metrics remain
            untransformed.
          </>
        )}{" "}

        The uncapped maximum
        absolute error across all
        checkpoints is{" "}
        <strong>
          {actualMaximum.toFixed(
            4
          )}
        </strong>
        .
      </div>
    </section>
  );
}


function ScaleButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children:
    React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={
        active
      }
      style={{
        border: 0,

        borderRadius:
          9,

        padding:
          "7px 11px",

        cursor:
          "pointer",

        fontSize:
          "0.72rem",

        fontWeight:
          650,

        color:
          active
            ? "#e2e8f0"
            : "#64748b",

        background:
          active
            ? "rgba(34,211,238,0.13)"
            : "transparent",

        transition:
          "background 140ms ease, color 140ms ease",
      }}
    >
      {children}
    </button>
  );
}


function MetricCard({
  label,
  value,
  note,
}: {
  label: string;
  value: string;
  note: string;
}) {
  return (
    <div
      style={{
        padding:
          "13px 15px",

        borderRadius:
          "14px",

        border:
          "1px solid rgba(148, 163, 184, 0.12)",

        background:
          "rgba(15, 23, 42, 0.45)",
      }}
    >
      <div
        style={{
          fontSize:
            "0.68rem",

          letterSpacing:
            "0.08em",

          textTransform:
            "uppercase",

          opacity:
            0.55,
        }}
      >
        {label}
      </div>

      <div
        style={{
          marginTop:
            "4px",

          fontSize:
            "1.15rem",

          fontWeight:
            650,
        }}
      >
        {value}
      </div>

      <div
        style={{
          marginTop:
            "2px",

          fontSize:
            "0.68rem",

          opacity:
            0.48,
        }}
      >
        {note}
      </div>
    </div>
  );
}