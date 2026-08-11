"use client";

import {
  FormEvent,
  useMemo,
  useState,
} from "react";

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import {
  calibrateVolatilitySurface,
  CalibratedVolatilityQuote,
  VolatilityQuoteInput,
} from "@/lib/api/volatility";


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


export default function VolatilityLabPage() {
  const [spot, setSpot] =
    useState(100);

  const [rate, setRate] =
    useState(0.05);

  const [
    dividendYield,
    setDividendYield,
  ] = useState(0);

  const [
    quotes,
    setQuotes,
  ] = useState<
    VolatilityQuoteInput[]
  >(DEFAULT_QUOTES);

  const [
    calibrated,
    setCalibrated,
  ] = useState<
    CalibratedVolatilityQuote[]
  >([]);

  const [
    loading,
    setLoading,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState<string | null>(
    null
  );


  async function handleSubmit(
    event: FormEvent
  ) {
    event.preventDefault();

    if (loading) {
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


  function updateQuote(
    index: number,
    field:
      | "strike"
      | "maturity"
      | "market_price",
    value: string
  ) {
    setQuotes(
      (current) =>
        current.map(
          (quote, quoteIndex) =>
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
          (a, b) => a - b
        ),
      [calibrated]
    );


  const smileData =
    useMemo(() => {
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

        byStrike
          .get(
            quote.strike
          )![
            `T=${quote.maturity}`
          ] =
          quote
            .implied_volatility_percent;
      }

      return Array.from(
        byStrike.values()
      ).sort(
        (a, b) =>
          a.strike
          - b.strike
      );
    }, [calibrated]);


  const atmQuote =
    useMemo(() => {
      if (
        calibrated.length === 0
      ) {
        return null;
      }

      return calibrated.reduce(
        (best, quote) =>
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
    }, [
      calibrated,
      spot,
    ]);


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
            Recover market-implied volatility
            from option prices and inspect how
            volatility changes across strike
            and maturity.
          </p>
        </header>


        <form
          onSubmit={handleSubmit}
          className="mb-12 rounded-2xl border border-zinc-800 bg-zinc-900 p-6"
        >
          <div className="grid gap-4 md:grid-cols-3">

            <NumberInput
              label="Spot"
              value={spot}
              onChange={
                setSpot
              }
            />

            <NumberInput
              label="Risk-free rate"
              value={rate}
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


          <div className="mt-8">

            <div className="mb-4 flex items-center justify-between">
              <div>
                <p className="text-sm uppercase tracking-[0.2em] text-zinc-500">
                  Option Chain
                </p>

                <h2 className="mt-1 text-xl font-semibold">
                  Market quotes
                </h2>
              </div>

              <button
                type="button"
                onClick={() =>
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
                  )
                }
                className="rounded-lg border border-zinc-700 px-3 py-2 text-sm text-zinc-300 hover:border-emerald-400"
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
                        key={index}
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
                          step="0.25"
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
                              setQuotes(
                                (
                                  current
                                ) =>
                                  current.map(
                                    (
                                      item,
                                      quoteIndex
                                    ) =>
                                      quoteIndex ===
                                      index
                                        ? {
                                            ...item,
                                            option_type:
                                              event
                                                .target
                                                .value as
                                                | "call"
                                                | "put",
                                          }
                                        : item
                                  )
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
                              setQuotes(
                                (
                                  current
                                ) =>
                                  current.filter(
                                    (
                                      _,
                                      quoteIndex
                                    ) =>
                                      quoteIndex !==
                                      index
                                  )
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
          </div>


          <button
            disabled={loading}
            className="mt-6 rounded-xl bg-emerald-400 px-5 py-3 font-semibold text-zinc-950 transition hover:bg-emerald-300 disabled:opacity-50"
          >
            {loading
              ? "Calibrating..."
              : "Calibrate surface"}
          </button>

          {error && (
            <p className="mt-4 text-sm text-red-400">
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
                  label="ATM IV"
                  value={
                    atmQuote
                      ? `${atmQuote.implied_volatility_percent.toFixed(
                          2
                        )}%`
                      : "—"
                  }
                />

                <StatCard
                  label="Minimum IV"
                  value={
                    minIv !==
                    null
                      ? `${minIv.toFixed(
                          2
                        )}%`
                      : "—"
                  }
                />

                <StatCard
                  label="Maximum IV"
                  value={
                    maxIv !==
                    null
                      ? `${maxIv.toFixed(
                          2
                        )}%`
                      : "—"
                  }
                />

                <StatCard
                  label="Quotes"
                  value={
                    calibrated.length.toString()
                  }
                />

              </div>
            </section>


            <section className="mb-12">

              <div className="mb-6">
                <p className="text-sm uppercase tracking-[0.2em] text-zinc-500">
                  Smile Analysis
                </p>

                <h2 className="mt-2 text-3xl font-semibold">
                  Implied volatility by strike
                </h2>
              </div>

              <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-6">

                <div className="h-[420px]">

                  <ResponsiveContainer
                    width="100%"
                    height="100%"
                  >
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
                        tick={{
                          fill:
                            "#a1a1aa",
                        }}
                      />

                      <YAxis
                        tick={{
                          fill:
                            "#a1a1aa",
                        }}
                        label={{
                          value:
                            "IV (%)",
                          angle:
                            -90,
                          position:
                            "insideLeft",
                        }}
                      />

                      <Tooltip
                        contentStyle={{
                          background:
                            "#18181b",
                          border:
                            "1px solid #3f3f46",
                        }}
                      />

                      <Legend />

                      {maturities.map(
                        (
                          maturity,
                          index
                        ) => (
                          <Line
                            key={
                              maturity
                            }
                            type="monotone"
                            dataKey={`T=${maturity}`}
                            name={`T=${maturity}`}
                            stroke={
                              [
                                "#34d399",
                                "#60a5fa",
                                "#fbbf24",
                                "#f87171",
                                "#c084fc",
                              ][
                                index %
                                  5
                              ]
                            }
                            strokeWidth={
                              2
                            }
                            connectNulls
                          />
                        )
                      )}

                    </LineChart>
                  </ResponsiveContainer>

                </div>
              </div>

            </section>


            <section>
              <div className="mb-6">
                <p className="text-sm uppercase tracking-[0.2em] text-zinc-500">
                  Surface Data
                </p>

                <h2 className="mt-2 text-3xl font-semibold">
                  Calibrated quotes
                </h2>
              </div>

              <div className="overflow-x-auto rounded-2xl border border-zinc-800 bg-zinc-900">

                <table className="w-full min-w-[700px] text-sm">

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
                        IV
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
                          key={index}
                          className="border-t border-zinc-800"
                        >
                          <td className="px-5 py-4 font-mono">
                            {quote.strike.toFixed(
                              2
                            )}
                          </td>

                          <td className="px-5 py-4 font-mono">
                            {quote.maturity.toFixed(
                              2
                            )}
                          </td>

                          <td className="px-5 py-4 font-mono">
                            {quote.market_price.toFixed(
                              4
                            )}
                          </td>

                          <td className="px-5 py-4 font-mono text-emerald-400">
                            {quote.implied_volatility_percent.toFixed(
                              2
                            )}
                            %
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
        value={value}
        step={step}
        onChange={(event) =>
          onChange(
            Number(
              event.target
                .value
            )
          )
        }
        className="w-full rounded-xl border border-zinc-700 bg-zinc-950 px-4 py-3 outline-none focus:border-emerald-400"
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
        value={value}
        step={step}
        onChange={(event) =>
          onChange(
            event.target.value
          )
        }
        className="w-28 rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 font-mono outline-none focus:border-emerald-400"
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

      <p className="mt-4 font-mono text-2xl font-semibold">
        {value}
      </p>
    </article>
  );
}