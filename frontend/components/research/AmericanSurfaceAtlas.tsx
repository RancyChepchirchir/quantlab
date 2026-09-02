"use client";

import dynamic from "next/dynamic";

import {
  ReactNode,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  AmericanSurfaceAtlasInput,
  AmericanSurfaceAtlasResult,
  getAmericanSurfaceAtlas,
} from "@/lib/api/americanSurfaceAtlas";

import PinnLearningDynamics
  from "@/components/research/PinnLearningDynamics";

import FreeBoundaryDifficulty
  from "@/components/research/FreeBoundaryDifficulty";

import BoundaryDistanceProfile
  from "@/components/research/BoundaryDistanceProfile";

import PinnErrorTopography
  from "@/components/research/PinnErrorTopography";


const Plot = dynamic(
  () => import("react-plotly.js"),
  {
    ssr: false,
  }
);


type Props = {
  input?: Partial<
    AmericanSurfaceAtlasInput
  >;
};


const DEFAULT_INPUT:
  AmericanSurfaceAtlasInput = {
    spot: 100,
    strike: 100,
    rate: 0.05,
    volatility: 0.20,
    maturity: 1.0,
    dividend_yield: 0.0,

    s_max: 250,

    space_steps: 80,
    time_steps: 80,

    crr_steps: 150,
    crr_surface_points: 31,

    boundary_tolerance: 1e-4,
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


export default function AmericanSurfaceAtlas({
  input,
}: Props) {
  const [data, setData] =
    useState<
      AmericanSurfaceAtlasResult | null
    >(null);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState<string | null>(null);


  const request = useMemo(
    () => ({
      ...DEFAULT_INPUT,
      ...input,
    }),
    [input]
  );


  useEffect(() => {
    let active = true;

    async function load() {
      try {
        setLoading(true);
        setError(null);

        const result =
          await getAmericanSurfaceAtlas(
            request
          );

        if (active) {
          setData(result);
        }
      } catch (err) {
        if (active) {
          setError(
            err instanceof Error
              ? err.message
              : "Unable to load Surface Atlas."
          );
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    load();

    return () => {
      active = false;
    };
  }, [request]);


  if (loading) {
    return <LoadingState />;
  }


  if (error || !data) {
    return (
      <section className="ql-card">
        <div
          style={{
            color: "#f87171",
          }}
        >
          {error ??
            "No surface data returned."}
        </div>
      </section>
    );
  }


  const boundary =
    data.exercise_boundary.filter(
      (
        point
      ): point is {
        time_to_maturity: number;
        spot: number;
      } => point.spot !== null
    );


  const boundaryZ =
    boundary.map(
      (point) => {
        const tauIndex =
          nearestIndex(
            data.grid
              .time_to_maturity,
            point.time_to_maturity
          );

        const spotIndex =
          nearestIndex(
            data.grid.spot,
            point.spot
          );

        return (
          data.surfaces
            .crank_nicolson[
              tauIndex
            ][spotIndex]
        );
      }
    );


  const pinnAvailable =
    data.pinn.available &&
    data.surfaces.pinn_v2 !== null &&
    data.errors.pinn_signed !== null &&
    data.errors.pinn_absolute !== null;


  const sceneBase = {
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

    camera: CAMERA,

    aspectratio: {
      x: 1.35,
      y: 1.0,
      z: 0.85,
    },
  };


  return (
    <section
      style={{
        display: "grid",
        gap: 18,
      }}
    >
      <AtlasHeader
        data={data}
      />

      <KpiStrip
        data={data}
      />


      {/* =========================================
          PRICE SURFACE MATRIX
          ========================================= */}

      <SectionHeading
        eyebrow="Method Atlas"
        title="American Put Price Surfaces"
        description={
          <>
            Identical state-space geometry
            across lattice, finite-difference
            and physics-informed neural
            approximations.
          </>
        }
      />


      <div
        style={{
          display: "grid",

          gridTemplateColumns:
            "repeat(auto-fit, minmax(340px, 1fr))",

          gap: 14,
        }}
      >
        <SurfacePanel
          number="01"
          eyebrow="Lattice"
          title="CRR Binomial"
          equation="VCRR(S,τ)"
          accent="#22d3ee"
        >
          <SurfacePlot
            x={data.grid.spot}
            y={
              data.grid
                .time_to_maturity
            }
            z={data.surfaces.crr}
            zTitle="Option Value"
            colorTitle="V"
            colorscale="Turbo"
            sceneBase={sceneBase}
            height={365}
            cmin={
              data.summary.min_price
            }
            cmax={
              data.summary.max_price
            }
          />
        </SurfacePanel>


        <SurfacePanel
          number="02"
          eyebrow="Finite Difference"
          title="Projected Crank–Nicolson"
          equation="VCN(S,τ)"
          accent="#a78bfa"
        >
          <SurfaceWithBoundary
            data={data}
            boundary={boundary}
            boundaryZ={boundaryZ}
            sceneBase={sceneBase}
          />
        </SurfacePanel>


        <SurfacePanel
          number="03"
          eyebrow="Neural PDE"
          title="PINN V2"
          equation="Vθ(S,τ)"
          accent="#34d399"
        >
          {pinnAvailable ? (
            <SurfacePlot
              x={data.grid.spot}
              y={
                data.grid
                  .time_to_maturity
              }
              z={
                data.surfaces
                  .pinn_v2!
              }
              zTitle="PINN Value"
              colorTitle="Vθ"
              colorscale="Turbo"
              sceneBase={sceneBase}
              height={365}
              cmin={
                data.summary.min_price
              }
              cmax={
                data.summary.max_price
              }
            />
          ) : (
            <UnavailableSurface />
          )}
        </SurfacePanel>
      </div>


      {/* =========================================
          ERROR MATRIX
          ========================================= */}

      <SectionHeading
        eyebrow="Error Geometry"
        title="Numerical & Neural Error Landscapes"
        description={
          <>
            Crank–Nicolson is used here as
            the common numerical reference
            surface. These landscapes show
            where disagreement occurs, not
            merely its average magnitude.
          </>
        }
      />


      <div
        style={{
          display: "grid",

          gridTemplateColumns:
            "repeat(auto-fit, minmax(340px, 1fr))",

          gap: 14,
        }}
      >
        <SurfacePanel
          number="04"
          eyebrow="Numerical Error"
          title="CRR − CN"
          equation="ECRR = VCRR − VCN"
          accent="#fb7185"
        >
          <SurfacePlot
            x={data.grid.spot}
            y={
              data.grid
                .time_to_maturity
            }
            z={
              data.errors
                .crr_signed
            }
            zTitle="Signed Error"
            colorTitle="ΔV"
            colorscale="RdBu"
            sceneBase={sceneBase}
            height={365}
            symmetricRange={
              data.summary
                .max_crr_absolute_error
            }
          />
        </SurfacePanel>


        <SurfacePanel
          number="05"
          eyebrow="Neural Error"
          title="PINN − CN"
          equation="EPINN = Vθ − VCN"
          accent="#f59e0b"
        >
          {pinnAvailable ? (
            <SurfacePlot
              x={data.grid.spot}
              y={
                data.grid
                  .time_to_maturity
              }
              z={
                data.errors
                  .pinn_signed!
              }
              zTitle="Signed Error"
              colorTitle="ΔV"
              colorscale="RdBu"
              sceneBase={sceneBase}
              height={365}
              symmetricRange={
                data.pinn
                  .max_absolute_error_vs_cn ??
                undefined
              }
            />
          ) : (
            <UnavailableSurface />
          )}
        </SurfacePanel>


        <SurfacePanel
          number="06"
          eyebrow="Neural Error Magnitude"
          title="|PINN − CN|"
          equation="|EPINN(S,τ)|"
          accent="#e879f9"
        >
          {pinnAvailable ? (
            <SurfacePlot
              x={data.grid.spot}
              y={
                data.grid
                  .time_to_maturity
              }
              z={
                data.errors
                  .pinn_absolute!
              }
              zTitle="Absolute Error"
              colorTitle="|ΔV|"
              colorscale="Magma"
              sceneBase={sceneBase}
              height={365}
            />
          ) : (
            <UnavailableSurface />
          )}
        </SurfacePanel>
      </div>


      {/* =========================================
          PINN DIAGNOSTICS
          ========================================= */}

      {pinnAvailable && (
        <PinnDiagnostics
          data={data}
        />
      )}

      {data.pinn_convergence.available && (
        <>
            <div
            style={{
                height: 1,

                margin:
                "12px 0 4px",

                background:
                "linear-gradient(90deg, transparent, rgba(139,92,246,0.38), rgba(34,211,238,0.30), transparent)",
            }}
            />

            <PinnLearningDynamics
            data={data}
            />
        </>
        )}

      {data.pinn_convergence.available &&
        Object.keys(
            data.pinn_convergence
            .boundary_diagnostics
        ).length > 0 && (
            <>
            <div
                style={{
                height: 1,

                margin:
                    "14px 0 4px",

                background:
                    "linear-gradient(90deg, transparent, rgba(244,63,94,0.40), rgba(34,211,238,0.25), transparent)",
                }}
            />

            <FreeBoundaryDifficulty
                data={data}
            />
            </>
        )}

        {data.pinn_convergence.available &&
            Object.keys(
                data.pinn_convergence
                .boundary_distance_profiles
            ).length > 0 && (
                <>
                <div
                    style={{
                    height: 1,

                    margin:
                        "14px 0 4px",

                    background:
                        "linear-gradient(90deg, transparent, rgba(34,211,238,0.40), rgba(139,92,246,0.30), transparent)",
                    }}
                />

                <BoundaryDistanceProfile
                    data={data}
                />
                </>
            )}

        {data.pinn_convergence.available && (
            <>
                <div
                style={{
                    height: 1,

                    margin:
                    "16px 0 5px",

                    background:
                    "linear-gradient(90deg, transparent, rgba(244,63,94,0.42), rgba(34,211,238,0.30), transparent)",
                }}
                />

                <PinnErrorTopography
                data={data}
                />
            </>
            )}


      {/* =========================================
          EXERCISE GEOMETRY
          ========================================= */}

      <SectionHeading
        eyebrow="Optimal Stopping"
        title="Early-Exercise Geometry"
        description={
          <>
            The obstacle gap separates the
            continuation and exercise
            regimes. The estimated white
            curve tracks the numerical
            free boundary.
          </>
        }
      />


      <div
        style={{
          display: "grid",

          gridTemplateColumns:
            "minmax(340px, 0.9fr) minmax(500px, 1.5fr)",

          gap: 14,
        }}
        className="atlas-exercise-grid"
      >
        <SurfacePanel
          number="07"
          eyebrow="Obstacle Problem"
          title="Continuation Premium"
          equation="G = VCN − Φ"
          accent="#34d399"
        >
          <SurfacePlot
            x={data.grid.spot}
            y={
              data.grid
                .time_to_maturity
            }
            z={
              data.surfaces
                .exercise_gap
            }
            zTitle="Obstacle Gap"
            colorTitle="V − Φ"
            colorscale="Viridis"
            sceneBase={sceneBase}
            height={390}
          />
        </SurfacePanel>


        <BoundaryHeatmap
          data={data}
          boundary={boundary}
        />
      </div>


      <ResearchNote />
    </section>
  );
}


function LoadingState() {
  return (
    <section
      className="ql-card"
      style={{
        minHeight: 520,

        display: "grid",

        placeItems: "center",
      }}
    >
      <div
        style={{
          textAlign: "center",
        }}
      >
        <div
          style={{
            color: "#22d3ee",

            fontSize: 11,

            letterSpacing:
              "0.14em",

            textTransform:
              "uppercase",

            marginBottom: 9,
          }}
        >
          Numerical + Neural Engine
        </div>

        <div
          style={{
            color: "#cbd5e1",

            fontSize: 17,
          }}
        >
          Building comparative
          American-option surfaces...
        </div>
      </div>
    </section>
  );
}


function AtlasHeader({
  data,
}: {
  data:
    AmericanSurfaceAtlasResult;
}) {
  return (
    <header
      className="ql-card"
      style={{
        padding:
          "24px 26px",

        background:
          "radial-gradient(circle at 80% 0%, rgba(139,92,246,0.14), transparent 34%), radial-gradient(circle at 15% 100%, rgba(34,211,238,0.08), transparent 32%)",
      }}
    >
      <div
        style={{
          display: "flex",

          justifyContent:
            "space-between",

          alignItems:
            "flex-start",

          gap: 24,

          flexWrap: "wrap",
        }}
      >
        <div>
          <div
            style={{
              color:
                "#22d3ee",

              fontSize: 10,

              fontWeight: 800,

              letterSpacing:
                "0.18em",

              textTransform:
                "uppercase",
            }}
          >
            QuantLab · Research
            Workstation
          </div>

          <h1
            style={{
              margin:
                "8px 0 8px",

              fontSize:
                "clamp(27px, 3.3vw, 40px)",

              lineHeight: 1,
            }}
          >
            American Option
            Surface Atlas
          </h1>

          <p
            style={{
              margin: 0,

              maxWidth: 790,

              color:
                "#94a3b8",

              lineHeight: 1.6,

              fontSize: 14,
            }}
          >
            Interactive comparison of
            lattice, projected
            finite-difference and
            physics-informed neural
            approximations across the
            American put state space.
          </p>
        </div>


        <div
          style={{
            display: "grid",

            gap: 8,

            justifyItems: "end",
          }}
        >
          <Badge
            text="American Put"
            color="#c4b5fd"
          />

          <Badge
            text={
              data.pinn.available
                ? "PINN Artifact Loaded"
                : "PINN Artifact Unavailable"
            }
            color={
              data.pinn.available
                ? "#6ee7b7"
                : "#fbbf24"
            }
          />
        </div>
      </div>
    </header>
  );
}


function Badge({
  text,
  color,
}: {
  text: string;
  color: string;
}) {
  return (
    <div
      style={{
        padding:
          "6px 10px",

        borderRadius: 999,

        border:
          `1px solid ${color}44`,

        background:
          `${color}10`,

        color,

        fontSize: 10,

        fontWeight: 800,

        letterSpacing:
          "0.08em",

        textTransform:
          "uppercase",
      }}
    >
      {text}
    </div>
  );
}


function KpiStrip({
  data,
}: {
  data:
    AmericanSurfaceAtlasResult;
}) {
  const items = [
    {
      label: "Strike K",
      value:
        data.input.strike.toFixed(
          2
        ),
    },

    {
      label: "Volatility σ",
      value: `${(
        data.input.volatility *
        100
      ).toFixed(1)}%`,
    },

    {
      label: "Rate r",
      value: `${(
        data.input.rate * 100
      ).toFixed(2)}%`,
    },

    {
      label: "Maturity T",
      value: `${data.input.maturity.toFixed(
        2
      )}Y`,
    },

    {
      label: "CRR Max Error",
      value:
        data.summary
          .max_crr_absolute_error
          .toFixed(5),
    },

    {
      label: "PINN RMSE",
      value:
        data.pinn.rmse_vs_cn !==
        null
          ? data.pinn.rmse_vs_cn.toFixed(
              5
            )
          : "—",
    },

    {
      label: "PINN MAE",
      value:
        data.pinn.mae_vs_cn !==
        null
          ? data.pinn.mae_vs_cn.toFixed(
              5
            )
          : "—",
    },

    {
      label: "PINN Max Error",
      value:
        data.pinn
          .max_absolute_error_vs_cn !==
        null
          ? data.pinn
              .max_absolute_error_vs_cn
              .toFixed(5)
          : "—",
    },
  ];


  return (
    <div
      style={{
        display: "grid",

        gridTemplateColumns:
          "repeat(auto-fit, minmax(125px, 1fr))",

        gap: 9,
      }}
    >
      {items.map(
        (item) => (
          <div
            key={item.label}
            className="ql-card"
            style={{
              padding:
                "12px 14px",
            }}
          >
            <div
              style={{
                color:
                  "#64748b",

                fontSize: 9,

                textTransform:
                  "uppercase",

                letterSpacing:
                  "0.11em",

                marginBottom: 5,
              }}
            >
              {item.label}
            </div>

            <div
              style={{
                color:
                  "#e2e8f0",

                fontSize: 15,

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


function SectionHeading({
  eyebrow,
  title,
  description,
}: {
  eyebrow: string;
  title: string;
  description: ReactNode;
}) {
  return (
    <div
      style={{
        display: "flex",

        justifyContent:
          "space-between",

        alignItems:
          "flex-end",

        gap: 30,

        flexWrap: "wrap",

        padding:
          "14px 2px 0",
      }}
    >
      <div>
        <div
          style={{
            color: "#8b5cf6",

            fontSize: 10,

            fontWeight: 800,

            letterSpacing:
              "0.15em",

            textTransform:
              "uppercase",
          }}
        >
          {eyebrow}
        </div>

        <h2
          style={{
            margin:
              "5px 0 0",

            fontSize: 21,
          }}
        >
          {title}
        </h2>
      </div>


      <p
        style={{
          margin: 0,

          color:
            "#64748b",

          fontSize: 12,

          lineHeight: 1.55,

          maxWidth: 560,
        }}
      >
        {description}
      </p>
    </div>
  );
}


function SurfacePanel({
  number,
  eyebrow,
  title,
  equation,
  accent,
  children,
}: {
  number: string;
  eyebrow: string;
  title: string;
  equation: string;
  accent: string;
  children: ReactNode;
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

          top: 12,
          right: 15,

          color:
            "rgba(148,163,184,0.16)",

          fontSize: 26,

          fontWeight: 900,

          zIndex: 2,
        }}
      >
        {number}
      </div>


      <div
        style={{
          padding:
            "15px 18px 0",
        }}
      >
        <div
          style={{
            color: accent,

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

        <h3
          style={{
            margin:
              "4px 0 3px",

            fontSize: 16,
          }}
        >
          {title}
        </h3>

        <code
          style={{
            color:
              "#64748b",

            fontSize: 10,
          }}
        >
          {equation}
        </code>
      </div>

      {children}
    </article>
  );
}


function SurfacePlot({
  x,
  y,
  z,
  zTitle,
  colorTitle,
  colorscale,
  sceneBase,
  height,
  symmetricRange,
  cmin,
  cmax,
}: {
  x: number[];
  y: number[];
  z: number[][];
  zTitle: string;
  colorTitle: string;
  colorscale: string;
  sceneBase: Record<
    string,
    unknown
  >;
  height: number;
  symmetricRange?: number;
  cmin?: number;
  cmax?: number;
}) {
  const range =
    symmetricRange &&
    symmetricRange > 0
      ? {
          cmin:
            -symmetricRange,

          cmax:
            symmetricRange,
        }
      : {
          ...(cmin !== undefined
            ? { cmin }
            : {}),

          ...(cmax !== undefined
            ? { cmax }
            : {}),
        };


  return (
    <Plot
      data={[
        {
          type: "surface",

          x,
          y,
          z,

          colorscale,

          ...range,

          colorbar: {
            title: {
              text:
                colorTitle,
            },

            thickness: 9,

            len: 0.72,
          },

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
            "z=%{z:.6f}" +
            "<extra></extra>",
        },
      ]}
      layout={{
        autosize: true,

        height,

        margin: {
          l: 0,
          r: 0,
          t: 4,
          b: 0,
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

        scene: {
          ...sceneBase,

          zaxis: {
            ...AXIS_STYLE,

            title: {
              text: zTitle,
            },
          },
        },
      }}
      config={{
        responsive: true,

        displaylogo: false,

        scrollZoom: true,

        toImageButtonOptions: {
          format: "png",

          filename:
            "quantlab-surface",
        },
      }}
      style={{
        width: "100%",
      }}
    />
  );
}


function SurfaceWithBoundary({
  data,
  boundary,
  boundaryZ,
  sceneBase,
}: {
  data:
    AmericanSurfaceAtlasResult;

  boundary: Array<{
    time_to_maturity: number;
    spot: number;
  }>;

  boundaryZ: number[];

  sceneBase: Record<
    string,
    unknown
  >;
}) {
  return (
    <Plot
      data={[
        {
          type: "surface",

          x:
            data.grid.spot,

          y:
            data.grid
              .time_to_maturity,

          z:
            data.surfaces
              .crank_nicolson,

          colorscale:
            "Turbo",

          cmin:
            data.summary.min_price,

          cmax:
            data.summary.max_price,

          colorbar: {
            title: {
              text: "V",
            },

            thickness: 9,

            len: 0.72,
          },

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
            "V=%{z:.6f}" +
            "<extra></extra>",
        },

        {
          type: "scatter3d",

          mode: "lines",

          x:
            boundary.map(
              (point) =>
                point.spot
            ),

          y:
            boundary.map(
              (point) =>
                point
                  .time_to_maturity
            ),

          z: boundaryZ,

          line: {
            color:
              "#ffffff",

            width: 6,
          },

          name: "S*(τ)",

          hovertemplate:
            "S*=%{x:.2f}<br>" +
            "τ=%{y:.3f}" +
            "<extra></extra>",
        },
      ]}
      layout={{
        autosize: true,

        height: 365,

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
          ...sceneBase,

          zaxis: {
            ...AXIS_STYLE,

            title: {
              text:
                "Option Value",
            },
          },
        },

        showlegend: false,
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
  );
}


function PinnDiagnostics({
  data,
}: {
  data:
    AmericanSurfaceAtlasResult;
}) {
  const metrics = [
    {
      label:
        "Training Loss",

      value:
        data.pinn.final_loss !==
        null
          ? scientific(
              data.pinn.final_loss
            )
          : "—",
    },

    {
      label:
        "Training Time",

      value:
        data.pinn
          .training_seconds !==
        null
          ? `${data.pinn.training_seconds.toFixed(
              1
            )} s`
          : "—",
    },

    {
      label:
        "MAE vs CN",

      value:
        data.pinn.mae_vs_cn !==
        null
          ? data.pinn.mae_vs_cn.toFixed(
              6
            )
          : "—",
    },

    {
      label:
        "RMSE vs CN",

      value:
        data.pinn.rmse_vs_cn !==
        null
          ? data.pinn.rmse_vs_cn.toFixed(
              6
            )
          : "—",
    },

    {
      label:
        "Max |Error|",

      value:
        data.pinn
          .max_absolute_error_vs_cn !==
        null
          ? data.pinn
              .max_absolute_error_vs_cn
              .toFixed(6)
          : "—",
    },
  ];


  return (
    <article
      className="ql-card"
      style={{
        padding:
          "16px 18px",
      }}
    >
      <div
        style={{
          display: "flex",

          justifyContent:
            "space-between",

          gap: 20,

          alignItems:
            "center",

          flexWrap: "wrap",
        }}
      >
        <div>
          <div
            style={{
              color:
                "#34d399",

              fontSize: 9,

              fontWeight: 800,

              letterSpacing:
                "0.14em",

              textTransform:
                "uppercase",
            }}
          >
            Neural Solver Artifact
          </div>

          <div
            style={{
              marginTop: 4,

              color:
                "#cbd5e1",

              fontSize: 13,

              fontWeight: 650,
            }}
          >
            {data.pinn.method ??
              "PINN V2"}
          </div>
        </div>


        <div
          style={{
            display: "grid",

            gridTemplateColumns:
              "repeat(5, minmax(100px, 1fr))",

            gap: 9,

            flex: 1,

            minWidth: 620,
          }}
        >
          {metrics.map(
            (metric) => (
              <div
                key={
                  metric.label
                }
                style={{
                  padding:
                    "9px 11px",

                  border:
                    "1px solid rgba(148,163,184,0.10)",

                  borderRadius: 8,

                  background:
                    "rgba(15,23,42,0.42)",
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
                      "0.09em",
                  }}
                >
                  {metric.label}
                </div>

                <div
                  style={{
                    marginTop: 4,

                    color:
                      "#e2e8f0",

                    fontSize: 12,

                    fontWeight: 700,
                  }}
                >
                  {metric.value}
                </div>
              </div>
            )
          )}
        </div>
      </div>
    </article>
  );
}


function BoundaryHeatmap({
  data,
  boundary,
}: {
  data:
    AmericanSurfaceAtlasResult;

  boundary: Array<{
    time_to_maturity: number;
    spot: number;
  }>;
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
          Regime Map
        </div>

        <h3
          style={{
            margin:
              "4px 0 3px",

            fontSize: 16,
          }}
        >
          Free-Boundary Geometry
        </h3>

        <code
          style={{
            color:
              "#64748b",

            fontSize: 10,
          }}
        >
          S*(τ)
        </code>
      </div>


      <Plot
        data={[
          {
            type: "heatmap",

            x:
              data.grid.spot,

            y:
              data.grid
                .time_to_maturity,

            z:
              data.surfaces
                .exercise_gap,

            colorscale:
              "Viridis",

            colorbar: {
              title: {
                text: "V − Φ",
              },

              thickness: 10,
            },

            hovertemplate:
              "S=%{x:.2f}<br>" +
              "τ=%{y:.3f}<br>" +
              "Gap=%{z:.6f}" +
              "<extra></extra>",
          },

          {
            type: "scatter",

            mode: "lines",

            x:
              boundary.map(
                (point) =>
                  point.spot
              ),

            y:
              boundary.map(
                (point) =>
                  point
                    .time_to_maturity
              ),

            line: {
              color:
                "#ffffff",

              width: 3,
            },

            name: "S*(τ)",
          },

          {
            type: "scatter",

            mode: "lines",

            x: [
              data.input.strike,
              data.input.strike,
            ],

            y: [
              0,
              data.input.maturity,
            ],

            line: {
              color:
                "#fbbf24",

              width: 1,

              dash: "dot",
            },

            name: "Strike K",
          },
        ]}
        layout={{
          autosize: true,

          height: 390,

          margin: {
            l: 60,
            r: 30,
            t: 25,
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
              text: "Spot S",
            },

            gridcolor:
              "rgba(148,163,184,0.12)",
          },

          yaxis: {
            title: {
              text:
                "Time to maturity τ",
            },

            gridcolor:
              "rgba(148,163,184,0.12)",
          },

          legend: {
            orientation: "h",

            x: 0,

            y: 1.1,
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


function UnavailableSurface() {
  return (
    <div
      style={{
        height: 365,

        display: "grid",

        placeItems: "center",

        padding: 30,

        textAlign: "center",

        color: "#64748b",
      }}
    >
      PINN artifact does not match
      the current model parameters.
    </div>
  );
}


function ResearchNote() {
  return (
    <article
      className="ql-card"
      style={{
        padding:
          "18px 20px",

        borderLeft:
          "3px solid rgba(139,92,246,0.65)",
      }}
    >
      <div
        style={{
          color:
            "#a78bfa",

          fontSize: 9,

          fontWeight: 800,

          letterSpacing:
            "0.14em",

          textTransform:
            "uppercase",

          marginBottom: 7,
        }}
      >
        Research Interpretation
      </div>

      <p
        style={{
          margin: 0,

          color:
            "#94a3b8",

          lineHeight: 1.65,

          fontSize: 12,
        }}
      >
        Crank–Nicolson is a numerical
        reference here rather than an
        analytical ground truth. The
        signed surfaces reveal directional
        bias, while absolute-error
        geometry identifies regions of
        state space where approximation
        quality deteriorates. Particular
        attention should be paid to the
        neighbourhood of the
        early-exercise boundary, where
        the American obstacle introduces
        non-smooth solution behaviour.
      </p>
    </article>
  );
}


function nearestIndex(
  values: number[],
  target: number
) {
  let bestIndex = 0;
  let bestDistance =
    Infinity;

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

        bestIndex = index;
      }
    }
  );

  return bestIndex;
}


function scientific(
  value: number
) {
  return value.toExponential(3);
}