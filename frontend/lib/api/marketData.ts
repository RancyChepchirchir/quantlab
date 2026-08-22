export type OptionChainQuote = {
  symbol: string;
  expiry: string;

  option_type:
    | "call"
    | "put";

  strike: number;

  bid: number | null;
  ask: number | null;
  last: number | null;

  volume: number | null;

  open_interest:
    number | null;

  implied_volatility:
    number | null;

  source: string;
};


export type OptionChainSnapshot = {
  symbol: string;

  spot: number;

  currency: string;

  expiries:
    string[];

  quotes:
    OptionChainQuote[];

  source: string;

  selected_expiries:
    string[] | null;

  requested_strikes_per_expiry:
    number | null;

  returned_quote_count:
    number | null;

  cache_hit:
    boolean;

  cache_age_seconds:
    number | null;

  cache_ttl_seconds:
    number | null;
};


export type MarketDataErrorDetail = {
  message: string;

  provider:
    string | null;

  upstream_status:
    number | null;

  retryable:
    boolean;

  cached:
    boolean;

  retry_after_seconds:
    number | null;
};


export class MarketDataApiError
  extends Error {

  status: number;

  provider:
    string | null;

  upstreamStatus:
    number | null;

  retryable:
    boolean;

  cached:
    boolean;

  retryAfterSeconds:
    number | null;


  constructor(
    message: string,
    options: {
      status: number;

      provider:
        string | null;

      upstreamStatus:
        number | null;

      retryable:
        boolean;

      cached:
        boolean;

      retryAfterSeconds:
        number | null;
    }
  ) {
    super(
      message
    );

    this.name =
      "MarketDataApiError";

    this.status =
      options.status;

    this.provider =
      options.provider;

    this.upstreamStatus =
      options.upstreamStatus;

    this.retryable =
      options.retryable;

    this.cached =
      options.cached;

    this.retryAfterSeconds =
      options.retryAfterSeconds;
  }
}


export type MarketDataStatus = {
  label: string;

  description: string;

  kind:
    | "fresh"
    | "cached";
};


const API_URL =
  process.env
    .NEXT_PUBLIC_API_URL
  ?? "http://127.0.0.1:8000";


function isRecord(
  value: unknown
): value is Record<
  string,
  unknown
> {
  return (
    typeof value
    === "object"
    && value !== null
  );
}


function numberOrNull(
  value: unknown
): number | null {
  return (
    typeof value
    === "number"
    && Number.isFinite(
      value
    )
  )
    ? value
    : null;
}


function stringOrNull(
  value: unknown
): string | null {
  return (
    typeof value
    === "string"
  )
    ? value
    : null;
}


function booleanValue(
  value: unknown,
  fallback = false
): boolean {
  return (
    typeof value
    === "boolean"
  )
    ? value
    : fallback;
}


function parseErrorDetail(
  payload: unknown
): MarketDataErrorDetail {
  if (
    !isRecord(
      payload
    )
  ) {
    return {
      message:
        "Unable to load market data.",

      provider:
        null,

      upstream_status:
        null,

      retryable:
        false,

      cached:
        false,

      retry_after_seconds:
        null,
    };
  }

  const rawDetail =
    payload.detail;

  if (
    typeof rawDetail
    === "string"
  ) {
    return {
      message:
        rawDetail,

      provider:
        null,

      upstream_status:
        null,

      retryable:
        false,

      cached:
        false,

      retry_after_seconds:
        null,
    };
  }

  if (
    !isRecord(
      rawDetail
    )
  ) {
    return {
      message:
        "Unable to load market data.",

      provider:
        null,

      upstream_status:
        null,

      retryable:
        false,

      cached:
        false,

      retry_after_seconds:
        null,
    };
  }

  return {
    message:
      typeof rawDetail.message
      === "string"
        ? rawDetail.message
        : "Unable to load market data.",

    provider:
      stringOrNull(
        rawDetail.provider
      ),

    upstream_status:
      numberOrNull(
        rawDetail
          .upstream_status
      ),

    retryable:
      booleanValue(
        rawDetail.retryable
      ),

    cached:
      booleanValue(
        rawDetail.cached
      ),

    retry_after_seconds:
      numberOrNull(
        rawDetail
          .retry_after_seconds
      ),
  };
}


