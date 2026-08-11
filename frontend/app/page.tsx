"use client";

import {
  FormEvent,
  useState,
} from "react";

import {
  compareModels,
  getGreeks,
  getSpotSweep,
  getConvergence,
  ComparisonResult,
  GreeksResult,
  PricingInput,
  SpotSweepResult,
  ConvergenceResult,
} from "@/lib/quantlab";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import Link from "next/link";


const DEFAULT_INPUT: PricingInput = {
  spot: 100,
  strike: 100,
  rate: 0.05,
  volatility: 0.20,
  maturity: 1,
  dividend_yield: 0,
  option_type: "call",
};

function ConvergenceChart({
  title,
  data,
  xKey,
  series,
}: {
  title: string;
  data: Array<Record<string, number>>;
  xKey: string;
  series: Array<{
    key: string;
    label: string;
  }>;
}) {
  const colors = [
    "#34d399",
    "#60a5fa",
    "#fbbf24",
    "#f87171",
  ];

  return (
    <article className="rounded-2xl border border-zinc-800 bg-zinc-900 p-6">
      <h3 className="mb-6 text-lg font-semibold">
        {title}
      </h3>

      <div className="h-72">
        <ResponsiveContainer
          width="100%"
          height="100%"
        >
          <LineChart data={data}>
            <CartesianGrid
              strokeDasharray="3 3"
              opacity={0.15}
            />

            <XAxis
              dataKey={xKey}
              tick={{
                fill: "#a1a1aa",
                fontSize: 12,
              }}
            />

            <YAxis
              tick={{
                fill: "#a1a1aa",
                fontSize: 12,
              }}
            />

            <Tooltip
              contentStyle={{
                background: "#18181b",
                border:
                  "1px solid #3f3f46",
              }}
            />

            {series.map((item, index) => (
              <Line
                key={item.key}
                type="monotone"
                dataKey={item.key}
                name={item.label}
                stroke={colors[index % colors.length]}
                dot={false}
                strokeWidth={2}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </article>
  );
}

export default function Home() {
  const [
    input,
    setInput,
  ] = useState<PricingInput>(
    DEFAULT_INPUT
  );

  const [
    result,
    setResult,
  ] = useState<
    ComparisonResult | null
  >(null);

  const [greeks, setGreeks] =
  useState<GreeksResult | null>(null);

  const [
    sweep,
    setSweep,
  ] = useState<
    SpotSweepResult | null
  >(null);

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

  const sweepData =
  sweep?.spot.map(
    (spot, index) => ({
      spot,
      price: sweep.price[index],
      delta: sweep.delta[index],
      gamma: sweep.gamma[index],
    })
  ) ?? [];

  const [
    convergence,
    setConvergence,
  ] = useState<
    ConvergenceResult | null
  >(null);


  function updateNumber(
    field: keyof PricingInput,
    value: string
  ) {
    setInput((current) => ({
      ...current,
      [field]: Number(value),
    }));
  }


  async function handleSubmit(
  event: FormEvent
) {
  event.preventDefault();

  // Prevent overlapping submissions.
  if (loading) {
    return;
  }

  setLoading(true);
  setError(null);

  // Clear secondary analysis from the previous run.
  setGreeks(null);
  setSweep(null);
  setConvergence(null);

  try {
    // -------------------------------------------------
    // 1. Core pricing comparison
    // -------------------------------------------------
    // This controls the main "Pricing..." state.
    const comparisonData =
      await compareModels(input);

    setResult(comparisonData);

    // The main pricing calculation is finished.
    setLoading(false);

    // -------------------------------------------------
    // 2. Secondary analyses
    // -------------------------------------------------
    // These now load independently.
    void getGreeks(input)
      .then((data) => {
        setGreeks(data);
      })
      .catch((err) => {
        console.error(
          "Greeks request failed:",
          err
        );
      });

    void getSpotSweep(input)
      .then((data) => {
        setSweep(data);
      })
      .catch((err) => {
        console.error(
          "Spot sweep request failed:",
          err
        );
      });

    void getConvergence(input)
      .then((data) => {
        setConvergence(data);
      })
      .catch((err) => {
        console.error(
          "Convergence request failed:",
          err
        );
      });
  } catch (err) {
    console.error(
      "Comparison request failed:",
      err
    );

    setError(
      err instanceof Error
        ? err.message
        : "Pricing failed."
    );

    setLoading(false);
  }
}

  const crrConvergenceData =
  convergence?.crr.map(
    (item) => ({
      effort: item.steps,
      error:
        item.absolute_error,
      runtime:
        item.runtime_seconds,
    })
  ) ?? [];

const mcConvergenceData =
  convergence?.monte_carlo.map(
    (item) => ({
      effort:
        item.simulations,
      error:
        item.absolute_error,
      standardError:
        item.standard_error,
      theoretical:
        item.theoretical_error,
      runtime:
        item.runtime_seconds,
    })
  ) ?? [];


  return (
    <main className="min-h-screen bg-zinc-950 text-zinc-100">
      <div className="mx-auto max-w-7xl px-6 py-12">

        <header className="mb-12">
          <p className="mb-3 text-sm uppercase tracking-[0.3em] text-emerald-400">
            QuantLab
          </p>

          <h1 className="max-w-4xl text-4xl font-semibold tracking-tight md:text-6xl">
            Option pricing,
            numerical methods &
            computational finance.
          </h1>

          <p className="mt-5 max-w-2xl text-lg leading-8 text-zinc-400">
            Compare analytical,
            lattice and stochastic
            pricing methods under
            identical market
            assumptions.
          </p>
        </header>


        <div className="grid gap-8 lg:grid-cols-[360px_1fr]">

          <form
            onSubmit={handleSubmit}
            className="rounded-2xl border border-zinc-800 bg-zinc-900 p-6"
          >
            <h2 className="mb-6 text-xl font-semibold">
              Contract
            </h2>

            <Input
              label="Spot price"
              value={input.spot}
              onChange={(value) =>
                updateNumber(
                  "spot",
                  value
                )
              }
            />

            <Input
              label="Strike"
              value={input.strike}
              onChange={(value) =>
                updateNumber(
                  "strike",
                  value
                )
              }
            />

            <Input
              label="Risk-free rate"
              value={input.rate}
              step="0.01"
              onChange={(value) =>
                updateNumber(
                  "rate",
                  value
                )
              }
            />

            <Input
              label="Volatility"
              value={
                input.volatility
              }
              step="0.01"
              onChange={(value) =>
                updateNumber(
                  "volatility",
                  value
                )
              }
            />

            <Input
              label="Maturity (years)"
              value={input.maturity}
              step="0.1"
              onChange={(value) =>
                updateNumber(
                  "maturity",
                  value
                )
              }
            />

            <label className="mb-6 block">
              <span className="mb-2 block text-sm text-zinc-400">
                Option type
              </span>

              <select
                value={
                  input.option_type
                }
                onChange={(event) =>
                  setInput(
                    (current) => ({
                      ...current,
                      option_type:
                        event.target
                          .value as
                          | "call"
                          | "put",
                    })
                  )
                }
                className="w-full rounded-xl border border-zinc-700 bg-zinc-950 px-4 py-3 outline-none"
              >
                <option value="call">
                  Call
                </option>

                <option value="put">
                  Put
                </option>
              </select>
            </label>

            <button
              disabled={loading}
              className="w-full rounded-xl bg-emerald-400 px-4 py-3 font-semibold text-zinc-950 transition hover:bg-emerald-300 disabled:opacity-50"
            >
              {loading
                ? "Pricing..."
                : "Run models"}
            </button>

            {error && (
              <p className="mt-4 text-sm text-red-400">
                {error}
              </p>
            )}
          </form>


          <section>
            {!result ? (
              <div className="flex min-h-[420px] items-center justify-center rounded-2xl border border-dashed border-zinc-800">
                <p className="text-zinc-500">
                  Run the models to
                  compare pricing
                  methods.
                </p>
              </div>
            ) : (
              <div className="space-y-6">
                <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">

                  <ResultCard
                    title="Black–Scholes"
                    price={
                      result
                        .black_scholes
                        .price
                    }
                    subtitle="Analytical benchmark"
                  />

                  <ResultCard
                    title="CRR Binomial"
                    price={
                      result
                        .binomial
                        .price
                    }
                    subtitle={`Error ${result.binomial.absolute_error.toFixed(
                      6
                    )}`}
                  />

                  <ResultCard
                    title="Crank–Nicolson"
                    price={
                      result
                        .finite_difference
                        .price
                    }
                    subtitle={`Error ${result.finite_difference.absolute_error.toFixed(
                      6
                    )}`}
                  />

                  <ResultCard
                    title="Monte Carlo"
                    price={
                      result
                        .monte_carlo
                        .price
                    }
                    subtitle={`SE ${result.monte_carlo.standard_error.toFixed(
                      6
                    )}`}
                  />

                </div>

                <div className="mt-6 overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-900">

                <div className="border-b border-zinc-800 p-6">
                  <p className="text-sm uppercase tracking-[0.2em] text-zinc-500">
                    Computational comparison
                  </p>

                  <h2 className="mt-2 text-2xl font-semibold">
                    Accuracy vs runtime
                  </h2>
                </div>

                <div className="divide-y divide-zinc-800">

                  <MethodRow
                    method="Black–Scholes"
                    error={0}
                    runtime={
                      result
                        .black_scholes
                        .runtime_seconds
                    }
                  />

                  <MethodRow
                    method="CRR Binomial"
                    error={
                      result
                        .binomial
                        .absolute_error
                    }
                    runtime={
                      result
                        .binomial
                        .runtime_seconds
                    }
                  />

                  <MethodRow
                    method="Crank–Nicolson"
                    error={
                      result
                        .finite_difference
                        .absolute_error
                    }
                    runtime={
                      result
                        .finite_difference
                        .runtime_seconds
                    }
                  />

                  <MethodRow
                    method="Monte Carlo"
                    error={
                      result
                        .monte_carlo
                        .absolute_error
                    }
                    runtime={
                      result
                        .monte_carlo
                        .runtime_seconds
                    }
                  />

                </div>
              </div>


                <div className="mt-6 rounded-2xl border border-zinc-800 bg-zinc-900 p-6">

                  <p className="text-sm uppercase tracking-[0.2em] text-zinc-500">
                    Monte Carlo uncertainty
                  </p>

                  <h2 className="mt-2 text-2xl font-semibold">
                    95% confidence interval
                  </h2>

                  <p className="mt-4 text-3xl font-mono text-emerald-400">
                    [
                    {result
                      .monte_carlo
                      .confidence_interval[0]
                      .toFixed(4)}
                    ,{" "}
                    {result
                      .monte_carlo
                      .confidence_interval[1]
                      .toFixed(4)}
                    ]
                  </p>

                </div>

                {greeks && (
                  <div className="mt-6">
                    <div className="mb-4">
                      <p className="text-sm uppercase tracking-[0.2em] text-zinc-500">
                        Risk sensitivities
                      </p>

                      <h2 className="mt-2 text-2xl font-semibold">
                        Black–Scholes Greeks
                      </h2>
                    </div>

                    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
                      <GreekCard
                        symbol="Δ"
                        name="Delta"
                        value={greeks.delta}
                      />

                      <GreekCard
                        symbol="Γ"
                        name="Gamma"
                        value={greeks.gamma}
                      />

                      <GreekCard
                        symbol="ν"
                        name="Vega"
                        value={greeks.vega}
                      />

                      <GreekCard
                        symbol="Θ"
                        name="Theta"
                        value={greeks.theta}
                      />

                      <GreekCard
                        symbol="ρ"
                        name="Rho"
                        value={greeks.rho}
                      />
                    </div>
                  </div>
                )}

                {sweep && (
                  <div className="mt-8 space-y-6">
                    <div>
                      <p className="text-sm uppercase tracking-[0.2em] text-zinc-500">
                        Spot sensitivity
                      </p>

                      <h2 className="mt-2 text-2xl font-semibold">
                        Pricing surface slice
                      </h2>
                    </div>

                    <ChartCard
                      title="Option value vs spot"
                      data={sweepData}
                      dataKey="price"
                    />

                    <div className="grid gap-6 lg:grid-cols-2">
                      <ChartCard
                        title="Delta vs spot"
                        data={sweepData}
                        dataKey="delta"
                      />

                      <ChartCard
                        title="Gamma vs spot"
                        data={sweepData}
                        dataKey="gamma"
                      />
                    </div>
                  </div>
                )}

                {convergence && (
              <section className="mt-12">
                <div className="mb-6">
                  <p className="text-sm uppercase tracking-[0.2em] text-zinc-500">
                    Numerical analysis
                  </p>

                  <h2 className="mt-2 text-3xl font-semibold">
                    Convergence Lab
                  </h2>

                  <p className="mt-3 max-w-2xl text-zinc-400">
                    Compare how deterministic lattice
                    refinement and stochastic sampling
                    approach the Black–Scholes benchmark.
                  </p>
                </div>

                <div className="grid gap-6 lg:grid-cols-2">
                  <ConvergenceChart
                    title="CRR lattice convergence"
                    data={crrConvergenceData}
                    xKey="effort"
                    series={[
                      {
                        key: "error",
                        label:
                          "Absolute error",
                      },
                    ]}
                  />
                  <ConvergenceChart
                    title="Monte Carlo convergence"
                    data={mcConvergenceData}
                    xKey="effort"
                    series={[
                      {
                        key: "error",
                        label:
                          "Absolute error",
                      },
                      {
                        key:
                          "standardError",
                        label:
                          "Standard error",
                      },
                      {
                        key:
                          "theoretical",
                        label:
                          "O(M^-1/2)",
                      },
                    ]}
            />
          </div>
        </section>
      )}
              </div>
            )}
          </section>

        </div>
      </div>
    </main>
  );
}


function Input({
  label,
  value,
  step = "1",
  onChange,
}: {
  label: string;
  value: number;
  step?: string;
  onChange: (
    value: string
  ) => void;
}) {
  return (
    <label className="mb-5 block">

      <span className="mb-2 block text-sm text-zinc-400">
        {label}
      </span>

      <input
        type="number"
        step={step}
        value={value}
        onChange={(event) =>
          onChange(
            event.target.value
          )
        }
        className="w-full rounded-xl border border-zinc-700 bg-zinc-950 px-4 py-3 outline-none transition focus:border-emerald-400"
      />

    </label>
  );
}


function ResultCard({
  title,
  price,
  subtitle,
}: {
  title: string;
  price: number;
  subtitle: string;
}) {
  return (
    <article className="rounded-2xl border border-zinc-800 bg-zinc-900 p-6">

      <p className="text-sm text-zinc-500">
        {title}
      </p>

      <p className="mt-3 font-mono text-3xl font-semibold">
        {price.toFixed(4)}
      </p>

      <p className="mt-3 text-sm text-zinc-400">
        {subtitle}
      </p>

    </article>
  );
}

function GreekCard({
  symbol,
  name,
  value,
}: {
  symbol: string;
  name: string;
  value: number;
}) {
  return (
    <article className="rounded-2xl border border-zinc-800 bg-zinc-900 p-5">

      <div className="flex items-center justify-between">
        <span className="text-2xl text-emerald-400">
          {symbol}
        </span>

        <span className="text-xs uppercase tracking-[0.15em] text-zinc-500">
          {name}
        </span>
      </div>

      <p className="mt-5 font-mono text-2xl font-semibold">
        {value.toFixed(5)}
      </p>
    </article>
  );
}

function ChartCard({
  title,
  data,
  dataKey,
}: {
  title: string;
  data: {
    spot: number;
    price: number;
    delta: number;
    gamma: number;
  }[];
  dataKey:
    | "price"
    | "delta"
    | "gamma";
}) {
  return (
    <article className="rounded-2xl border border-zinc-800 bg-zinc-900 p-6">

      <h3 className="mb-6 text-lg font-semibold">
        {title}
      </h3>

      <div className="h-72">
        <ResponsiveContainer
          width="100%"
          height="100%"
        >
          <LineChart data={data}>
            <CartesianGrid
              strokeDasharray="3 3"
              opacity={0.15}
            />

            <XAxis
              dataKey="spot"
              tick={{
                fill: "#a1a1aa",
                fontSize: 12,
              }}
            />

            <YAxis
              tick={{
                fill: "#a1a1aa",
                fontSize: 12,
              }}
            />

            <Tooltip
              contentStyle={{
                background: "#18181b",
                border:
                  "1px solid #3f3f46",
              }}
            />

            <Line
              type="monotone"
              dataKey={dataKey}
              stroke="#34d399"
              dot={false}
              strokeWidth={2}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </article>
  );
}

function MethodRow({
  method,
  error,
  runtime,
}: {
  method: string;
  error: number;
  runtime: number;
}) {
  return (
    <div className="grid grid-cols-3 gap-4 px-6 py-4">

      <span className="text-zinc-300">
        {method}
      </span>

      <span className="font-mono text-zinc-400">
        {error.toExponential(3)}
      </span>

      <span className="text-right font-mono text-zinc-400">
        {runtime.toFixed(6)} s
      </span>

    </div>
  );
}