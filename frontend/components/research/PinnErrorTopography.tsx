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


export default function PinnErrorTopography({
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


  const epoch =
    convergence.epochs[
      convergence.epochs.length - 1
    ];

  const key =
    String(epoch);

  const errorSurface =
    convergence
      .absolute_errors[
        key
      ];


  if (
    !errorSurface ||
    errorSurface.length === 0
  ) {
    return null;
  }


  const spotGrid =
    data.grid.spot;

  const tauGrid =
    data.grid.time_to_maturity;


  const boundary =
    data.exercise_boundary
      .filter(
        (
          point
        ): point is {
          time_to_maturity: number;
          spot: number;
        } =>
          point.spot !== null
      );


  /*
   * To draw the stopping boundary across
   * the error landscape we need the error
   * height at each boundary location.
   *
   * We use nearest-grid interpolation here
   * purely for visualization. The boundary
   * itself still comes from the CN exercise
   * diagnostic.
   */

  const boundaryTau:
    number[] = [];

  const boundarySpot:
    number[] = [];

  const boundaryError:
    number[] = [];


  for (
    const point
    of boundary
  ) {
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


    const error =
      errorSurface[
        tauIndex
      ]?.[
        spotIndex
      ];


    if (
      error === undefined ||
      !Number.isFinite(
        error
      )
    ) {
      continue;
    }


    boundaryTau.push(
      point
        .time_to_maturity
    );

    boundarySpot.push(
      point.spot
    );

    boundaryError.push(
      error
    );
  }


  return (
    <section
      style={{
        display: "grid",
        gap: 12,
      }}
    >
      <header
        className="ql-card"
        style={{
          padding:
            "19px 21px",

          background:
            "radial-gradient(circle at 88% 5%, rgba(244,63,94,0.11), transparent 32%), radial-gradient(circle at 8% 100%, rgba(34,211,238,0.08), transparent 34%)",
        }}
      >
        <div
          style={{
            color:
              "#fb7185",

            fontSize: 8,

            fontWeight: 800,

            letterSpacing:
              "0.14em",

            textTransform:
              "uppercase",
          }}
        >
          PINN Spatial Residual
        </div>

        <h2
          style={{
            margin:
              "5px 0 5px",

            fontSize: 21,
          }}
        >
          3D Error Topography
          + Free-Boundary Ridge
        </h2>

        <p
          style={{
            margin: 0,

            color:
              "#94a3b8",

            maxWidth: 820,

            fontSize: 10,

            lineHeight: 1.7,
          }}
        >
          Absolute PINN pricing
          error relative to the
          projected Crank–Nicolson
          reference, with the
          numerically estimated
          American exercise boundary
          embedded directly into the
          error landscape.
        </p>
      </header>


      <article
        className="ql-card"
        style={{
          padding:
            "10px 10px 3px",
        }}
      >
        <Plot
          data={[
            {
              type:
                "surface",

              x:
                spotGrid,

              y:
                tauGrid,

              z:
                errorSurface,

              name:
                "|PINN − CN|",

              colorbar: {
                title: {
                  text:
                    "|Error|",
                },

                thickness: 10,

                len: 0.72,
              },

              contours: {
                z: {
                  show: true,

                  usecolormap:
                    true,

                  highlightcolor:
                    "#ffffff",

                  project: {
                    z: true,
                  },
                },
              },

              hovertemplate:
                "S=%{x:.2f}<br>" +
                "τ=%{y:.3f}<br>" +
                "|PINN−CN|=%{z:.6f}" +
                "<extra></extra>",
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

              name:
                "CN free boundary",

              line: {
                width: 8,

                color:
                  "#ffffff",
              },

              marker: {
                size: 2,

                color:
                  "#ffffff",
              },

              hovertemplate:
                "Boundary<br>" +
                "S*=%{x:.2f}<br>" +
                "τ=%{y:.3f}<br>" +
                "|Error|=%{z:.6f}" +
                "<extra></extra>",
            },
          ]}
          layout={{
            autosize: true,

            height: 620,

            margin: {
              l: 0,
              r: 0,
              t: 25,
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
              bgcolor:
                "rgba(0,0,0,0)",

              xaxis: {
                title: {
                  text:
                    "Spot S",
                },

                gridcolor:
                  "rgba(148,163,184,0.12)",

                zerolinecolor:
                  "rgba(148,163,184,0.15)",
              },

              yaxis: {
                title: {
                  text:
                    "Time to maturity τ",
                },

                gridcolor:
                  "rgba(148,163,184,0.12)",

                zerolinecolor:
                  "rgba(148,163,184,0.15)",
              },

              zaxis: {
                title: {
                  text:
                    "|PINN − CN|",
                },

                gridcolor:
                  "rgba(148,163,184,0.12)",
              },

              camera: {
                eye: {
                  x: 1.55,
                  y: -1.75,
                  z: 1.15,
                },
              },

              aspectratio: {
                x: 1.45,
                y: 1.0,
                z: 0.72,
              },
            },

            legend: {
              x: 0.02,
              y: 0.98,

              bgcolor:
                "rgba(2,6,23,0.55)",
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


      <div
        style={{
          display: "grid",

          gridTemplateColumns:
            "repeat(auto-fit, minmax(190px, 1fr))",

          gap: 8,
        }}
      >
        <MetricCard
          label="Training checkpoint"
          value={
            `${epoch.toLocaleString()} epochs`
          }
        />

        <MetricCard
          label="Surface definition"
          value="|VPINN − VCN|"
        />

        <MetricCard
          label="Boundary source"
          value="Projected CN"
        />

        <MetricCard
          label="Boundary geometry"
          value="S*(τ)"
        />
      </div>


      <article
        className="ql-card"
        style={{
          padding:
            "16px 18px",

          borderLeft:
            "3px solid rgba(244,63,94,0.65)",
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
          How to read this surface
        </div>

        <p
          style={{
            margin:
              "7px 0 0",

            color:
              "#94a3b8",

            fontSize: 10,

            lineHeight: 1.75,
          }}
        >
          Peaks represent regions
          where the trained PINN
          departs most strongly from
          the projected
          Crank–Nicolson reference.
          The overlaid curve is the
          estimated American stopping
          boundary S*(τ). Visual
          alignment between persistent
          error ridges and this curve
          provides a geometric
          complement to the
          grid-distance diagnostics
          above; it should be treated
          as descriptive evidence
          rather than an analytical
          free-boundary solution.
        </p>
      </article>
    </section>
  );
}


function MetricCard({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div
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

          fontSize: 7,

          letterSpacing:
            "0.08em",

          textTransform:
            "uppercase",
        }}
      >
        {label}
      </div>

      <strong
        style={{
          display: "block",

          marginTop: 4,

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


function nearestIndex(
  values: number[],
  target: number
) {
  let bestIndex = 0;

  let bestDistance =
    Infinity;


  for (
    let index = 0;
    index < values.length;
    index += 1
  ) {
    const distance =
      Math.abs(
        values[index]
        - target
      );

    if (
      distance
      < bestDistance
    ) {
      bestDistance =
        distance;

      bestIndex =
        index;
    }
  }


  return bestIndex;
}