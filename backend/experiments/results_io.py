from pathlib import Path
from typing import Any

import json

from typing import Any, Dict


RESULTS_DIR = Path(
    "experiments/results"
)

RESULTS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


def save_result(
    filename: str,
    payload: Dict[str, Any],
) -> Path:
    path = (
        RESULTS_DIR
        / filename
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            payload,
            file,
            indent=2,
        )

    print()
    print(
        f"Saved results to {path}"
    )

    return path