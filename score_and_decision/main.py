"""
main.py

VentureX-Ray Scoring & Decision API

FastAPI application exposing the Scoring & Decision module so other
VentureX-Ray team members (Attacker Module, Final Report Module, etc.)
can integrate over plain HTTP/JSON.

Pipeline:

    conversation -> analyzer -> scorer -> decision_engine -> FinalAnalysisResponse

Run with:

    python -m uvicorn main:app --reload

Swagger UI:

    http://127.0.0.1:8000/docs
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException

from modules.scoring.analyzer import AnalyzerError, analyze_conversation
from modules.scoring.decision_engine import make_decision
from modules.scoring.models import (
    AnalysisResult,
    ConversationRequest,
    DecisionResult,
    FinalAnalysisResponse,
)
from modules.scoring.scorer import calculate_defense_score

app = FastAPI(
    title="VentureX-Ray Scoring & Decision API",
    description=(
        "Analyzes an investor <-> founder conversation, calculates a "
        "deterministic defense score, and decides whether the startup's "
        "story is STRONG (ready for final report) or WEAK (needs a "
        "targeted re-attack from a specific attacker module)."
    ),
    version="1.0.0",
)


def _run_pipeline(request: ConversationRequest) -> FinalAnalysisResponse:
    """Shared pipeline logic used by the /analyze endpoint."""
    if not request.conversation:
        raise HTTPException(status_code=400, detail="conversation must not be empty.")

    try:
        analysis: AnalysisResult = analyze_conversation(request.conversation)
    except AnalyzerError as exc:
        raise HTTPException(status_code=502, detail=f"Analysis failed: {exc}") from None

    defense_score = calculate_defense_score(analysis)
    decision: DecisionResult = make_decision(analysis, defense_score)

    return FinalAnalysisResponse(
        defense_score=decision.defense_score,
        analysis=analysis,
        decision=decision.decision,
        next_action=decision.next_action,
        target_attacker=decision.target_attacker,
        weak_areas=decision.weak_areas,
        reason=decision.reason,
    )


@app.get("/")
def root():
    """Basic health/info endpoint."""
    return {
        "service": "VentureX-Ray Scoring & Decision API",
        "status": "ok",
        "docs": "/docs",
    }


@app.post("/api/v1/scoring/analyze", response_model=FinalAnalysisResponse)
def analyze(request: ConversationRequest) -> FinalAnalysisResponse:
    """
    Main endpoint. Runs the full pipeline:

        conversation -> analyzer -> scorer -> decision engine

    Returns defense_score, analysis, decision, next_action, target_attacker,
    weak_areas and reason in a single response.
    """
    return _run_pipeline(request)


@app.post("/api/v1/scoring/score", response_model=AnalysisResult)
def score(request: ConversationRequest) -> AnalysisResult:
    """
    Runs only the analysis step and returns the raw AnalysisResult
    (per-dimension scores, weak areas, and reasoning). Useful for callers
    that only need Claude's analysis without the STRONG/WEAK decision.
    """
    if not request.conversation:
        raise HTTPException(status_code=400, detail="conversation must not be empty.")

    try:
        return analyze_conversation(request.conversation)
    except AnalyzerError as exc:
        raise HTTPException(status_code=502, detail=f"Analysis failed: {exc}") from None


@app.post("/api/v1/scoring/decision", response_model=DecisionResult)
def decision(request: ConversationRequest) -> DecisionResult:
    """
    Runs the full pipeline (analyzer -> scorer -> decision engine) and
    returns only the DecisionResult - useful for callers (like the
    Attacker Module) that only care about STRONG/WEAK routing, not the
    full per-dimension analysis.
    """
    if not request.conversation:
        raise HTTPException(status_code=400, detail="conversation must not be empty.")

    try:
        analysis = analyze_conversation(request.conversation)
    except AnalyzerError as exc:
        raise HTTPException(status_code=502, detail=f"Analysis failed: {exc}") from None

    defense_score = calculate_defense_score(analysis)
    return make_decision(analysis, defense_score)
