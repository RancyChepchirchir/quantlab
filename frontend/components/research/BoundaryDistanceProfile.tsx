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


type DistanceProfile =
  AmericanSurfaceAtlasResult[
    "pinn_convergence"
  ][
    "boundary_distance_profiles"
  ][string];


export default function BoundaryDistanceProfile({
  data,
}: Props) {
  const convergence =
    data.pinn_convergence;

  const profiles =
    convergence
      .boundary_distance_profiles;


  if (
    !convergence.available ||
    convergence.epochs.length === 0 ||
    Object.keys(
      profiles
    ).length === 0
  ) {
    return null;
  }


  const rows =
    convergence.epochs
      .map(
        (epoch) => ({
          epoch,

          profile:
            profiles[
              String(epoch)
            ],
        })
      )
      .filter(
        (
          item
        ): item is {
          epoch: number;
          profile:
            DistanceProfile;
        } =>
          Boolean(
            item.profile
          )
      );


  if (
    rows.length === 0
  ) {
    return null;
  }


  const last =
    rows[
      rows.length - 1
    ];

  const lastProfile =
    last.profile;

  const validBins =
    lastProfile.bins.filter(
      (bin) =>
        bin.mae !== null
    );


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
            "18px 20px",

          background:
            "radial-gradient(circle at 85% 10%, rgba(34,211,238,0.09), transparent 32%), radial-gradient(circle at 10% 100%, rgba(139,92,246,0.09), transparent 34%)",
        }}
      >
        <div
          style={{
            display: "flex",

            justifyContent:
              "space-between",

            gap: 24,

            alignItems:
              "flex-end",

            flexWrap:
              "wrap",
          }}
        >
          <div>
            <div
              style={{
                color:
                  "#22d3ee",

                fontSize: 8,

                fontWeight: 800,

                letterSpacing:
                  "0.14em",

                textTransform:
                  "uppercase",
              }}
            >
              Spatial Error Geometry
            </div>

            <h2
              style={{
                margin:
                  "5px 0 5px",

                fontSize: 20,
              }}
            >
              Error vs Distance
              from the Free Boundary
            </h2>

            <p
              style={{
                margin: 0,

                maxWidth: 760,

                color:
                  "#94a3b8",

                fontSize: 10,

                lineHeight: 1.7,
              }}
            >
              Measures PINN pricing
              error across normalized
              distance bands from the
              CN-estimated American
              exercise boundary.
            </p>
          </div>


          <div
            style={{
              display: "grid",

              gridTemplateColumns:
                "repeat(2, auto)",

              gap: 8,
            }}
          >
            <SmallStat
              label="Final Epoch"
              value={
                last.epoch
                  .toLocaleString()
              }
            />

            <SmallStat
              label="Observations"
              value={
                lastProfile
                  .observation_count
                  .toLocaleString()
              }
            />
          </div>
        </div>
      </header>


      <div
        style={{
          display: "grid",

          gridTemplateColumns:
            "minmax(0, 1.45fr) minmax(270px, 0.55fr)",

          gap: 12,
        }}
      >
        <DistanceErrorChart
          rows={rows}
        />

        <CorrelationPanel
          rows={rows}
        />
      </div>


      <ErrorStatisticChart
        epoch={last.epoch}
        profile={lastProfile}
      />


      <div
        style={{
          display: "grid",

          gridTemplateColumns:
            "repeat(auto-fit, minmax(150px, 1fr))",

          gap: 8,
        }}
      >
        {validBins.map(
          (bin) => (
            <DistanceBandCard
              key={bin.label}
              bin={bin}
            />
          )
        )}
      </div>


      <ProfileInterpretation
        epoch={last.epoch}
        profile={lastProfile}
      />
    </section>
  );
}


