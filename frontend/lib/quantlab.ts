export type OptionType =
  | "call"
  | "put";

export type PricingInput = {
  spot: number;
  strike: number;
  rate: number;
  volatility: number;
  maturity: number;
  dividend_yield: number;
  option_type: OptionType;
};

export type ComparisonResult = {
  input: PricingInput;

  black_scholes: {
    price: number;
    runtime_seconds: number;
  };

  binomial: {
    price: number;
    steps: number;
    absolute_error: number;
    runtime_seconds: number;
  };

  finite_difference: {
    price: number;
    space_steps: number;
    time_steps: number;
    absolute_error: number;
    runtime_seconds: number;
  };

  monte_carlo: {
    price: number;
    simulations: number;
    standard_error: number;
    confidence_interval: [
      number,
      number
    ];
    absolute_error: number;
    runtime_seconds: number;
  };
};


const API_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  "http://127.0.0.1:8000";


export async function compareModels(
  input: PricingInput
): Promise<ComparisonResult> {
  const response = await fetch(
    `${API_URL}/compare`,
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
    throw new Error(
      `QuantLab API error: ${
        response.status
      }`
    );
  }

  return response.json();
}

export type GreeksResult = {
  method: string;
  option_type: OptionType;
  delta: number;
  gamma: number;
  vega: number;
  theta: number;
  rho: number;
};

export async function getGreeks(
  input: PricingInput
): Promise<GreeksResult> {
  const response = await fetch(
    `${API_URL}/price/greeks`,
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
    throw new Error(
      `QuantLab API error: ${response.status}`
    );
  }

  return response.json();
}

export type SpotSweepResult = {
  spot: number[];
  price: number[];
  delta: number[];
  gamma: number[];
};

export async function getSpotSweep(
  input: PricingInput
): Promise<SpotSweepResult> {
  const response = await fetch(
    `${API_URL}/sweep/spot`,
    {
      method: "POST",
      headers: {
        "Content-Type":
          "application/json",
      },
      body: JSON.stringify({
        ...input,
        spot_min:
          Math.max(1, input.spot * 0.5),
        spot_max:
          input.spot * 1.5,
        points: 61,
      }),
    }
  );

  if (!response.ok) {
    throw new Error(
      `QuantLab API error: ${response.status}`
    );
  }

  return response.json();
}

export type ConvergenceResult = {
  benchmark: {
    method: string;
    price: number;
  };

  crr: {
    steps: number;
    price: number;
    absolute_error: number;
    runtime_seconds: number;
  }[];

  monte_carlo: {
    simulations: number;
    price: number;
    absolute_error: number;
    standard_error: number;
    confidence_low: number;
    confidence_high: number;
    runtime_seconds: number;
    theoretical_error: number;
  }[];
};


export async function getConvergence(
  input: PricingInput
): Promise<ConvergenceResult> {
  const response = await fetch(
    `${API_URL}/convergence`,
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
    throw new Error(
      `QuantLab API error: ${
        response.status
      }`
    );
  }

  return response.json();
}