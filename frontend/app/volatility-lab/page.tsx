"use client";

import {
  FormEvent,
  Fragment,
  useMemo,
  useState,
} from "react";

import {
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Scatter,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import {
  calibrateVolatilitySurface,
  AtmTermStructurePoint,
  CalibratedVolatilityQuote,
  PutCallParityDiagnostic,
  RejectedVolatilityQuote,
  SkewDiagnostic,
  SSVISurface,
  SVISurface,
  VolatilityQuoteInput,
  VolatilitySurfaceGrid,
} from "@/lib/api/volatility";

import {
  describeMarketDataSnapshot,
  loadOptionChain,
  MarketDataApiError,
  MarketDataStatus,
  OptionChainSnapshot,
} from "@/lib/api/marketData";


const DEFAULT_QUOTES: VolatilityQuoteInput[] = [
  {
    strike: 80,
    maturity: 0.5,
    market_price: 22.20,
    option_type: "call",
  },
  {
    strike: 90,
    maturity: 0.5,
    market_price: 14.20,
    option_type: "call",
  },
  {
    strike: 100,
    maturity: 0.5,
    market_price: 8.00,
    option_type: "call",
  },
  {
    strike: 110,
    maturity: 0.5,
    market_price: 4.10,
    option_type: "call",
  },
  {
    strike: 120,
    maturity: 0.5,
    market_price: 1.95,
    option_type: "call",
  },
  {
    strike: 80,
    maturity: 1.0,
    market_price: 24.60,
    option_type: "call",
  },
  {
    strike: 90,
    maturity: 1.0,
    market_price: 17.10,
    option_type: "call",
  },
  {
    strike: 100,
    maturity: 1.0,
    market_price: 10.80,
    option_type: "call",
  },
  {
    strike: 110,
    maturity: 1.0,
    market_price: 6.30,
    option_type: "call",
  },
  {
    strike: 120,
    maturity: 1.0,
    market_price: 3.45,
    option_type: "call",
  },
];


function yearFraction(
  expiry: string
): number {
  const expiryDate =
    new Date(
      `${expiry}T00:00:00Z`
    );

  const now =
    new Date();

  const milliseconds =
    expiryDate.getTime()
    - now.getTime();

  const days =
    milliseconds
    / (
      1000
      * 60
      * 60
      * 24
    );

  return Math.max(
    days / 365.25,
    1 / 365.25
  );
}


export default function VolatilityLabPage() {
  const [
    spot,
    setSpot,
  ] = useState(100);

  const [
    rate,
    setRate,
  ] = useState(0.05);

  const [
    dividendYield,
    setDividendYield,
  ] = useState(0);

  const [
    quotes,
    setQuotes,
  ] = useState<
    VolatilityQuoteInput[]
  >(
    DEFAULT_QUOTES
  );

  const [
    calibrated,
    setCalibrated,
  ] = useState<
    CalibratedVolatilityQuote[]
  >([]);

  const [
    rejectedQuotes,
    setRejectedQuotes,
  ] = useState<
    RejectedVolatilityQuote[]
  >([]);

  const [
    calibrationStats,
    setCalibrationStats,
  ] = useState({
    inputCount: 0,
    calibratedCount: 0,
    rejectedCount: 0,
    successRate: 0,
  });

  const [
    skewDiagnostics,
    setSkewDiagnostics,
  ] = useState<
    SkewDiagnostic[]
  >([]);

  const [
    termStructure,
    setTermStructure,
  ] = useState<
    AtmTermStructurePoint[]
  >([]);

  const [
    parityDiagnostics,
    setParityDiagnostics,
  ] = useState<
    PutCallParityDiagnostic[]
  >([]);

  const [
    paritySummary,
    setParitySummary,
  ] = useState<{
    meanAbsoluteError:
      number | null;

    maxAbsoluteError:
      number | null;
  }>({
    meanAbsoluteError:
      null,

    maxAbsoluteError:
      null,
  });

  const [
    surfaceGrid,
    setSurfaceGrid,
  ] = useState<
    VolatilitySurfaceGrid | null
  >(null);

  const [
    sviSurface,
    setSviSurface,
  ] = useState<
    SVISurface | null
  >(null);

  const [
    ssviSurface,
    setSsviSurface,
  ] = useState<
    SSVISurface | null
  >(null);

  const [
    loading,
    setLoading,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState<
    string | null
  >(null);

  const [
    symbol,
    setSymbol,
  ] = useState("SPY");

  const [
    marketLoading,
    setMarketLoading,
  ] = useState(false);

  const [
    marketSource,
    setMarketSource,
  ] = useState<
    string | null
  >(null);

  const [
    marketSnapshot,
    setMarketSnapshot,
  ] = useState<
    OptionChainSnapshot | null
  >(null);

  const [
    marketStatus,
    setMarketStatus,
  ] = useState<
    MarketDataStatus | null
  >(null);

  const [
    marketError,
    setMarketError,
  ] = useState<
    MarketDataApiError | null
  >(null);


  function clearCalibrationResults() {
    setCalibrated([]);
    setRejectedQuotes([]);

    setSkewDiagnostics([]);
    setTermStructure([]);
    setParityDiagnostics([]);

    setParitySummary({
      meanAbsoluteError:
        null,

      maxAbsoluteError:
        null,
    });

    setSurfaceGrid(null);
    setSviSurface(null);
    setSsviSurface(null);

    setCalibrationStats({
      inputCount: 0,
      calibratedCount: 0,
      rejectedCount: 0,
      successRate: 0,
    });
  }


  function markQuotesAsManuallyEdited() {
    clearCalibrationResults();

    if (
      marketSource
      && !marketSource.includes(
        "manual edits"
      )
    ) {
      setMarketSource(
        `${marketSource} + manual edits`
      );
    }
  }


  async function handleSubmit(
    event: FormEvent
  ) {
    event.preventDefault();

    if (loading) {
      return;
    }

    if (
      quotes.length === 0
    ) {
      setError(
        "Add at least one option quote before calibration."
      );

      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result =
        await calibrateVolatilitySurface({
          spot,

          rate,

          dividend_yield:
            dividendYield,

          quotes,
        });

      setCalibrated(
        result.quotes
      );

      setRejectedQuotes(
        result.rejected_quotes
      );

      setCalibrationStats({
        inputCount:
          result.quote_count,

        calibratedCount:
          result.calibrated_count,

        rejectedCount:
          result.rejected_count,

        successRate:
          result.success_rate,
      });

      setSkewDiagnostics(
        result
          .diagnostics
          .skew
      );

      setTermStructure(
        result
          .diagnostics
          .atm_term_structure
      );

      setParityDiagnostics(
        result
          .diagnostics
          .put_call_parity
      );

      setParitySummary({
        meanAbsoluteError:
          result
            .diagnostics
            .mean_absolute_parity_error,

        maxAbsoluteError:
          result
            .diagnostics
            .max_absolute_parity_error,
      });

      setSurfaceGrid(
        result.surface_grid
      );

      setSviSurface(
        result.svi
      );

      setSsviSurface(
        result.ssvi
        );

    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Calibration failed."
      );

    } finally {
      setLoading(false);
    }
  }


  async function loadMarketChain(
    refresh = false
  ) {
    if (marketLoading) {
      return;
    }

    const normalizedSymbol =
      symbol
        .trim()
        .toUpperCase();

    if (!normalizedSymbol) {
      setError(
        "Enter an underlying symbol."
      );

      return;
    }

    setMarketLoading(true);
    setError(null);
    setMarketError(null);

    clearCalibrationResults();

    try {
      const snapshot =
        await loadOptionChain(
          normalizedSymbol,
          "massive",
          refresh
        );

      setSpot(
        snapshot.spot
      );

      const importedQuotes =
        snapshot.quotes
          .filter(
            (quote) =>
              quote.last !== null
              && quote.last > 0
          )
          .map(
            (quote) => ({
              strike:
                quote.strike,

              maturity:
                yearFraction(
                  quote.expiry
                ),

              market_price:
                quote.last as number,

              option_type:
                quote.option_type,
            })
          );

      if (
        importedQuotes.length
        === 0
      ) {
        throw new Error(
          "The provider returned contracts, but none had usable market prices."
        );
      }

      setQuotes(
        importedQuotes
      );

      setMarketSource(
        snapshot.source
      );

      setMarketSnapshot(
        snapshot
      );

      setMarketStatus(
        describeMarketDataSnapshot(
          snapshot
        )
      );

    } catch (err) {
      if (
        err instanceof
        MarketDataApiError
      ) {
        setMarketError(
          err
        );

        setError(
          err.message
        );

      } else {
        setError(
          err instanceof Error
            ? err.message
            : "Unable to load market chain."
        );
      }

    } finally {
      setMarketLoading(false);
    }
  }


  function updateQuote(
    index: number,
    field:
      | "strike"
      | "maturity"
      | "market_price",
    value: string
  ) {
    markQuotesAsManuallyEdited();

    setQuotes(
      (current) =>
        current.map(
          (
            quote,
            quoteIndex
          ) =>
            quoteIndex === index
              ? {
                  ...quote,

                  [field]:
                    Number(value),
                }
              : quote
        )
    );
  }


  function updateOptionType(
    index: number,
    optionType:
      | "call"
      | "put"
  ) {
    markQuotesAsManuallyEdited();

    setQuotes(
      (current) =>
        current.map(
          (
            quote,
            quoteIndex
          ) =>
            quoteIndex === index
              ? {
                  ...quote,

                  option_type:
                    optionType,
                }
              : quote
        )
    );
  }


  function removeQuote(
    index: number
  ) {
    markQuotesAsManuallyEdited();

    setQuotes(
      (current) =>
        current.filter(
          (
            _,
            quoteIndex
          ) =>
            quoteIndex
            !== index
        )
    );
  }


  function addQuote() {
    markQuotesAsManuallyEdited();

    setQuotes(
      (current) => [
        ...current,

        {
          strike:
            spot,

          maturity:
            1,

          market_price:
            5,

          option_type:
            "call",
        },
      ]
    );
  }


  function loadDemoQuotes() {
    clearCalibrationResults();

    setQuotes(
      DEFAULT_QUOTES
    );

    setSpot(100);
    setRate(0.05);
    setDividendYield(0);

    setMarketSource(
      "manual"
    );

    setMarketSnapshot(null);
    setMarketStatus(null);
    setMarketError(null);

    setError(null);
  }


  const retryBlocked =
    Boolean(
      marketError
      && marketError.cached
      && marketError.retryable
      && marketError
        .retryAfterSeconds
        != null
      && marketError
        .retryAfterSeconds
        > 0
    );


  const retryLabel =
    marketError
      ?.retryAfterSeconds
      != null
      ? `${Math.max(
          1,
          Math.ceil(
            marketError
              .retryAfterSeconds
          )
        )}s`
      : null;


  const maturities =
    useMemo(
      () =>
        Array.from(
          new Set(
            calibrated.map(
              (quote) =>
                quote.maturity
            )
          )
        ).sort(
          (
            first,
            second
          ) =>
            first - second
        ),
      [
        calibrated,
      ]
    );


  const smileData =
    useMemo(
      () => {
        const byStrike =
          new Map<
            number,
            Record<
              string,
              number
            >
          >();

        for (
          const quote
          of calibrated
        ) {
          if (
            !byStrike.has(
              quote.strike
            )
          ) {
            byStrike.set(
              quote.strike,
              {
                strike:
                  quote.strike,
              }
            );
          }

          const maturityKey =
            quote.maturity.toFixed(
              4
            );

          const row =
            byStrike.get(
              quote.strike
            )!;

          row[
            `BS T=${maturityKey}`
          ] =
            quote
              .implied_volatility_percent;

          if (
            quote
              .american_implied_volatility_percent
            != null
          ) {
            row[
              `AM T=${maturityKey}`
            ] =
              quote
                .american_implied_volatility_percent;
          }
        }

        return Array.from(
          byStrike.values()
        ).sort(
          (
            first,
            second
          ) =>
            first.strike
            - second.strike
        );
      },
      [
        calibrated,
      ]
    );


  const atmQuote =
    useMemo(
      () => {
        if (
          calibrated.length
          === 0
        ) {
          return null;
        }

        return calibrated.reduce(
          (
            best,
            quote
          ) =>
            Math.abs(
              quote.strike
              - spot
            )
            <
            Math.abs(
              best.strike
              - spot
            )
              ? quote
              : best
        );
      },
      [
        calibrated,
        spot,
      ]
    );


  const minIv =
    calibrated.length
      ? Math.min(
          ...calibrated.map(
            (quote) =>
              quote
                .implied_volatility_percent
          )
        )
      : null;


  const maxIv =
    calibrated.length
      ? Math.max(
          ...calibrated.map(
            (quote) =>
              quote
                .implied_volatility_percent
          )
        )
      : null;


  const termStructureData =
    useMemo(
      () =>
        termStructure.map(
          (item) => ({
            maturity:
              item.maturity,

            atmIv:
              item
                .atm_implied_volatility_percent,
          })
        ),
      [
        termStructure,
      ]
    );


  const skewData =
    useMemo(
      () =>
        skewDiagnostics.map(
          (item) => ({
            maturity:
              item.maturity,

            skew:
              item.skew_slope,
          })
        ),
      [
        skewDiagnostics,
      ]
    );


  const surfaceIvRange =
    useMemo(
      () => {
        if (
          !surfaceGrid
          || surfaceGrid
            .points
            .length === 0
        ) {
          return null;
        }

        const values =
          surfaceGrid
            .points
            .map(
              (point) =>
                point
                  .implied_volatility_percent
            );

        return {
          min:
            Math.min(
              ...values
            ),

          max:
            Math.max(
              ...values
            ),
        };
      },
      [
        surfaceGrid,
      ]
    );


  function surfaceIntensity(
    value: number
  ): number {
    if (!surfaceIvRange) {
      return 0.5;
    }

    const range =
      surfaceIvRange.max
      - surfaceIvRange.min;

    if (
      Math.abs(
        range
      )
      < 1e-12
    ) {
      return 0.5;
    }

    return (
      value
      - surfaceIvRange.min
    ) / range;
  }


  const sviWarnings =
    useMemo(
      () => {
        if (!sviSurface) {
          return [];
        }

        return sviSurface
          .smiles
          .filter(
            (smile) =>
              smile
                .arbitrage
                .butterfly_warning
              || smile
                .arbitrage
                .negative_variance_detected
              || smile
                .arbitrage
                .invalid_parameter_region
          );
      },
      [
        sviSurface,
      ]
    );


  const sviMeanRmse =
    useMemo(
      () => {
        if (
          !sviSurface
          || sviSurface
            .smiles
            .length === 0
        ) {
          return null;
        }

        return (
          sviSurface
            .smiles
            .reduce(
              (
                total,
                smile
              ) =>
                total
                + smile
                  .parameters
                  .rmse,
              0
            )
          / sviSurface
            .smiles
            .length
        );
      },
      [
        sviSurface,
      ]
    );

    const ssviMeanRmse =
    useMemo(
        () => {
        if (
            !ssviSurface
            || !ssviSurface.available
            || !ssviSurface.parameters
        ) {
            return null;
        }

        return (
            ssviSurface
            .parameters
            .rmse
        );
        },
        [
        ssviSurface,
        ]
    );


const ssviCalendarViolationCount =
  useMemo(
    () => {
      if (
        !ssviSurface
        || !ssviSurface.available
      ) {
        return 0;
      }

      return (
        ssviSurface
          .calendar_diagnostics
          .filter(
            (item) =>
              item
                .violation_detected
          )
          .length
      );
    },
    [
      ssviSurface,
    ]
  );


const ssviButterflyWarningCount =
  useMemo(
    () => {
      if (
        !ssviSurface
        || !ssviSurface.available
      ) {
        return 0;
      }

      return (
        ssviSurface
          .arbitrage_diagnostics
          .filter(
            (item) =>
              item
                .butterfly_warning
          )
          .length
      );
    },
    [
      ssviSurface,
    ]
  );


  const modelComparisonData =
    useMemo(
      () => {
        if (
          !sviSurface
          || !ssviSurface
          || !ssviSurface.available
        ) {
          return [];
        }

        function interpolate(
          points: Array<{
            strike: number;
            iv: number;
          }>,
          strike: number
        ): number | null {
          if (points.length === 0) {
            return null;
          }

          const ordered = [
            ...points,
          ].sort(
            (first, second) =>
              first.strike
              - second.strike
          );

          if (
            strike
            < ordered[0].strike
            || strike
            > ordered[
              ordered.length - 1
            ].strike
          ) {
            return null;
          }

          for (
            let index = 0;
            index < ordered.length;
            index += 1
          ) {
            if (
              Math.abs(
                ordered[index].strike
                - strike
              )
              < 1e-10
            ) {
              return ordered[index].iv;
            }

            if (
              index
              === ordered.length - 1
            ) {
              break;
            }

            const left =
              ordered[index];

            const right =
              ordered[index + 1];

            if (
              strike > left.strike
              && strike < right.strike
            ) {
              const weight =
                (
                  strike
                  - left.strike
                )
                / (
                  right.strike
                  - left.strike
                );

              return (
                left.iv
                + weight
                * (
                  right.iv
                  - left.iv
                )
              );
            }
          }

          return null;
        }

        return sviSurface
          .smiles
          .map(
            (smile) => {
              const maturity =
                smile
                  .parameters
                  .maturity;

              const rawSvi =
                smile.points.map(
                  (point) => ({
                    strike:
                      point.strike,

                    iv:
                      point
                        .fitted_iv_percent,
                  })
                );

              const ssvi =
                ssviSurface
                  .points
                  .filter(
                    (point) =>
                      Math.abs(
                        point.maturity
                        - maturity
                      )
                      < 1e-8
                  )
                  .map(
                    (point) => ({
                      strike:
                        point.strike,

                      iv:
                        100
                        * point.fitted_iv,
                    })
                  );

              if (
                rawSvi.length === 0
                || ssvi.length === 0
              ) {
                return null;
              }

              const observedByStrike =
                new Map<
                  number,
                  number[]
                >();

              calibrated
                .filter(
                  (quote) =>
                    Math.abs(
                      quote.maturity
                      - maturity
                    )
                    < 1e-8
                )
                .forEach(
                  (quote) => {
                    const values =
                      observedByStrike
                        .get(
                          quote.strike
                        )
                      ?? [];

                    values.push(
                      quote
                        .implied_volatility_percent
                    );

                    observedByStrike.set(
                      quote.strike,
                      values
                    );
                  }
                );

              const observed =
                Array.from(
                  observedByStrike.entries()
                ).map(
                  ([
                    strike,
                    values,
                  ]) => ({
                    strike,

                    iv:
                      values.reduce(
                        (total, value) =>
                          total + value,
                        0
                      )
                      / values.length,
                  })
                );

              const strikes =
                Array.from(
                  new Set(
                    [
                      ...rawSvi.map(
                        (point) =>
                          point.strike
                      ),

                      ...ssvi.map(
                        (point) =>
                          point.strike
                      ),

                      ...observed.map(
                        (point) =>
                          point.strike
                      ),
                    ]
                  )
                ).sort(
                  (first, second) =>
                    first - second
                );

              const observedMap =
                new Map(
                  observed.map(
                    (point) => [
                      point.strike,
                      point.iv,
                    ]
                  )
                );

              return {
                maturity,

                rows:
                  strikes.map(
                    (strike) => ({
                      strike,

                      observedIv:
                        observedMap.get(
                          strike
                        ),

                      rawSviIv:
                        interpolate(
                          rawSvi,
                          strike
                        ),

                      ssviIv:
                        interpolate(
                          ssvi,
                          strike
                        ),
                    })
                  ),
              };
            }
          )
          .filter(
            (item): item is {
              maturity: number;
              rows: Array<{
                strike: number;
                observedIv:
                  number | undefined;
                rawSviIv:
                  number | null;
                ssviIv:
                  number | null;
              }>;
            } =>
              item !== null
          );
      },
      [
        calibrated,
        sviSurface,
        ssviSurface,
      ]
    );


  return (
    <main className="min-h-screen bg-zinc-950 text-zinc-100">

      <div className="mx-auto max-w-7xl px-6 py-14 md:px-10">

        <header className="mb-12">

          <p className="text-sm uppercase tracking-[0.3em] text-emerald-400">
            QuantLab Volatility
          </p>

          <h1 className="mt-3 max-w-4xl text-4xl font-semibold tracking-tight md:text-6xl">
            Implied volatility
            smiles & surfaces.
          </h1>

          <p className="mt-5 max-w-3xl text-lg leading-8 text-zinc-400">
            Recover market-implied
            volatility, compare European
            and American models, inspect
            skew and term structure,
            fit raw SVI and SSVI surfaces, and monitor
            market-data freshness explicitly.
          </p>

        </header>


        <form
          onSubmit={
            handleSubmit
          }
          className="mb-12 rounded-2xl border border-zinc-800 bg-zinc-900 p-6"
        >

          <section>

            <p className="text-sm uppercase tracking-[0.2em] text-zinc-500">
              Market inputs
            </p>

            <div className="mt-4 grid gap-4 md:grid-cols-3">

              <NumberInput
                label="Spot"
                value={
                  spot
                }
                onChange={
                  setSpot
                }
              />

              <NumberInput
                label="Risk-free rate"
                value={
                  rate
                }
                step="0.01"
                onChange={
                  setRate
                }
              />

              <NumberInput
                label="Dividend yield"
                value={
                  dividendYield
                }
                step="0.01"
                onChange={
                  setDividendYield
                }
              />

            </div>

          </section>


          <section className="mt-8 rounded-xl border border-zinc-800 bg-zinc-950/40 p-5">

            <p className="text-sm uppercase tracking-[0.2em] text-zinc-500">
              Market data
            </p>

            <h2 className="mt-1 text-xl font-semibold">
              Load option chain
            </h2>

            <p className="mt-2 text-sm leading-6 text-zinc-500">
              Import end-of-day option
              contracts from Massive using
              QuantLab&apos;s backend cache
              and provider cooldown controls.
            </p>


            <div className="mt-5 grid gap-4 md:grid-cols-[1fr_auto_auto_auto]">

              <label>

                <span className="mb-2 block text-sm text-zinc-400">
                  Underlying symbol
                </span>

                <input
                  value={
                    symbol
                  }
                  onChange={(
                    event
                  ) =>
                    setSymbol(
                      event
                        .target
                        .value
                        .toUpperCase()
                    )
                  }
                  placeholder="SPY"
                  className="w-full rounded-xl border border-zinc-700 bg-zinc-950 px-4 py-3 outline-none focus:border-emerald-400"
                />

              </label>


              <button
                type="button"
                onClick={() =>
                  loadMarketChain(
                    false
                  )
                }
                disabled={
                  marketLoading
                  || retryBlocked
                }
                className="self-end rounded-xl border border-zinc-700 px-5 py-3 font-semibold transition hover:border-emerald-400 hover:text-emerald-300 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {marketLoading
                  ? "Loading..."
                  : retryBlocked
                    ? `Retry in ${retryLabel}`
                    : "Load market chain"}
              </button>


              <button
                type="button"
                onClick={() =>
                  loadMarketChain(
                    true
                  )
                }
                disabled={
                  marketLoading
                }
                title="Bypass QuantLab market-data caches and contact the provider directly."
                className="self-end rounded-xl border border-zinc-700 px-5 py-3 font-semibold transition hover:border-amber-400 hover:text-amber-300 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Refresh provider
              </button>


              <button
                type="button"
                onClick={
                  loadDemoQuotes
                }
                className="self-end rounded-xl border border-zinc-700 px-5 py-3 font-semibold transition hover:border-blue-400 hover:text-blue-300"
              >
                Demo
              </button>

            </div>


            {marketStatus
              && marketSnapshot
              && (
                <div className="mt-5 rounded-xl border border-zinc-800 bg-zinc-900/60 p-5">

                  <div className="flex flex-wrap items-center gap-3">

                    <StatusBadge
                      warning={
                        marketStatus.kind
                        === "cached"
                      }
                      warningText="Cached"
                      okText="Fresh"
                    />

                    <span className="text-sm text-zinc-400">
                      {marketStatus
                        .description}
                    </span>

                  </div>


                  <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">

                    <Metric
                      label="Source"
                      value={
                        marketSnapshot
                          .source
                      }
                    />

                    <Metric
                      label="Contracts"
                      value={
                        (
                          marketSnapshot
                            .returned_quote_count
                          ?? marketSnapshot
                            .quotes
                            .length
                        ).toString()
                      }
                    />

                    <Metric
                      label="Strikes / expiry"
                      value={
                        marketSnapshot
                          .requested_strikes_per_expiry
                        != null
                          ? marketSnapshot
                              .requested_strikes_per_expiry
                              .toString()
                          : "—"
                      }
                    />

                    <Metric
                      label="Cache TTL"
                      value={
                        marketSnapshot
                          .cache_ttl_seconds
                        != null
                          ? `${marketSnapshot
                              .cache_ttl_seconds}s`
                          : "—"
                      }
                    />

                  </div>


                  {marketSnapshot
                    .selected_expiries
                    ?.length
                    ? (
                      <div className="mt-5">

                        <p className="text-xs uppercase tracking-[0.15em] text-zinc-500">
                          Selected expiries
                        </p>

                        <div className="mt-2 flex flex-wrap gap-2">

                          {marketSnapshot
                            .selected_expiries
                            .map(
                              (
                                expiry
                              ) => (
                                <span
                                  key={
                                    expiry
                                  }
                                  className="rounded-full border border-zinc-700 px-3 py-1 font-mono text-xs text-zinc-300"
                                >
                                  {expiry}
                                </span>
                              )
                            )}

                        </div>

                      </div>
                    )
                    : null}

                </div>
              )}


            {marketError && (
              <div className="mt-5 rounded-xl border border-amber-900/50 bg-amber-950/20 p-5">

                <div className="flex flex-wrap items-center gap-3">

                  <StatusBadge
                    warning
                    warningText={
                      marketError.status
                      === 429
                        ? "Rate limited"
                        : marketError.status
                          === 403
                          ? "Provider access"
                          : "Provider error"
                    }
                    okText="OK"
                  />

                  {marketError.cached && (
                    <span className="rounded-full border border-zinc-700 px-3 py-1 text-xs text-zinc-400">
                      Cached provider state
                    </span>
                  )}

                  {marketError.retryable && (
                    <span className="rounded-full border border-zinc-700 px-3 py-1 text-xs text-zinc-400">
                      Retryable
                    </span>
                  )}

                </div>

                <p className="mt-4 text-sm leading-6 text-amber-200">
                  {marketError.message}
                </p>

                {marketError
                  .retryAfterSeconds
                  != null
                  && (
                    <p className="mt-2 text-xs text-zinc-500">
                      QuantLab cooldown remaining:{" "}

                      {Math.max(
                        1,
                        Math.ceil(
                          marketError
                            .retryAfterSeconds
                        )
                      )}

                      {" "}seconds.
                    </p>
                  )}

              </div>
            )}

          </section>


          <section className="mt-8">

            <div className="mb-4 flex items-center justify-between gap-4">

              <div>

                <p className="text-sm uppercase tracking-[0.2em] text-zinc-500">
                  Option chain
                </p>

                <h2 className="mt-1 text-xl font-semibold">
                  Market quotes
                </h2>

              </div>

              <button
                type="button"
                onClick={
                  addQuote
                }
                className="rounded-lg border border-zinc-700 px-3 py-2 text-sm text-zinc-300 transition hover:border-emerald-400 hover:text-emerald-300"
              >
                + Add quote
              </button>

            </div>


            <div className="overflow-x-auto rounded-xl border border-zinc-800">

              <table className="w-full min-w-[700px] text-sm">

                <thead className="bg-zinc-950 text-left text-zinc-500">

                  <tr>

                    <th className="px-4 py-3">
                      Strike
                    </th>

                    <th className="px-4 py-3">
                      Maturity
                    </th>

                    <th className="px-4 py-3">
                      Market price
                    </th>

                    <th className="px-4 py-3">
                      Type
                    </th>

                    <th className="px-4 py-3">
                      Remove
                    </th>

                  </tr>

                </thead>

                <tbody>

                  {quotes.map(
                    (
                      quote,
                      index
                    ) => (
                      <tr
                        key={
                          `${quote.strike}-${quote.maturity}-${quote.option_type}-${index}`
                        }
                        className="border-t border-zinc-800"
                      >

                        <EditableNumber
                          value={
                            quote.strike
                          }
                          onChange={(
                            value
                          ) =>
                            updateQuote(
                              index,
                              "strike",
                              value
                            )
                          }
                        />

                        <EditableNumber
                          value={
                            quote.maturity
                          }
                          step="0.01"
                          onChange={(
                            value
                          ) =>
                            updateQuote(
                              index,
                              "maturity",
                              value
                            )
                          }
                        />

                        <EditableNumber
                          value={
                            quote.market_price
                          }
                          step="0.01"
                          onChange={(
                            value
                          ) =>
                            updateQuote(
                              index,
                              "market_price",
                              value
                            )
                          }
                        />

                        <td className="px-4 py-3">

                          <select
                            value={
                              quote.option_type
                            }
                            onChange={(
                              event
                            ) =>
                              updateOptionType(
                                index,
                                event
                                  .target
                                  .value as
                                  | "call"
                                  | "put"
                              )
                            }
                            className="rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2"
                          >

                            <option value="call">
                              Call
                            </option>

                            <option value="put">
                              Put
                            </option>

                          </select>

                        </td>

                        <td className="px-4 py-3">

                          <button
                            type="button"
                            onClick={() =>
                              removeQuote(
                                index
                              )
                            }
                            className="text-zinc-500 hover:text-red-400"
                          >
                            Remove
                          </button>

                        </td>

                      </tr>
                    )
                  )}

                </tbody>

              </table>

            </div>

          </section>


          <button
            type="submit"
            disabled={
              loading
            }
            className="mt-6 rounded-xl bg-emerald-400 px-5 py-3 font-semibold text-zinc-950 disabled:opacity-50"
          >
            {loading
              ? "Calibrating..."
              : "Calibrate surface"}
          </button>


          {error && (
            <p className="mt-4 rounded-lg border border-red-900/60 bg-red-950/30 px-4 py-3 text-sm text-red-400">
              {error}
            </p>
          )}

        </form>


        {calibrated.length > 0 && (
          <>

            <section className="mb-12">

              <p className="text-sm uppercase tracking-[0.2em] text-zinc-500">
                Diagnostics
              </p>

              <h2 className="mt-2 text-2xl font-semibold">
                Calibrated surface summary
              </h2>

              <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">

                <StatCard
                  label="Input quotes"
                  value={
                    calibrationStats
                      .inputCount
                      .toString()
                  }
                />

                <StatCard
                  label="Calibrated"
                  value={
                    calibrationStats
                      .calibratedCount
                      .toString()
                  }
                />

                <StatCard
                  label="Rejected"
                  value={
                    calibrationStats
                      .rejectedCount
                      .toString()
                  }
                />

                <StatCard
                  label="Success rate"
                  value={
                    `${(
                      calibrationStats
                        .successRate
                      * 100
                    ).toFixed(1)}%`
                  }
                />

                <StatCard
                  label="ATM BS IV"
                  value={
                    atmQuote
                      ? `${atmQuote
                          .implied_volatility_percent
                          .toFixed(
                            2
                          )}%`
                      : "—"
                  }
                />

                <StatCard
                  label="Minimum BS IV"
                  value={
                    minIv != null
                      ? `${minIv.toFixed(
                          2
                        )}%`
                      : "—"
                  }
                />

                <StatCard
                  label="Maximum BS IV"
                  value={
                    maxIv != null
                      ? `${maxIv.toFixed(
                          2
                        )}%`
                      : "—"
                  }
                />

                <StatCard
                  label="Market source"
                  value={
                    marketSource
                    ?? "manual"
                  }
                />

              </div>

            </section>


            <section className="mb-12">

              <h2 className="mb-6 text-3xl font-semibold">
                European vs American volatility smiles
              </h2>

              <ChartPanel>

                <LineChart
                  data={
                    smileData
                  }
                >

                  <CartesianGrid
                    strokeDasharray="3 3"
                    opacity={
                      0.15
                    }
                  />

                  <XAxis
                    dataKey="strike"
                  />

                  <YAxis />

                  <Tooltip />

                  <Legend />

                  {maturities.map(
                    (
                      maturity,
                      index
                    ) => {
                      const key =
                        maturity.toFixed(
                          4
                        );

                      const palette = [
                        "#34d399",
                        "#60a5fa",
                        "#fbbf24",
                        "#f87171",
                        "#c084fc",
                      ];

                      const stroke =
                        palette[
                          index
                          % palette.length
                        ];

                      return (
                        <Fragment
                          key={
                            key
                          }
                        >

                          <Line
                            type="monotone"
                            dataKey={
                              `BS T=${key}`
                            }
                            name={
                              `BS T=${maturity.toFixed(
                                3
                              )}`
                            }
                            stroke={
                              stroke
                            }
                            strokeWidth={
                              2
                            }
                            dot
                            connectNulls
                          />

                          <Line
                            type="monotone"
                            dataKey={
                              `AM T=${key}`
                            }
                            name={
                              `American T=${maturity.toFixed(
                                3
                              )}`
                            }
                            stroke={
                              stroke
                            }
                            strokeWidth={
                              2
                            }
                            strokeDasharray="6 4"
                            dot
                            connectNulls
                          />

                        </Fragment>
                      );
                    }
                  )}

                </LineChart>

              </ChartPanel>

            </section>


            {termStructure.length > 0 && (
              <section className="mb-12">

                <h2 className="mb-6 text-3xl font-semibold">
                  ATM implied volatility by maturity
                </h2>

                <ChartPanel>

                  <LineChart
                    data={
                      termStructureData
                    }
                  >

                    <CartesianGrid
                      strokeDasharray="3 3"
                      opacity={
                        0.15
                      }
                    />

                    <XAxis
                      dataKey="maturity"
                    />

                    <YAxis />

                    <Tooltip />

                    <Line
                      type="monotone"
                      dataKey="atmIv"
                      stroke="#34d399"
                      strokeWidth={
                        2
                      }
                      dot
                    />

                  </LineChart>

                </ChartPanel>

              </section>
            )}


            {skewDiagnostics.length > 0 && (
              <section className="mb-12">

                <h2 className="mb-6 text-3xl font-semibold">
                  Volatility skew by maturity
                </h2>

                <ChartPanel>

                  <LineChart
                    data={
                      skewData
                    }
                  >

                    <CartesianGrid
                      strokeDasharray="3 3"
                      opacity={
                        0.15
                      }
                    />

                    <XAxis
                      dataKey="maturity"
                    />

                    <YAxis />

                    <Tooltip />

                    <Line
                      type="monotone"
                      dataKey="skew"
                      stroke="#60a5fa"
                      strokeWidth={
                        2
                      }
                      dot
                    />

                  </LineChart>

                </ChartPanel>

              </section>
            )}


            {sviSurface
              && sviSurface
                .fitted_maturity_count
                > 0
              && (
                <>

                  <section className="mb-12">

                    <p className="text-sm uppercase tracking-[0.2em] text-purple-400">
                      SVI calibration
                    </p>

                    <h2 className="mt-2 text-3xl font-semibold">
                      Parametric volatility smiles
                    </h2>

                    <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">

                      <StatCard
                        label="SVI maturities"
                        value={
                          sviSurface
                            .fitted_maturity_count
                            .toString()
                        }
                      />

                      <StatCard
                        label="Mean RMSE"
                        value={
                          sviMeanRmse
                          != null
                            ? sviMeanRmse
                                .toExponential(
                                  3
                                )
                            : "—"
                        }
                      />

                      <StatCard
                        label="Smile warnings"
                        value={
                          sviWarnings
                            .length
                            .toString()
                        }
                      />

                      <StatCard
                        label="Calendar status"
                        value={
                          sviSurface
                            .calendar_warning
                            ? "Warning"
                            : "Pass"
                        }
                      />

                    </div>

                  </section>


                  {sviSurface
                    .smiles
                    .map(
                      (
                        smile,
                        index
                      ) => {

                        const grouped =
                          new Map<
                            number,
                            number[]
                          >();

                        calibrated
                          .filter(
                            (quote) =>
                              Math.abs(
                                quote.maturity
                                - smile
                                  .parameters
                                  .maturity
                              )
                              < 1e-8
                          )
                          .forEach(
                            (quote) => {
                              const values =
                                grouped.get(
                                  quote.strike
                                )
                                ?? [];

                              values.push(
                                quote
                                  .implied_volatility_percent
                              );

                              grouped.set(
                                quote.strike,
                                values
                              );
                            }
                          );

                        const observed =
                          Array.from(
                            grouped.entries()
                          )
                            .map(
                              (
                                [
                                  strike,
                                  values,
                                ]
                              ) => ({
                                strike,

                                iv:
                                  values.reduce(
                                    (
                                      total,
                                      value
                                    ) =>
                                      total
                                      + value,
                                    0
                                  )
                                  / values.length,
                              })
                            );

                        const fitted =
                          smile.points.map(
                            (point) => ({
                              strike:
                                point.strike,

                              iv:
                                point
                                  .fitted_iv_percent,
                            })
                          );

                        return (
                          <section
                            key={
                              `${smile.parameters.maturity}-${index}`
                            }
                            className="mb-12"
                          >

                            <h3 className="mb-6 text-2xl font-semibold">
                              Observed vs SVI · T=
                              {smile
                                .parameters
                                .maturity
                                .toFixed(
                                  4
                                )}
                            </h3>

                            <ChartPanel>

                              <ComposedChart
                                data={
                                  fitted
                                }
                              >

                                <CartesianGrid
                                  strokeDasharray="3 3"
                                  opacity={
                                    0.15
                                  }
                                />

                                <XAxis
                                  type="number"
                                  dataKey="strike"
                                  domain={[
                                    "dataMin",
                                    "dataMax",
                                  ]}
                                />

                                <YAxis
                                  type="number"
                                  dataKey="iv"
                                />

                                <Tooltip />

                                <Legend />

                                <Line
                                  dataKey="iv"
                                  name="SVI fitted IV"
                                  stroke="#c084fc"
                                  strokeWidth={
                                    2
                                  }
                                  dot={
                                    false
                                  }
                                />

                                <Scatter
                                  data={
                                    observed
                                  }
                                  dataKey="iv"
                                  name="Observed IV"
                                  fill="#34d399"
                                />

                              </ComposedChart>

                            </ChartPanel>

                          </section>
                        );
                      }
                    )}

                </>
              )}

              {ssviSurface && (
  <section className="mb-12">

    <div className="mb-6">

      <p className="text-sm uppercase tracking-[0.2em] text-cyan-400">
        SSVI surface
      </p>

      <h2 className="mt-2 text-3xl font-semibold">
        Shared cross-maturity volatility model
      </h2>

      <p className="mt-2 max-w-3xl text-sm leading-6 text-zinc-500">
        SSVI fits one shared parameter
        triplet across usable maturities
        using forward log-moneyness and
        maturity-specific ATM total
        variance.
      </p>

    </div>


    {!ssviSurface.available ? (
      <div className="rounded-2xl border border-amber-900/40 bg-amber-950/10 p-6">

        <p className="text-sm uppercase tracking-[0.2em] text-amber-400">
          SSVI unavailable
        </p>

        <p className="mt-3 text-sm leading-6 text-zinc-400">
          {ssviSurface.message
            ?? (
              "The current calibration "
              + "does not contain enough "
              + "usable maturities."
            )}
        </p>

      </div>
    ) : (
      <>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">

          <StatCard
            label="η"
            value={
              ssviSurface.parameters
                ? ssviSurface
                    .parameters
                    .eta
                    .toFixed(
                      6
                    )
                : "—"
            }
          />

          <StatCard
            label="ρ"
            value={
              ssviSurface.parameters
                ? ssviSurface
                    .parameters
                    .rho
                    .toFixed(
                      6
                    )
                : "—"
            }
          />

          <StatCard
            label="γ"
            value={
              ssviSurface.parameters
                ? ssviSurface
                    .parameters
                    .gamma
                    .toFixed(
                      6
                    )
                : "—"
            }
          />

          <StatCard
            label="Variance RMSE"
            value={
              ssviMeanRmse
              != null
                ? ssviMeanRmse
                    .toExponential(
                      3
                    )
                : "—"
            }
          />

          <StatCard
            label="Observations"
            value={
              ssviSurface.parameters
                ? ssviSurface
                    .parameters
                    .observation_count
                    .toString()
                : "—"
            }
          />

          <StatCard
            label="Maturities"
            value={
              ssviSurface.parameters
                ? ssviSurface
                    .parameters
                    .maturity_count
                    .toString()
                : "—"
            }
          />

          <StatCard
            label="Butterfly warnings"
            value={
              ssviButterflyWarningCount
                .toString()
            }
          />

          <StatCard
            label="Calendar warnings"
            value={
              ssviCalendarViolationCount
                .toString()
            }
          />

        </div>


        <div className="mt-8 overflow-x-auto rounded-2xl border border-zinc-800 bg-zinc-900">

          <table className="w-full min-w-[900px] text-sm">

            <thead className="text-left text-zinc-500">

              <tr>

                <th className="px-5 py-4">
                  Maturity
                </th>

                <th className="px-5 py-4">
                  Forward
                </th>

                <th className="px-5 py-4">
                  ATM strike
                </th>

                <th className="px-5 py-4">
                  ATM IV
                </th>

                <th className="px-5 py-4">
                  θ
                </th>

              </tr>

            </thead>

            <tbody>

              {ssviSurface
                .atm_slices
                .map(
                  (
                    item,
                    index
                  ) => (
                    <tr
                      key={
                        `${item.maturity}-${index}`
                      }
                      className="border-t border-zinc-800"
                    >

                      <td className="px-5 py-4 font-mono">
                        {item
                          .maturity
                          .toFixed(
                            4
                          )}
                      </td>

                      <td className="px-5 py-4 font-mono">
                        {item
                          .forward
                          .toFixed(
                            4
                          )}
                      </td>

                      <td className="px-5 py-4 font-mono">
                        {item
                          .atm_strike
                          .toFixed(
                            4
                          )}
                      </td>

                      <td className="px-5 py-4 font-mono">
                        {(
                          100
                          * item
                            .atm_implied_volatility
                        ).toFixed(
                          2
                        )}
                        %
                      </td>

                      <td className="px-5 py-4 font-mono">
                        {item
                          .theta
                          .toExponential(
                            4
                          )}
                      </td>

                    </tr>
                  )
                )}

            </tbody>

          </table>

        </div>


        {ssviSurface
          .calendar_diagnostics
          .length > 0
          && (
            <div className="mt-8">

              <h3 className="text-2xl font-semibold">
                SSVI calendar diagnostics
              </h3>

              <div className="mt-5 overflow-x-auto rounded-2xl border border-zinc-800 bg-zinc-900">

                <table className="w-full min-w-[900px] text-sm">

                  <thead className="text-left text-zinc-500">

                    <tr>

                      <th className="px-5 py-4">
                        Short T
                      </th>

                      <th className="px-5 py-4">
                        Long T
                      </th>

                      <th className="px-5 py-4">
                        Min Δw
                      </th>

                      <th className="px-5 py-4">
                        Violations
                      </th>

                      <th className="px-5 py-4">
                        Grid points
                      </th>

                      <th className="px-5 py-4">
                        Status
                      </th>

                    </tr>

                  </thead>

                  <tbody>

                    {ssviSurface
                      .calendar_diagnostics
                      .map(
                        (
                          item,
                          index
                        ) => (
                          <tr
                            key={
                              `${item.shorter_maturity}-${item.longer_maturity}-${index}`
                            }
                            className="border-t border-zinc-800"
                          >

                            <td className="px-5 py-4 font-mono">
                              {item
                                .shorter_maturity
                                .toFixed(
                                  4
                                )}
                            </td>

                            <td className="px-5 py-4 font-mono">
                              {item
                                .longer_maturity
                                .toFixed(
                                  4
                                )}
                            </td>

                            <td className="px-5 py-4 font-mono">
                              {item
                                .minimum_variance_difference
                                .toExponential(
                                  4
                                )}
                            </td>

                            <td className="px-5 py-4 font-mono">
                              {item
                                .violation_count}
                            </td>

                            <td className="px-5 py-4 font-mono">
                              {item
                                .comparison_point_count}
                            </td>

                            <td className="px-5 py-4">

                              <StatusBadge
                                warning={
                                  item
                                    .violation_detected
                                }
                                warningText="Calendar warning"
                                okText="Pass"
                              />

                            </td>

                          </tr>
                        )
                      )}

                  </tbody>

                </table>

              </div>

            </div>
          )}


        {ssviSurface
            .arbitrage_diagnostics
            .length > 0
            && (
                <div className="mt-8">

                <h3 className="text-2xl font-semibold">
                    SSVI butterfly diagnostics
                </h3>

                <div className="mt-5 overflow-x-auto rounded-2xl border border-zinc-800 bg-zinc-900">

                    <table className="w-full min-w-[1050px] text-sm">

                    <thead className="text-left text-zinc-500">

                        <tr>

                        <th className="px-5 py-4">
                            Maturity
                        </th>

                        <th className="px-5 py-4">
                            θ
                        </th>

                        <th className="px-5 py-4">
                            φ
                        </th>

                        <th className="px-5 py-4">
                            Bound 1
                        </th>

                        <th className="px-5 py-4">
                            Bound 2
                        </th>

                        <th className="px-5 py-4">
                            Status
                        </th>

                        </tr>

                    </thead>

                    <tbody>

                        {ssviSurface
                        .arbitrage_diagnostics
                        .map(
                            (
                            item,
                            index
                            ) => (
                            <tr
                                key={
                                `${item.maturity}-${index}`
                                }
                                className="border-t border-zinc-800"
                            >

                                <td className="px-5 py-4 font-mono">
                                {item
                                    .maturity
                                    .toFixed(
                                    4
                                    )}
                                </td>

                                <td className="px-5 py-4 font-mono">
                                {item
                                    .theta
                                    .toExponential(
                                    4
                                    )}
                                </td>

                                <td className="px-5 py-4 font-mono">
                                {item
                                    .phi
                                    .toExponential(
                                    4
                                    )}
                                </td>

                                <td className="px-5 py-4 font-mono">
                                {item
                                    .first_butterfly_bound
                                    .toExponential(
                                    4
                                    )}
                                </td>

                                <td className="px-5 py-4 font-mono">
                                {item
                                    .second_butterfly_bound
                                    .toExponential(
                                    4
                                    )}
                                </td>

                                <td className="px-5 py-4">

                                <StatusBadge
                                    warning={
                                    item
                                        .butterfly_warning
                                    }
                                    warningText="Butterfly warning"
                                    okText="Pass"
                                />

                                </td>

                            </tr>
                            )
                        )}

                    </tbody>

                    </table>

                </div>

                </div>
            )}

        </>
        )}

    </section>
    )}


            {modelComparisonData.length > 0 && (
              <section className="mb-12">

                <p className="text-sm uppercase tracking-[0.2em] text-cyan-400">
                  Model comparison
                </p>

                <h2 className="mt-2 text-3xl font-semibold">
                  Observed IV vs raw SVI vs SSVI
                </h2>

                <p className="mt-2 max-w-3xl text-sm leading-6 text-zinc-500">
                  Observed Black–Scholes implied volatility is shown against
                  the maturity-specific raw-SVI fit and the shared
                  cross-maturity SSVI fit. This makes the trade-off between
                  local smile flexibility and global surface structure visible.
                </p>

                <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">

                  <StatCard
                    label="Raw SVI maturities"
                    value={
                      sviSurface
                        ?.fitted_maturity_count
                        .toString()
                      ?? "—"
                    }
                  />

                  <StatCard
                    label="Raw SVI mean RMSE"
                    value={
                      sviMeanRmse != null
                        ? sviMeanRmse
                            .toExponential(3)
                        : "—"
                    }
                  />

                  <StatCard
                    label="SSVI global RMSE"
                    value={
                      ssviMeanRmse != null
                        ? ssviMeanRmse
                            .toExponential(3)
                        : "—"
                    }
                  />

                  <StatCard
                    label="Compared maturities"
                    value={
                      modelComparisonData
                        .length
                        .toString()
                    }
                  />

                </div>

                <p className="mt-4 text-xs leading-5 text-zinc-500">
                  RMSE values describe each model&apos;s own total-variance
                  calibration objective. Use the charts and arbitrage
                  diagnostics alongside RMSE rather than treating the smallest
                  number as sufficient evidence of the better surface.
                </p>

                <div className="mt-8 space-y-10">

                  {modelComparisonData.map(
                    (comparison) => (
                      <div
                        key={
                          `model-comparison-${comparison.maturity}`
                        }
                      >

                        <h3 className="mb-5 text-2xl font-semibold">
                          T={comparison
                            .maturity
                            .toFixed(4)}
                        </h3>

                        <ChartPanel>

                          <ComposedChart
                            data={
                              comparison.rows
                            }
                          >

                            <CartesianGrid
                              strokeDasharray="3 3"
                              opacity={0.15}
                            />

                            <XAxis
                              type="number"
                              dataKey="strike"
                              domain={[
                                "dataMin",
                                "dataMax",
                              ]}
                            />

                            <YAxis
                              type="number"
                              domain={[
                                "auto",
                                "auto",
                              ]}
                              label={{
                                value: "IV (%)",
                                angle: -90,
                                position: "insideLeft",
                              }}
                            />

                            <Tooltip
                              formatter={(
                                value: number | string
                              ) => {
                                const numeric =
                                  Number(value);

                                return Number.isFinite(
                                  numeric
                                )
                                  ? `${numeric.toFixed(2)}%`
                                  : value;
                              }}
                            />

                            <Legend />

                            <Line
                              type="monotone"
                              dataKey="rawSviIv"
                              name="Raw SVI"
                              stroke="#c084fc"
                              strokeWidth={2}
                              dot={false}
                              connectNulls
                            />

                            <Line
                              type="monotone"
                              dataKey="ssviIv"
                              name="SSVI"
                              stroke="#22d3ee"
                              strokeWidth={2}
                              strokeDasharray="7 4"
                              dot={false}
                              connectNulls
                            />

                            <Scatter
                              dataKey="observedIv"
                              name="Observed BS IV"
                              fill="#34d399"
                            />

                          </ComposedChart>

                        </ChartPanel>

                      </div>
                    )
                  )}

                </div>

              </section>
            )}


            {surfaceGrid
              && surfaceIvRange
              && surfaceGrid
                .is_two_dimensional
              && (
                <section className="mb-12">

                  <h2 className="mb-6 text-3xl font-semibold">
                    IDW volatility heatmap
                  </h2>

                  <div className="overflow-x-auto rounded-2xl border border-zinc-800 bg-zinc-900 p-6">

                    <div
                      className="grid min-w-[900px] gap-[2px]"
                      style={{
                        gridTemplateColumns:
                          `repeat(${surfaceGrid.strikes.length}, minmax(24px, 1fr))`,
                      }}
                    >

                      {[...surfaceGrid
                        .maturities]
                        .reverse()
                        .flatMap(
                          (
                            maturity
                          ) =>
                            surfaceGrid
                              .points
                              .filter(
                                (point) =>
                                  Math.abs(
                                    point.maturity
                                    - maturity
                                  )
                                  < 1e-8
                              )
                              .sort(
                                (
                                  first,
                                  second
                                ) =>
                                  first.strike
                                  - second.strike
                              )
                              .map(
                                (point) => (
                                  <div
                                    key={
                                      `${point.maturity}-${point.strike}`
                                    }
                                    title={
                                      `K=${point.strike.toFixed(2)}, `
                                      + `T=${point.maturity.toFixed(4)}, `
                                      + `IV=${point.implied_volatility_percent.toFixed(2)}%`
                                    }
                                    className="aspect-square rounded-sm bg-emerald-400"
                                    style={{
                                      opacity:
                                        0.15
                                        + surfaceIntensity(
                                          point
                                            .implied_volatility_percent
                                        )
                                        * 0.85,
                                    }}
                                  />
                                )
                              )
                        )}

                    </div>

                  </div>

                </section>
              )}


            <section>

              <h2 className="mb-6 text-3xl font-semibold">
                Calibrated quotes
              </h2>

              <div className="overflow-x-auto rounded-2xl border border-zinc-800 bg-zinc-900">

                <table className="w-full min-w-[950px] text-sm">

                  <thead className="text-left text-zinc-500">

                    <tr>

                      <th className="px-5 py-4">
                        Strike
                      </th>

                      <th className="px-5 py-4">
                        Maturity
                      </th>

                      <th className="px-5 py-4">
                        Market price
                      </th>

                      <th className="px-5 py-4">
                        Type
                      </th>

                      <th className="px-5 py-4">
                        BS IV
                      </th>

                      <th className="px-5 py-4">
                        American IV
                      </th>

                    </tr>

                  </thead>

                  <tbody>

                    {calibrated.map(
                      (
                        quote,
                        index
                      ) => (
                        <tr
                          key={
                            `${quote.strike}-${quote.maturity}-${index}`
                          }
                          className="border-t border-zinc-800"
                        >

                          <td className="px-5 py-4 font-mono">
                            {quote.strike.toFixed(
                              2
                            )}
                          </td>

                          <td className="px-5 py-4 font-mono">
                            {quote.maturity.toFixed(
                              4
                            )}
                          </td>

                          <td className="px-5 py-4 font-mono">
                            {quote.market_price.toFixed(
                              4
                            )}
                          </td>

                          <td className="px-5 py-4 capitalize">
                            {quote.option_type}
                          </td>

                          <td className="px-5 py-4 font-mono text-emerald-400">
                            {quote
                              .implied_volatility_percent
                              .toFixed(
                                2
                              )}
                            %
                          </td>

                          <td className="px-5 py-4 font-mono text-blue-400">
                            {quote
                              .american_implied_volatility_percent
                            != null
                              ? `${quote
                                  .american_implied_volatility_percent
                                  .toFixed(
                                    2
                                  )}%`
                              : "—"}
                          </td>

                        </tr>
                      )
                    )}

                  </tbody>

                </table>

              </div>

            </section>

          </>
        )}

      </div>

    </main>
  );
}