function formatErrorMessage(
  detail:
    MarketDataErrorDetail,

  status:
    number
): string {

  if (
    status === 429
  ) {
    if (
      detail.cached
      && detail
        .retry_after_seconds
        != null
    ) {
      const seconds =
        Math.max(
          1,
          Math.ceil(
            detail
              .retry_after_seconds
          )
        );

      return (
        `${detail.message} `
        + `Retry in approximately `
        + `${seconds} second`
        + `${seconds === 1 ? "" : "s"}.`
      );
    }

    return detail.message;
  }


  if (
    status === 403
  ) {
    return (
      detail.message
      || (
        "The configured provider "
        + "does not permit access "
        + "to this market data."
      )
    );
  }


  if (
    status === 502
  ) {
    return (
      detail.message
      || (
        "The upstream market-data "
        + "provider is temporarily "
        + "unavailable."
      )
    );
  }


  return detail.message;
}


export function describeMarketDataSnapshot(
  snapshot:
    OptionChainSnapshot
): MarketDataStatus {

  if (
    snapshot.cache_hit
  ) {
    const age =
      snapshot
        .cache_age_seconds;

    const ageLabel =
      age != null
        ? (
            `${Math.max(
              0,
              Math.round(
                age
              )
            )}s old`
          )
        : "cached";

    return {
      label:
        "Cached",

      description:
        `Cached market snapshot · ${ageLabel}`,

      kind:
        "cached",
    };
  }

  return {
    label:
      "Fresh",

    description:
      "Fresh provider response",

    kind:
      "fresh",
  };
}


export async function loadOptionChain(
  symbol: string,
  provider = "mock",
  refresh = false
): Promise<
  OptionChainSnapshot
> {

  const normalizedSymbol =
    symbol
      .trim()
      .toUpperCase();

  const normalizedProvider =
    provider
      .trim()
      .toLowerCase();

  if (
    !normalizedSymbol
  ) {
    throw new Error(
      "Underlying symbol is required."
    );
  }


  const params =
    new URLSearchParams();

  params.set(
    "provider",
    normalizedProvider
  );

  if (refresh) {
    params.set(
      "refresh",
      "true"
    );
  }


  const response =
    await fetch(
      `${API_URL}/market-data/options/${encodeURIComponent(
        normalizedSymbol
      )}?${params.toString()}`,
      {
        method:
          "GET",

        cache:
          "no-store",
      }
    );


  if (
    !response.ok
  ) {
    let payload:
      unknown = null;

    try {
      payload =
        await response.json();

    } catch {
      payload = null;
    }

    const detail =
      parseErrorDetail(
        payload
      );

    throw new MarketDataApiError(
      formatErrorMessage(
        detail,
        response.status
      ),
      {
        status:
          response.status,

        provider:
          detail.provider,

        upstreamStatus:
          detail
            .upstream_status,

        retryable:
          detail.retryable,

        cached:
          detail.cached,

        retryAfterSeconds:
          detail
            .retry_after_seconds,
      }
    );
  }


  const payload:
    unknown =
      await response.json();


  if (
    !isRecord(
      payload
    )
  ) {
    throw new Error(
      "Market-data API returned an invalid response."
    );
  }


  const snapshot =
  payload as unknown as OptionChainSnapshot;


  if (
    typeof snapshot.symbol
      !== "string"
    || typeof snapshot.spot
      !== "number"
    || !Array.isArray(
      snapshot.quotes
    )
    || !Array.isArray(
      snapshot.expiries
    )
  ) {
    throw new Error(
      "Market-data API returned an incomplete option-chain snapshot."
    );
  }


  return {
    ...snapshot,

    selected_expiries:
      Array.isArray(
        snapshot
          .selected_expiries
      )
        ? snapshot
            .selected_expiries
        : null,

    requested_strikes_per_expiry:
      numberOrNull(
        snapshot
          .requested_strikes_per_expiry
      ),

    returned_quote_count:
      numberOrNull(
        snapshot
          .returned_quote_count
      ),

    cache_hit:
      booleanValue(
        snapshot.cache_hit
      ),

    cache_age_seconds:
      numberOrNull(
        snapshot
          .cache_age_seconds
      ),

    cache_ttl_seconds:
      numberOrNull(
        snapshot
          .cache_ttl_seconds
      ),
  };
}