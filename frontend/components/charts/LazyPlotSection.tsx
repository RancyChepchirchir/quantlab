"use client";

import {
  ReactNode,
  useEffect,
  useRef,
  useState,
} from "react";

type Props = {
  children: ReactNode;

  rootMargin?: string;

  minHeight?: number;

  unloadWhenHidden?: boolean;
};

export default function LazyPlotSection({
  children,
  rootMargin = "700px 0px",
  minHeight = 420,
  unloadWhenHidden = true,
}: Props) {
  const ref =
    useRef<HTMLDivElement | null>(
      null
    );

  const [mounted, setMounted] =
    useState(false);

  useEffect(() => {
    const element =
      ref.current;

    if (!element) {
      return;
    }

    const observer =
      new IntersectionObserver(
        ([entry]) => {
          if (
            entry.isIntersecting
          ) {
            setMounted(true);
          } else if (
            unloadWhenHidden
          ) {
            setMounted(false);
          }
        },
        {
          root: null,
          rootMargin,
          threshold: 0.01,
        }
      );

    observer.observe(
      element
    );

    return () => {
      observer.disconnect();
    };
  }, [
    rootMargin,
    unloadWhenHidden,
  ]);

  return (
    <div
      ref={ref}
      style={{
        minHeight:
          mounted
            ? undefined
            : minHeight,
      }}
    >
      {mounted
        ? children
        : (
          <PlotPlaceholder
            minHeight={
              minHeight
            }
          />
        )}
    </div>
  );
}

function PlotPlaceholder({
  minHeight,
}: {
  minHeight: number;
}) {
  return (
    <div
      style={{
        minHeight,
        display: "grid",
        placeItems: "center",
        borderRadius: 18,
        border:
          "1px solid rgba(148,163,184,0.10)",
        background:
          "rgba(4,9,20,0.28)",
      }}
    >
      <div
        style={{
          fontSize:
            "0.72rem",
          letterSpacing:
            "0.08em",
          textTransform:
            "uppercase",
          opacity: 0.38,
        }}
      >
        3D research
        visualization
      </div>
    </div>
  );
}