function NumberInput({
  label,
  value,
  step = "1",
  onChange,
}: {
  label: string;
  value: number;
  step?: string;

  onChange: (
    value: number
  ) => void;
}) {
  return (
    <label>

      <span className="mb-2 block text-sm text-zinc-400">
        {label}
      </span>

      <input
        type="number"
        value={
          value
        }
        step={
          step
        }
        onChange={(
          event
        ) =>
          onChange(
            Number(
              event
                .target
                .value
            )
          )
        }
        className="w-full rounded-xl border border-zinc-700 bg-zinc-950 px-4 py-3"
      />

    </label>
  );
}


function EditableNumber({
  value,
  step = "1",
  onChange,
}: {
  value: number;
  step?: string;

  onChange: (
    value: string
  ) => void;
}) {
  return (
    <td className="px-4 py-3">

      <input
        type="number"
        value={
          value
        }
        step={
          step
        }
        onChange={(
          event
        ) =>
          onChange(
            event
              .target
              .value
          )
        }
        className="w-28 rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 font-mono"
      />

    </td>
  );
}


function StatCard({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <article className="rounded-2xl border border-zinc-800 bg-zinc-900 p-5">

      <p className="text-xs uppercase tracking-[0.18em] text-zinc-500">
        {label}
      </p>

      <p className="mt-4 break-words font-mono text-2xl font-semibold">
        {value}
      </p>

    </article>
  );
}


function Metric({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-950/50 p-4">

      <p className="text-xs uppercase tracking-[0.15em] text-zinc-500">
        {label}
      </p>

      <p className="mt-2 font-mono text-lg">
        {value}
      </p>

    </div>
  );
}


function StatusBadge({
  warning,
  warningText,
  okText,
}: {
  warning: boolean;
  warningText: string;
  okText: string;
}) {
  return (
    <span
      className={
        warning
          ? "inline-flex rounded-full border border-amber-800 bg-amber-950/30 px-3 py-1 text-xs text-amber-300"
          : "inline-flex rounded-full border border-emerald-800 bg-emerald-950/30 px-3 py-1 text-xs text-emerald-300"
      }
    >
      {warning
        ? warningText
        : okText}
    </span>
  );
}


function ChartPanel({
  children,
}: {
  children:
    React.ReactElement;
}) {
  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-6">

      <div className="h-[380px]">

        <ResponsiveContainer
          width="100%"
          height="100%"
        >
          {children}
        </ResponsiveContainer>

      </div>

    </div>
  );
}