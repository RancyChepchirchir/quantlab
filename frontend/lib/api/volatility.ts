export type VolatilityQuoteInput = {
  strike: number;
  maturity: number;
  market_price: number;

  option_type:
    | "call"
    | "put";
};


export type CalibratedVolatilityQuote = {
  strike: number;
  maturity: number;
  market_price: number;

  option_type:
    | "call"
    | "put";

  implied_volatility:
    number;

  implied_volatility_percent:
    number;

  american_implied_volatility:
    number | null;

  american_implied_volatility_percent:
    number | null;

  american_iv_difference:
    number | null;

  american_iv_difference_percentage_points:
    number | null;

  american_iv_converged:
    boolean | null;
};


export type RejectedVolatilityQuote = {
  strike: number;
  maturity: number;
  market_price: number;
  option_type: string;
  reason: string;
};


export type MoneynessDiagnostic = {
  strike: number;
  maturity: number;

  option_type:
    | "call"
    | "put";

  implied_volatility:
    number;

  implied_volatility_percent:
    number;

  moneyness:
    number;

  log_moneyness:
    number;
};


export type SkewDiagnostic = {
  maturity: number;

  atm_strike:
    number;

  atm_implied_volatility:
    number;

  atm_implied_volatility_percent:
    number;

  skew_slope:
    number | null;

  observation_count:
    number;
};


export type AtmTermStructurePoint = {
  maturity: number;

  atm_strike:
    number;

  atm_implied_volatility:
    number;

  atm_implied_volatility_percent:
    number;
};


export type PutCallParityDiagnostic = {
  strike: number;
  maturity: number;

  call_price:
    number;

  put_price:
    number;

  theoretical_difference:
    number;

  observed_difference:
    number;

  parity_error:
    number;

  absolute_parity_error:
    number;
};


export type VolatilityDiagnostics = {
  moneyness:
    MoneynessDiagnostic[];

  skew:
    SkewDiagnostic[];

  atm_term_structure:
    AtmTermStructurePoint[];

  put_call_parity:
    PutCallParityDiagnostic[];

  mean_absolute_parity_error:
    number | null;

  max_absolute_parity_error:
    number | null;
};


export type VolatilitySurfaceGridPoint = {
  strike: number;
  maturity: number;

  implied_volatility:
    number;

  implied_volatility_percent:
    number;
};


export type VolatilitySurfaceGrid = {
  strikes:
    number[];

  maturities:
    number[];

  observed_strike_count:
    number;

  observed_maturity_count:
    number;

  is_two_dimensional:
    boolean;

  points:
    VolatilitySurfaceGridPoint[];
};


export type SVIParameters = {
  maturity: number;

  a: number;
  b: number;
  rho: number;
  m: number;
  sigma: number;

  rmse: number;

  observation_count:
    number;
};


export type SVIFittedPoint = {
  strike: number;
  maturity: number;

  log_moneyness:
    number;

  observed_iv:
    number | null;

  observed_iv_percent:
    number | null;

  fitted_iv:
    number;

  fitted_iv_percent:
    number;

  total_variance:
    number;
};


export type SVIArbitrageDiagnostic = {
  maturity:
    number;

  minimum_total_variance:
    number;

  negative_variance_detected:
    boolean;

  invalid_parameter_region:
    boolean;

  butterfly_warning:
    boolean;
};


export type SVICalendarDiagnostic = {
  shorter_maturity:
    number;

  longer_maturity:
    number;

  minimum_variance_difference:
    number;

  violation_detected:
    boolean;

  violation_count:
    number;

  comparison_point_count:
    number;

  violation_fraction:
    number;
};


export type SVISmile = {
  parameters:
    SVIParameters;

  points:
    SVIFittedPoint[];

  arbitrage:
    SVIArbitrageDiagnostic;
};


export type SVISurface = {
  fitted_maturity_count:
    number;

  calendar_warning:
    boolean;

  calendar_diagnostics:
    SVICalendarDiagnostic[];

  smiles:
    SVISmile[];
};


export type VolatilitySurfaceResponse = {
  spot:
    number;

  rate:
    number;

  dividend_yield:
    number;

  quote_count:
    number;

  calibrated_count:
    number;

  rejected_count:
    number;

  success_rate:
    number;

  quotes:
    CalibratedVolatilityQuote[];

  rejected_quotes:
    RejectedVolatilityQuote[];

  diagnostics:
    VolatilityDiagnostics;

  surface_grid:
    VolatilitySurfaceGrid;

  svi:
    SVISurface;
};


const API_URL =
  process.env
    .NEXT_PUBLIC_API_URL
  ?? "http://127.0.0.1:8000";


export async function calibrateVolatilitySurface(
  input: {
    spot: number;

    rate: number;

    dividend_yield:
      number;

    quotes:
      VolatilityQuoteInput[];
  }
): Promise<
  VolatilitySurfaceResponse
> {
  const response =
    await fetch(
      `${API_URL}/calibration/volatility-surface`,
      {
        method:
          "POST",

        headers: {
          "Content-Type":
            "application/json",
        },

        body:
          JSON.stringify(
            input
          ),
      }
    );

  if (
    !response.ok
  ) {
    let message =
      "Volatility calibration failed.";

    try {
      const payload =
        await response.json();

      if (
        typeof payload
          ?.detail
        === "string"
      ) {
        message =
          payload.detail;
      }

    } catch {
      const text =
        await response.text();

      if (text) {
        message =
          text;
      }
    }

    throw new Error(
      message
    );
  }

  return (
    response.json()
  );
}