from fastapi import FastAPI
from fastapi.middleware.cors import (
    CORSMiddleware,
)

from app.api.pricing import (
    router as pricing_router,
)

from app.api.compare import (
    router as compare_router,
)

from app.api.sweep import (
    router as sweep_router,
)

from app.api.convergence import (
    router as convergence_router,
)

from app.api.benchmarks import (
    router as benchmarks_router,
)

import os

from app.api.implied_volatility import (
    router as implied_volatility_router,
)

from app.api.volatility_surface import (
    router as volatility_surface_router,
)


app = FastAPI(
    title="QuantLab API",
    description=(
        "Analytical and numerical "
        "option-pricing laboratory."
    ),
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


frontend_url = os.getenv(
    "FRONTEND_URL",
    "http://localhost:3000",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        frontend_url,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "quantlab-api",
    }


app.include_router(
    pricing_router
)

app.include_router(
    compare_router
)

app.include_router(sweep_router)

app.include_router(
    convergence_router
)

app.include_router(
    benchmarks_router
)

app.include_router(
    implied_volatility_router
)

app.include_router(
    volatility_surface_router
)