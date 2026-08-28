export type VolatilityQuoteInput = {
  strike: number;
  maturity: number;
  market_price: number;
  option_type: "call" | "put";
};


export type CalibratedVolatilityQuote = {
  strike: number;
  maturity: number;
  market_price: number;
  option_type: "call" | "put";

  implied_volatility: number;
  implied_volatility_percent: number;

  american_implied_volatility:
    number | null;

  american_implied_volatility_percent:
    number | null;

  american_iv_difference:
    number | null;

  american_iv_difference_percentage_points:
    number | null;

  american_iv_converged:
    boolean;
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
  option_type: string;

  implied_volatility: number;
  implied_volatility_percent: number;

  moneyness: number;
  log_moneyness: number;
};


export type SkewDiagnostic = {
  maturity: number;

  atm_strike: number;

  atm_implied_volatility: number;
  atm_implied_volatility_percent: number;

  skew_slope: number;

  observation_count: number;
};


export type AtmTermStructurePoint = {
  maturity: number;

  atm_strike: number;

  atm_implied_volatility: number;
  atm_implied_volatility_percent: number;
};


export type PutCallParityDiagnostic = {
  strike: number;
  maturity: number;

  call_price: number;
  put_price: number;

  theoretical_difference: number;
  observed_difference: number;

  parity_error: number;
  absolute_parity_error: number;
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


export type VolatilitySurfacePoint = {
  strike: number;
  maturity: number;

  implied_volatility: number;
  implied_volatility_percent: number;
};


export type VolatilitySurfaceGrid = {
  strikes: number[];
  maturities: number[];

  observed_strike_count: number;
  observed_maturity_count: number;

  is_two_dimensional: boolean;

  points:
    VolatilitySurfacePoint[];
};


export type SVIParameters = {
  maturity: number;

  a: number;
  b: number;
  rho: number;
  m: number;
  sigma: number;

  rmse: number;

  observation_count: number;
};


export type SVIPoint = {
  strike: number;
  maturity: number;

  log_moneyness: number;

  observed_iv:
    number | null;

  observed_iv_percent:
    number | null;

  fitted_iv: number;
  fitted_iv_percent: number;

  total_variance: number;
};


export type SVIArbitrageDiagnostic = {
  maturity: number;

  minimum_total_variance: number;

  negative_variance_detected:
    boolean;

  invalid_parameter_region:
    boolean;

  butterfly_warning:
    boolean;
};


export type SVISmile = {
  parameters:
    SVIParameters;

  points:
    SVIPoint[];

  arbitrage:
    SVIArbitrageDiagnostic;
};


export type SVICalendarDiagnostic = {
  shorter_maturity: number;
  longer_maturity: number;

  minimum_variance_difference:
    number;

  violation_detected: boolean;

  violation_count: number;

  comparison_point_count:
    number;

  violation_fraction:
    number;
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


// ============================================================
// SSVI
// ============================================================


export type SSVIParameters = {
  eta: number;
  rho: number;
  gamma: number;

  rmse: number;

  observation_count: number;
  maturity_count: number;
};


export type SSVIAtmSlice = {
  maturity: number;

  forward: number;

  atm_strike: number;
  atm_implied_volatility:
    number;

  theta: number;
};


export type SSVIPoint = {
  strike: number;
  maturity: number;

  forward: number;

  log_forward_moneyness:
    number;

  theta: number;

  observed_iv:
    number | null;

  fitted_iv: number;

  observed_total_variance:
    number | null;

  fitted_total_variance:
    number;
};


export type SSVIArbitrageDiagnostic = {
  maturity: number;

  theta: number;
  phi: number;

  first_butterfly_bound:
    number;

  second_butterfly_bound:
    number;

  first_bound_satisfied:
    boolean;

  second_bound_satisfied:
    boolean;

  butterfly_warning:
    boolean;
};


export type SSVICalendarDiagnostic = {
  shorter_maturity: number;
  longer_maturity: number;

  minimum_variance_difference:
    number;

  violation_detected:
    boolean;

  violation_count:
    number;

  comparison_point_count:
    number;
};


export type SSVISurface = {
  available: boolean;

  parameters:
    SSVIParameters | null;

  atm_slices:
    SSVIAtmSlice[];

  points:
    SSVIPoint[];

  arbitrage_diagnostics:
    SSVIArbitrageDiagnostic[];

  calendar_diagnostics:
    SSVICalendarDiagnostic[];

  butterfly_warning:
    boolean | null;

  calendar_warning:
    boolean | null;

  message:
    string | null;
};

// ============================================================
// Main API response
// ============================================================


export type VolatilitySurfaceResponse = {
  spot: number;
  rate: number;
  dividend_yield: number;

  quote_count: number;
  calibrated_count: number;
  rejected_count: number;
  success_rate: number;

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

  ssvi:
    SSVISurface;

  arbitrage_layers: VolatilityArbitrageLayers | null;
};

export interface CalendarArbitrageViolation {
  strike: number;
  earlier_maturity: number;
  later_maturity: number;
  earlier_total_variance: number;
  later_total_variance: number;
  difference: number;
}

export interface ButterflyArbitrageViolation {
  maturity: number;
  left_strike: number;
  center_strike: number;
  right_strike: number;
  curvature: number;
}

export interface VolatilityArbitrageDiagnostics {
  calendar_arbitrage_free: boolean;
  butterfly_arbitrage_free: boolean;
  arbitrage_free: boolean;

  calendar_violation_count: number;
  butterfly_violation_count: number;
  total_violation_count: number;

  calendar_violations: CalendarArbitrageViolation[];
  butterfly_violations: ButterflyArbitrageViolation[];
}

export interface VolatilityArbitrageLayer {
  name: string;
  diagnostics: VolatilityArbitrageDiagnostics;
}

export interface VolatilityArbitrageLayers {
  market: VolatilityArbitrageLayer;
  svi: VolatilityArbitrageLayer;
  ssvi: VolatilityArbitrageLayer;
}

const API_URL =
  process.env
    .NEXT_PUBLIC_API_URL
  ?? "http://127.0.0.1:8000";


export async function calibrateVolatilitySurface(
  payload: {
    spot: number;
    rate: number;
    dividend_yield: number;

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
            payload
          ),

        cache:
          "no-store",
      }
    );


  let data:
    unknown = null;


  try {
    data =
      await response.json();

  } catch {
    data = null;
  }


  if (
    !response.ok
  ) {
    let message =
      "Volatility calibration failed.";

    if (
      typeof data
      === "object"
      && data !== null
      && "detail" in data
    ) {
      const detail =
        (
          data as {
            detail?: unknown;
          }
        ).detail;

      if (
        typeof detail
        === "string"
      ) {
        message =
          detail;
      }
    }

    throw new Error(
      message
    );
  }


  return (
    data as
      VolatilitySurfaceResponse
  );
}