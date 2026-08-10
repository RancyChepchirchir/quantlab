from dataclasses import asdict
from pathlib import Path
from time import perf_counter

import json
import numpy as np

from app.models.black_scholes import (
    OptionInputs,
    european_call,
    european_put,
)

from app.models.binomial import (
    binomial_price,
)

from app.models.finite_difference import (
    crank_nicolson_price,
)

from app.models.american_finite_difference import (
    projected_crank_nicolson_put,
)


OUTPUT_DIR = Path("experiments/results")
OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


def absolute_error(
    prediction: float,
    target: float,
) -> float:
    return abs(
        prediction - target
    )


def main():
    european = OptionInputs(
        spot=100.0,
        strike=100.0,
        rate=0.05,
        volatility=0.20,
        maturity=1.0,
        dividend_yield=0.0,
    )

    results = {
        "configuration": {
            "spot": european.spot,
            "strike": european.strike,
            "rate": european.rate,
            "volatility":
                european.volatility,
            "maturity":
                european.maturity,
            "dividend_yield":
                european.dividend_yield,
        },
        "european_call": {},
        "american_put": {},
    }

    # -----------------------------------
    # European analytical benchmark
    # -----------------------------------

    start = perf_counter()

    bs_call = european_call(
        european
    )

    bs_call_runtime = (
        perf_counter() - start
    )

    results[
        "european_call"
    ][
        "black_scholes"
    ] = {
        "price": bs_call,
        "absolute_error": 0.0,
        "runtime_seconds":
            bs_call_runtime,
    }

    # -----------------------------------
    # CRR
    # -----------------------------------

    start = perf_counter()

    crr_call = binomial_price(
        european,
        option_type="call",
        steps=1000,
        american=False,
    )

    crr_runtime = (
        perf_counter() - start
    )

    results[
        "european_call"
    ][
        "crr"
    ] = {
        "price":
            crr_call.price,
        "absolute_error":
            absolute_error(
                crr_call.price,
                bs_call,
            ),
        "runtime_seconds":
            crr_runtime,
        "steps":
            crr_call.steps,
    }

    # -----------------------------------
    # Crank–Nicolson
    # -----------------------------------

    start = perf_counter()

    cn_call = crank_nicolson_price(
        european,
        option_type="call",
        space_steps=200,
        time_steps=200,
    )

    cn_runtime = (
        perf_counter() - start
    )

    results[
        "european_call"
    ][
        "crank_nicolson"
    ] = {
        "price":
            cn_call.price,
        "absolute_error":
            absolute_error(
                cn_call.price,
                bs_call,
            ),
        "runtime_seconds":
            cn_runtime,
        "space_steps": 200,
        "time_steps": 200,
    }

    # -----------------------------------
    # American put
    # -----------------------------------

    european_put_price = european_put(
        european
    )

    start = perf_counter()

    american_crr = binomial_price(
        european,
        option_type="put",
        steps=2000,
        american=True,
    )

    american_crr_runtime = (
        perf_counter() - start
    )

    results[
        "american_put"
    ][
        "crr"
    ] = {
        "price":
            american_crr.price,
        "runtime_seconds":
            american_crr_runtime,
        "steps":
            american_crr.steps,
        "early_exercise_premium":
            american_crr.price
            - european_put_price,
    }

    start = perf_counter()

    american_cn = (
        projected_crank_nicolson_put(
            european,
            space_steps=300,
            time_steps=300,
        )
    )

    american_cn_runtime = (
        perf_counter()
        - start
    )

    results[
        "american_put"
    ][
        "projected_cn"
    ] = {
        "price":
            american_cn.price,
        "absolute_error_vs_crr":
            absolute_error(
                american_cn.price,
                american_crr.price,
            ),
        "runtime_seconds":
            american_cn_runtime,
        "space_steps": 300,
        "time_steps": 300,
        "early_exercise_premium":
            american_cn.price
            - european_put_price,
    }

    output_path = (
        OUTPUT_DIR
        / "benchmark_v1.json"
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            results,
            file,
            indent=2,
        )

    print()
    print(
        "QuantLab Benchmark Suite v1"
    )
    print("=" * 72)

    print()
    print(
        "European call"
    )
    print("-" * 72)

    for method, data in (
        results[
            "european_call"
        ].items()
    ):
        print(
            f"{method:<20}"
            f"{data['price']:>12.6f}"
            f"{data['absolute_error']:>16.6f}"
            f"{data['runtime_seconds']:>16.6f}"
        )

    print()
    print(
        "American put"
    )
    print("-" * 72)

    for method, data in (
        results[
            "american_put"
        ].items()
    ):
        error = data.get(
            "absolute_error_vs_crr",
            0.0,
        )

        print(
            f"{method:<20}"
            f"{data['price']:>12.6f}"
            f"{error:>16.6f}"
            f"{data['runtime_seconds']:>16.6f}"
        )

    print()
    print(
        f"Saved results to "
        f"{output_path}"
    )


if __name__ == "__main__":
    main()