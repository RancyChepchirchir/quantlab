import json
from pathlib import Path

from fastapi import APIRouter, HTTPException


router = APIRouter(
    prefix="/benchmarks",
    tags=["benchmarks"],
)


PROJECT_ROOT = Path(
    __file__
).resolve().parents[2]

RESULTS_DIR = (
    PROJECT_ROOT
    / "experiments"
    / "results"
)


@router.get("/v1")
def get_benchmark_v1():
    path = (
        RESULTS_DIR
        / "benchmark_v1.json"
    )

    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                "Benchmark results "
                "have not been generated."
            ),
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)
    

def load_json(
    filename: str,
):
    path = (
        RESULTS_DIR
        / filename
    )

    if not path.exists():
        return None

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(
            file
        )
    

@router.get("/research")
def get_research_results():

    return {
        "classical":
            load_json(
                "benchmark_v1.json"
            ),

        "pinn":
            load_json(
                "american_pinn_v1_vs_v2.json"
            ),

        "deeponet":
            load_json(
                "american_deeponet.json"
            ),

        "amortisation":
            load_json(
                "american_deeponet_benchmark.json"
            ),
    }