function DistanceErrorChart({
  rows,
}: {
  rows: Array<{
    epoch: number;
    profile:
      DistanceProfile;
  }>;
}) {
  const labels =
    rows[0]
      .profile
      .bins
      .map(
        (bin) =>
          bin.label
      );


  const traces =
    rows.map(
      ({
        epoch,
        profile,
      }) => ({
        type:
          "scatter" as const,

        mode:
          "lines+markers" as const,

        name:
          `${epoch} epochs`,

        x: labels,

        y:
          profile.bins.map(
            (bin) =>
              bin.mae
              ?? NaN
          ),

        line: {
          width: 2.5,
        },

        marker: {
          size: 7,
        },

        hovertemplate:
          "Distance=%{x}<br>" +
          "MAE=%{y:.6f}" +
          "<extra></extra>",
      })
    );


  return (
    <article
      className="ql-card"
      style={{
        padding:
          "15px 17px 4px",
      }}
    >
      <div
        style={{
          color:
            "#a78bfa",

          fontSize: 8,

          fontWeight: 800,

          textTransform:
            "uppercase",

          letterSpacing:
            "0.12em",
        }}
      >
        Distance Profile
      </div>

      <h3
        style={{
          margin:
            "4px 0 0",

          fontSize: 15,
        }}
      >
        Mean Absolute Error
        by Boundary Distance
      </h3>


      <Plot
        data={traces}
        layout={{
          autosize: true,

          height: 350,

          margin: {
            l: 65,
            r: 25,
            t: 40,
            b: 60,
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
                "Distance from S*(τ) [grid spacings ΔS]",
            },

            gridcolor:
              "rgba(148,163,184,0.08)",
          },

          yaxis: {
            title: {
              text:
                "Mean Absolute Error",
            },

            gridcolor:
              "rgba(148,163,184,0.10)",

            rangemode:
              "tozero",
          },

          legend: {
            orientation:
              "h",

            x: 0,

            y: 1.16,
          },

          hovermode:
            "x unified",
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


function CorrelationPanel({
  rows,
}: {
  rows: Array<{
    epoch: number;
    profile:
      DistanceProfile;
  }>;
}) {
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
        Spatial Correlation
      </div>

      <h3
        style={{
          margin:
            "4px 0 14px",

          fontSize: 14,
        }}
      >
        Distance ↔ Error
      </h3>


      {rows.map(
        ({
          epoch,
          profile,
        }) => {
          const correlation =
            profile
              .distance_error_correlation;

          return (
            <div
              key={epoch}
              style={{
                padding:
                  "10px 0",

                borderBottom:
                  "1px solid rgba(148,163,184,0.07)",
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
                <span
                  style={{
                    color:
                      "#64748b",

                    fontSize: 9,
                  }}
                >
                  {epoch.toLocaleString()}
                  {" "}epochs
                </span>

                <strong
                  style={{
                    color:
                      correlation === null
                        ? "#64748b"
                        : correlation < 0
                          ? "#fb7185"
                          : "#34d399",

                    fontSize: 15,
                  }}
                >
                  {correlation === null
                    ? "—"
                    : correlation
                        .toFixed(3)}
                </strong>
              </div>

              <div
                style={{
                  marginTop: 5,

                  color:
                    "#475569",

                  fontSize: 8,
                }}
              >
                {correlationText(
                  correlation
                )}
              </div>
            </div>
          );
        }
      )}


      <p
        style={{
          margin:
            "16px 0 0",

          color:
            "#64748b",

          fontSize: 9,

          lineHeight: 1.65,
        }}
      >
        Negative correlation means
        larger errors tend to occur
        closer to the estimated free
        boundary. Positive correlation
        means error tends to increase
        with distance from it.
      </p>
    </article>
  );
}


function ErrorStatisticChart({
  epoch,
  profile,
}: {
  epoch: number;
  profile:
    DistanceProfile;
}) {
  const labels =
    profile.bins.map(
      (bin) =>
        bin.label
    );


  return (
    <article
      className="ql-card"
      style={{
        padding:
          "15px 17px 4px",
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
        Distribution Shape
      </div>

      <h3
        style={{
          margin:
            "4px 0 0",

          fontSize: 15,
        }}
      >
        {epoch.toLocaleString()}
        {" "}Epoch Error Statistics
      </h3>


      <Plot
        data={[
          {
            type: "bar",

            name: "Median",

            x: labels,

            y:
              profile.bins.map(
                (bin) =>
                  bin
                    .median_absolute_error
                  ?? NaN
              ),
          },

          {
            type: "bar",

            name: "MAE",

            x: labels,

            y:
              profile.bins.map(
                (bin) =>
                  bin.mae
                  ?? NaN
              ),
          },

          {
            type: "bar",

            name: "P90",

            x: labels,

            y:
              profile.bins.map(
                (bin) =>
                  bin
                    .p90_absolute_error
                  ?? NaN
              ),
          },
        ]}
        layout={{
          autosize: true,

          height: 300,

          barmode:
            "group",

          margin: {
            l: 65,
            r: 25,
            t: 35,
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
                "|S − S*(τ)| / ΔS",
            },

            gridcolor:
              "rgba(148,163,184,0.06)",
          },

          yaxis: {
            title: {
              text:
                "Absolute Pricing Error",
            },

            rangemode:
              "tozero",

            gridcolor:
              "rgba(148,163,184,0.10)",
          },

          legend: {
            orientation:
              "h",

            x: 0,

            y: 1.17,
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


function DistanceBandCard({
  bin,
}: {
  bin:
    DistanceProfile[
      "bins"
    ][number];
}) {
  return (
    <article
      className="ql-card"
      style={{
        padding:
          "13px 14px",
      }}
    >
      <div
        style={{
          color:
            "#a78bfa",

          fontSize: 8,

          fontWeight: 800,

          letterSpacing:
            "0.08em",

          textTransform:
            "uppercase",
        }}
      >
        {bin.label}
      </div>

      <div
        style={{
          margin:
            "7px 0 10px",

          color:
            "#f8fafc",

          fontSize: 17,

          fontWeight: 800,
        }}
      >
        {formatNumber(
          bin.mae,
          6
        )}
      </div>

      <MetricRow
        label="Samples"
        value={
          bin.count
            .toLocaleString()
        }
      />

      <MetricRow
        label="Median"
        value={
          formatNumber(
            bin
              .median_absolute_error,
            6
          )
        }
      />

      <MetricRow
        label="RMSE"
        value={
          formatNumber(
            bin.rmse,
            6
          )
        }
      />

      <MetricRow
        label="P90"
        value={
          formatNumber(
            bin
              .p90_absolute_error,
            6
          )
        }
      />
    </article>
  );
}


function ProfileInterpretation({
  epoch,
  profile,
}: {
  epoch: number;
  profile:
    DistanceProfile;
}) {
  const valid =
    profile.bins.filter(
      (
        bin
      ): bin is typeof bin & {
        mae: number;
      } =>
        bin.mae !== null
    );


  if (
    valid.length < 2
  ) {
    return null;
  }


  const nearest =
    valid[0];

  const furthest =
    valid[
      valid.length - 1
    ];

  const ratio =
    furthest.mae > 0
      ? (
          nearest.mae
          / furthest.mae
        )
      : null;


  return (
    <article
      className="ql-card"
      style={{
        padding:
          "17px 19px",

        borderLeft:
          "3px solid rgba(34,211,238,0.60)",
      }}
    >
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
        Spatial Interpretation
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
        At{" "}
        <strong
          style={{
            color:
              "#e2e8f0",
          }}
        >
          {epoch.toLocaleString()}
        </strong>
        {" "}epochs, the nearest
        boundary-distance band has
        MAE{" "}
        <strong
          style={{
            color:
              "#e2e8f0",
          }}
        >
          {formatNumber(
            nearest.mae,
            6
          )}
        </strong>
        , compared with{" "}
        <strong
          style={{
            color:
              "#e2e8f0",
          }}
        >
          {formatNumber(
            furthest.mae,
            6
          )}
        </strong>
        {" "}in the furthest band.
        The corresponding near/far
        ratio is{" "}
        <strong
          style={{
            color:
              "#f8fafc",
          }}
        >
          {ratio === null
            ? "—"
            : `${ratio.toFixed(
                3
              )}×`}
        </strong>
        . This is a descriptive
        spatial diagnostic rather
        than a statistical test.
      </p>
    </article>
  );
}


function SmallStat({
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
          "8px 11px",
      }}
    >
      <div
        style={{
          color:
            "#64748b",

          fontSize: 7,

          textTransform:
            "uppercase",

          letterSpacing:
            "0.08em",
        }}
      >
        {label}
      </div>

      <strong
        style={{
          display: "block",

          marginTop: 3,

          fontSize: 12,
        }}
      >
        {value}
      </strong>
    </div>
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

        gap: 10,

        padding:
          "4px 0",
      }}
    >
      <span
        style={{
          color:
            "#64748b",

          fontSize: 8,
        }}
      >
        {label}
      </span>

      <strong
        style={{
          color:
            "#cbd5e1",

          fontSize: 9,
        }}
      >
        {value}
      </strong>
    </div>
  );
}


function correlationText(
  value: number | null
) {
  if (value === null) {
    return "Insufficient variation";
  }

  if (value <= -0.5) {
    return "Strong inverse association";
  }

  if (value <= -0.2) {
    return "Moderate inverse association";
  }

  if (value < 0) {
    return "Weak inverse association";
  }

  if (value < 0.2) {
    return "Weak positive association";
  }

  if (value < 0.5) {
    return "Moderate positive association";
  }

  return "Strong positive association";
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