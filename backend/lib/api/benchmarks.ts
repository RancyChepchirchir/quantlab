export type BenchmarkMethod = {
  price: number;
  absolute_error?: number;
  absolute_error_vs_crr?: number;
  runtime_seconds: number;

  steps?: number;

  space_steps?: number;
  time_steps?: number;

  early_exercise_premium?: number;
};

export type BenchmarkResults = {
  configuration: {
    spot: number;
    strike: number;
    rate: number;
    volatility: number;
    maturity: number;
    dividend_yield: number;
  };

  european_call: Record<
    string,
    BenchmarkMethod
  >;

  american_put: Record<
    string,
    BenchmarkMethod
  >;
};


const API_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  "http://127.0.0.1:8000";


export async function getBenchmarkResults():
  Promise<BenchmarkResults> {

  const response = await fetch(
    `${API_URL}/benchmarks/v1`,
    {
      cache: "no-store",
    }
  );

  if (!response.ok) {
    throw new Error(
      "Failed to load benchmark results."
    );
  }

  return response.json();
}