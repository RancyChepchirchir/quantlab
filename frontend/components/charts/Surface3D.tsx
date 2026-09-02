"use client";

import dynamic from "next/dynamic";

const Plot = dynamic(() => import("react-plotly.js"), {
  ssr: false,
});

type Surface3DProps = {
  x: number[];
  y: number[];
  z: number[][];
  xTitle: string;
  yTitle: string;
  zTitle: string;
  title?: string;
  height?: number;
  hoverTemplate?: string;
};

export default function Surface3D({
  x,
  y,
  z,
  xTitle,
  yTitle,
  zTitle,
  title,
  height = 430,
  hoverTemplate,
}: Surface3DProps) {
  return (
    <div
      style={{
        width: "100%",
        height,
        minHeight: height,
      }}
    >
      <Plot
        data={[
          {
            type: "surface",
            x,
            y,
            z,
            colorscale: "Turbo",
            showscale: true,

            colorbar: {
              title: {
                text: zTitle,
                side: "right",
              },
              thickness: 10,
              len: 0.68,
              x: 0.98,
              tickfont: {
                color: "#8f9bb3",
                size: 9,
              },
              titlefont: {
                color: "#aab5c9",
                size: 9,
              },
              outlinewidth: 0,
            },

            contours: {
              z: {
                show: true,
                usecolormap: true,
                highlightcolor: "#ffffff",
                project: {
                  z: true,
                },
              },
            },

            hovertemplate:
              hoverTemplate ??
              `${xTitle}: %{x:.4f}<br>` +
                `${yTitle}: %{y:.4f}<br>` +
                `${zTitle}: %{z:.4f}<extra></extra>`,
          },
        ]}
        layout={{
          title: title
            ? {
                text: title,
                font: {
                  color: "#eef2fb",
                  size: 13,
                },
                x: 0.02,
                xanchor: "left",
              }
            : undefined,

          autosize: true,

          margin: {
            l: 0,
            r: 10,
            t: title ? 38 : 10,
            b: 0,
          },

          paper_bgcolor: "rgba(0,0,0,0)",
          plot_bgcolor: "rgba(0,0,0,0)",

          font: {
            family:
              "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif",
            color: "#8996ae",
            size: 10,
          },

          scene: {
            bgcolor: "rgba(0,0,0,0)",

            camera: {
              eye: {
                x: 1.45,
                y: 1.45,
                z: 0.85,
              },
            },

            xaxis: {
              title: {
                text: xTitle,
                font: {
                  color: "#a8b3c7",
                  size: 10,
                },
              },

              tickfont: {
                color: "#75829b",
                size: 9,
              },

              gridcolor: "rgba(111, 130, 170, 0.15)",
              zerolinecolor: "rgba(111, 130, 170, 0.18)",
              showbackground: true,
              backgroundcolor: "rgba(6, 12, 25, 0.35)",
            },

            yaxis: {
              title: {
                text: yTitle,
                font: {
                  color: "#a8b3c7",
                  size: 10,
                },
              },

              tickfont: {
                color: "#75829b",
                size: 9,
              },

              gridcolor: "rgba(111, 130, 170, 0.15)",
              zerolinecolor: "rgba(111, 130, 170, 0.18)",
              showbackground: true,
              backgroundcolor: "rgba(6, 12, 25, 0.35)",
            },

            zaxis: {
              title: {
                text: zTitle,
                font: {
                  color: "#a8b3c7",
                  size: 10,
                },
              },

              tickfont: {
                color: "#75829b",
                size: 9,
              },

              gridcolor: "rgba(111, 130, 170, 0.15)",
              zerolinecolor: "rgba(111, 130, 170, 0.18)",
              showbackground: true,
              backgroundcolor: "rgba(6, 12, 25, 0.35)",
            },
          },
        }}
        config={{
          responsive: true,
          displaylogo: false,
          scrollZoom: true,

          modeBarButtonsToRemove: [
            "sendDataToCloud",
            "lasso2d",
            "select2d",
          ],

          toImageButtonOptions: {
            format: "png",
            filename: "quantlab-surface",
            height: 900,
            width: 1400,
            scale: 2,
          },
        }}
        style={{
          width: "100%",
          height: "100%",
        }}
        useResizeHandler
      />
    </div>
  );
}