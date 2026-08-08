"""
PitchCraft AI - VentureX-Ray
Module 7: Investor Simulation - FastAPI entrypoint.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.investor_routes import router as investor_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="VentureX-Ray - Investor Simulation Module",
    description=(
        "Module 7 of PitchCraft AI / VentureX-Ray. Simulates a skeptical "
        "investor conducting due diligence on a refined startup pitch."
    ),
    version="1.0.0",
)

app.include_router(investor_router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Catch-all so a raw LLM/parsing failure never leaks internals (or an
    API key) back to the client."""
    logger.exception("Unhandled error while processing %s %s", request.method, request.url)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal error while processing the investor simulation request."},
    )


@app.get("/")
def root():
    return {
        "service": "VentureX-Ray Investor Simulation Module",
        "status": "ok",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "ok"}
