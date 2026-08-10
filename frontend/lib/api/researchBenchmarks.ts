export type ClassicalBenchmark = {
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
    {
      price: number;
      absolute_error?: number;
      runtime_seconds: number;
      steps?: number;
      space_steps?: number;
      time_steps?: number;
    }
  >;

  american_put: Record<
    string,
    {
      price: number;
      absolute_error_vs_crr?: number;
      runtime_seconds: number;
      early_exercise_premium?: number;
    }
  >;
};


export type PINNBenchmark = {
  experiment: string;

  problem: {
    instrument: string;
    benchmark: string;
    spot: number;
    strike: number;
    rate: number;
    volatility: number;
    maturity: number;
    dividend_yield: number;
    evaluation_spot_min: number;
    evaluation_spot_max: number;
    evaluation_points: number;
  };

  methods: Record<
    string,
    {
      role: string;
      formulation?: string;

      mae: number;
      rmse: number;
      max_error: number;
      atm_error: number;

      runtime_seconds?: number;
      training_seconds?: number;
      inference_seconds?: number;

      final_loss?: number;
      atm_price: number;
    }
  >;
};


export type DeepONetBenchmark = {
  experiment: string;

  problem: {
    instrument: string;
    target_solver: string;
    train_parameter_sets: number;
    test_parameter_sets: number;
    spot_points_per_set: number;
  };

  model: {
    architecture: string;
    branch_variables: string[];
    trunk_variables: string[];
  };

  metrics: {
    mae: number;
    rmse: number;
    median_error: number;
    p95_error: number;
    max_error: number;
    training_seconds: number;
    final_loss: number;
  };
};


export type AmortisationBenchmark = {
  experiment: string;
  queries: number;

  offline: {
    data_generation_seconds: number;
    training_seconds: number;
    total_seconds: number;
  };

  online: {
    projected_cn: {
      total_seconds: number;
      seconds_per_query: number;
      queries_per_second: number;
    };

    deeponet: {
      total_seconds: number;
      seconds_per_query: number;
      queries_per_second: number;
    };

    speedup: number;
    break_even_queries: number | null;
  };

  accuracy: {
    mae: number;
    rmse: number;
    median_absolute_error: number;
    p95_absolute_error: number;
    max_error: number;
    median_relative_error: number;
  };
};


export type ResearchBenchmarks = {
  classical: ClassicalBenchmark | null;
  pinn: PINNBenchmark | null;
  deeponet: DeepONetBenchmark | null;
  amortisation:
    | AmortisationBenchmark
    | null;
};


const API_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  "http://127.0.0.1:8000";


export async function getResearchBenchmarks():
  Promise<ResearchBenchmarks> {

  const response = await fetch(
    `${API_URL}/benchmarks/research`,
    {
      cache: "no-store",
    }
  );

  if (!response.ok) {
    throw new Error(
      "Unable to load QuantLab research results."
    );
  }

  return response.json();
}