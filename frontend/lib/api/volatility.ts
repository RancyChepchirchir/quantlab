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
};

export type VolatilitySurfaceResponse = {
  spot: number;
  rate: number;
  dividend_yield: number;
  quote_count: number;
  quotes: CalibratedVolatilityQuote[];
};

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  "http://127.0.0.1:8000";

export async function calibrateVolatilitySurface(
  input: {
    spot: number;
    rate: number;
    dividend_yield: number;
    quotes: VolatilityQuoteInput[];
  }
): Promise<VolatilitySurfaceResponse> {
  const response = await fetch(
    `${API_URL}/calibration/volatility-surface`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(input),
    }
  );

  if (!response.ok) {
    const message =
      await response.text();

    throw new Error(
      message ||
      "Volatility calibration failed."
    );
  }

  return response.json();
}