export type ExerciseBoundaryPoint = {
  time_to_maturity: number;
  spot: number | null;
};

export type AmericanSurfaceAtlasInput = {
  spot: number;
  strike: number;
  rate: number;
  volatility: number;
  maturity: number;
  dividend_yield: number;

  s_max?: number;
  space_steps?: number;
  time_steps?: number;

  crr_steps?: number;
  crr_surface_points?: number;

  boundary_tolerance?: number;
};

export type AmericanSurfaceAtlasResult = {
  option_type: "put";

  reference_method:
    "projected_crank_nicolson";

  input: {
    spot: number;
    strike: number;
    rate: number;
    volatility: number;
    maturity: number;
    dividend_yield: number;
    s_max: number;
  };

  grid: {
    spot: number[];
    time_to_maturity: number[];

    space_steps: number;
    time_steps: number;
    crr_steps: number;
  };

  surfaces: {
    crank_nicolson: number[][];
    crr: number[][];
    pinn_v2: number[][] | null;
    payoff: number[][];
    exercise_gap: number[][];
  };

  errors: {
    crr_signed: number[][];
    crr_absolute: number[][];
    pinn_signed: number[][] | null;
    pinn_absolute: number[][] | null;
  };

  pinn: {
    available: boolean;
    method: string | null;
    final_loss: number | null;
    training_seconds: number | null;
    mae_vs_cn: number | null;
    rmse_vs_cn: number | null;
    max_absolute_error_vs_cn:
      number | null;
  };

  pinn_convergence: {
    available: boolean;

    epochs: number[];

    surfaces: Record<
        string,
        number[][]
    >;

    signed_errors: Record<
        string,
        number[][]
    >;

    absolute_errors: Record<
        string,
        number[][]
    >;

    metrics: Record<
        string,
        {
        mae: number;
        rmse: number;
        max_absolute_error: number;
        training_loss: number;
        elapsed_training_seconds: number;
        inference_seconds: number;
        }
    >;

    improvement_surface:
        number[][] | null;

    boundary_diagnostics: Record<
        string,
        {
            band_width: number;

            near_boundary: {
            count: number;
            mae: number | null;
            rmse: number | null;
            max_absolute_error: number | null;
            };

            away_from_boundary: {
            count: number;
            mae: number | null;
            rmse: number | null;
            max_absolute_error: number | null;
            };

            near_to_away_mae_ratio:
            number | null;

            worst_near_boundary: {
            spot: number;
            time_to_maturity: number;
            boundary_spot: number;
            distance_to_boundary: number;
            absolute_error: number;
            } | null;

            worst_away_from_boundary: {
            spot: number;
            time_to_maturity: number;
            boundary_spot: number;
            distance_to_boundary: number;
            absolute_error: number;
            } | null;
        }
        >;

    boundary_distance_profiles: Record<
        string,
        {
            distance_definition: string;
            grid_spacing: number;
            strike: number;
            observation_count: number;
            distance_error_correlation: number | null;

            bins: Array<{
            label: string;
            lower_distance: number;
            upper_distance: number | null;
            count: number;
            mae: number | null;
            rmse: number | null;
            median_absolute_error: number | null;
            p90_absolute_error: number | null;
            max_absolute_error: number | null;
            }>;
        }
        >;
    };

  exercise_boundary:
    ExerciseBoundaryPoint[];

  summary: {
    min_price: number;
    max_price: number;
    max_exercise_gap: number;
    max_crr_absolute_error: number;
  };
};


const API_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  "http://127.0.0.1:8000";


export async function getAmericanSurfaceAtlas(
  input: AmericanSurfaceAtlasInput
): Promise<AmericanSurfaceAtlasResult> {
  const response = await fetch(
    `${API_URL}/research/american-surface-atlas`,
    {
      method: "POST",

      headers: {
        "Content-Type":
          "application/json",
      },

      body: JSON.stringify(input),
    }
  );

  if (!response.ok) {
    const text =
      await response.text();

    throw new Error(
      `American Surface Atlas API error: ${
        response.status
      } ${text}`
    );
  }

  return response.json();
}