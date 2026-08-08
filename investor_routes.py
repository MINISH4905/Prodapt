"""
API routes for Module 7 - Investor Simulation.

Endpoints:
  POST /investor/start
  POST /investor/answer
  GET  /investor/session/{session_id}
  POST /investor/end
"""

from __future__ import annotations

import logging
import os

from fastapi import APIRouter, HTTPException

from app.agents.answer_analyzer import analyze_answer
from app.agents.investor_agent import generate_next_question
from app.models.schemas import (
    AnswerRequest,
    AnswerResponse,
    ConversationTurn,
    FinalResult,
    FounderPerformance,
    Role,
    SessionStatus,
    SessionView,
    StartSessionRequest,
    StartSessionResponse,
    StopReason,
)
from app.services.session_manager import (
    SessionAlreadyExistsError,
    SessionNotFoundError,
    get_session_manager,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/investor", tags=["investor-simulation"])

MAX_ANSWER_LENGTH = int(os.environ.get("MAX_ANSWER_LENGTH", "4000"))

# A session is considered to have gathered "sufficient evidence" once at
# least this many rounds have passed AND the last few answers were
# consistently strong. This keeps the stopping condition simple and
# explainable for a hackathon MVP (spec section 8).
SUFFICIENT_EVIDENCE_MIN_ROUNDS = 4
SUFFICIENT_EVIDENCE_STRENGTH_THRESHOLD = 0.8
SUFFICIENT_EVIDENCE_LOOKBACK = 3


def _check_stopping_condition(state) -> "StopReason | None":
    """Return a StopReason if the session should stop now, else None."""
    if state.round >= state.max_rounds:
        return StopReason.max_rounds_reached

    if state.round >= SUFFICIENT_EVIDENCE_MIN_ROUNDS:
        founder_turns = [t for t in state.conversation_history if t.role == Role.founder]
        recent = founder_turns[-SUFFICIENT_EVIDENCE_LOOKBACK:]
        if len(recent) >= SUFFICIENT_EVIDENCE_LOOKBACK:
            # We don't have per-turn strength stored on the turn itself, so we
            # approximate using the last_answer_analysis plus weak_areas/
            # unsupported_claims accumulated so far - if both are empty and
            # the most recent analysis is strong, we consider evidence
            # sufficient.
            analysis = state.last_answer_analysis
            if (
                analysis is not None
                and analysis.strength >= SUFFICIENT_EVIDENCE_STRENGTH_THRESHOLD
                and not analysis.unsupported_claims
                and not analysis.contradictions
                and len(state.unsupported_claims) == 0
            ):
                return StopReason.sufficient_evidence

    return None


def _build_final_result(state) -> FinalResult:
    founder_turns_analyses = []
    # We only keep the latest analysis explicitly, but we can reconstruct an
    # approximate performance summary from accumulated tracking fields plus
    # the last analysis for this MVP.
    analysis = state.last_answer_analysis

    overall_strength = analysis.strength if analysis else 0.5
    evidence_quality = (
        1.0 if analysis and analysis.evidence else (0.3 if state.evidence_found else 0.2)
    )
    clarity = analysis.specificity if analysis else 0.5
    total_claims = len(state.unsupported_claims)
    consistency = max(0.0, 1.0 - min(1.0, total_claims * 0.15))

    performance = FounderPerformance(
        overall_strength=round(overall_strength, 2),
        evidence_quality=round(evidence_quality, 2),
        clarity=round(clarity, 2),
        consistency=round(consistency, 2),
    )

    investor_concerns = []
    for v in state.vulnerability_map.all_vulnerabilities():
        if v.area in state.vulnerabilities_probed:
            investor_concerns.append(v.area)
    # Also surface any weak areas discovered during the conversation itself.
    for area in state.weak_areas:
        if area not in investor_concerns:
            investor_concerns.append(area)

    avg_score = (
        performance.overall_strength * 0.4
        + performance.evidence_quality * 0.3
        + performance.consistency * 0.3
    )
    if avg_score >= 0.75:
        recommendation = "STRONG"
    elif avg_score >= 0.5:
        recommendation = "NEEDS_IMPROVEMENT"
    else:
        recommendation = "WEAK"

    return FinalResult(
        session_id=state.session_id,
        status=SessionStatus.completed,
        total_rounds=state.round,
        conversation=state.conversation_history,
        founder_performance=performance,
        weak_areas=list(dict.fromkeys(state.weak_areas)),
        unsupported_claims=list(dict.fromkeys(state.unsupported_claims)),
        investor_concerns=list(dict.fromkeys(investor_concerns)),
        recommendation=recommendation,
    )


@router.post("/start", response_model=StartSessionResponse)
def start_session(payload: StartSessionRequest):
    manager = get_session_manager()

    try:
        state = manager.create_session(
            session_id=payload.session_id,
            startup_id=payload.startup_id,
            refined_pitch=payload.refined_pitch,
            vulnerability_map=payload.vulnerability_map,
            founder_concerns=payload.founder_concerns,
            max_rounds=payload.max_rounds,
        )
    except SessionAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    question = generate_next_question(state)

    state.round = 1
    state.current_question = question.question
    state.current_question_topic = question.topic
    state.current_question_targets = question.targets_vulnerability
    state.conversation_history.append(
        ConversationTurn(role=Role.investor, message=question.question, round=state.round)
    )
    if question.topic and question.topic not in state.topics_covered:
        state.topics_covered.append(question.topic)
    if question.targets_vulnerability and (
        question.targets_vulnerability not in state.vulnerabilities_probed
    ):
        state.vulnerabilities_probed.append(question.targets_vulnerability)

    manager.save(state)

    return StartSessionResponse(
        session_id=state.session_id,
        round=state.round,
        question=question.question,
        status=state.status,
    )


@router.post("/answer", response_model=AnswerResponse)
def submit_answer(payload: AnswerRequest):
    manager = get_session_manager()

    try:
        state = manager.get(payload.session_id)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if state.status == SessionStatus.completed:
        raise HTTPException(
            status_code=400, detail="This session has already been completed."
        )

    if state.current_question is None:
        raise HTTPException(
            status_code=400, detail="No active question to answer for this session."
        )

    if len(payload.answer) > MAX_ANSWER_LENGTH:
        raise HTTPException(
            status_code=422,
            detail=f"Answer exceeds maximum length of {MAX_ANSWER_LENGTH} characters.",
        )

    state.conversation_history.append(
        ConversationTurn(role=Role.founder, message=payload.answer, round=state.round)
    )

    analysis = analyze_answer(
        refined_pitch=state.refined_pitch,
        current_question=state.current_question,
        founder_answer=payload.answer,
        conversation_history=state.conversation_history,
        vulnerability_map=state.vulnerability_map,
    )

    state.last_answer_analysis = analysis
    for claim in analysis.unsupported_claims:
        if claim not in state.unsupported_claims:
            state.unsupported_claims.append(claim)
    for area in analysis.weak_areas:
        if area not in state.weak_areas:
            state.weak_areas.append(area)
    if analysis.evidence:
        state.evidence_found.append(payload.answer[:200])
    if analysis.vulnerability_exposed and (
        analysis.vulnerability_exposed not in state.vulnerabilities_probed
    ):
        state.vulnerabilities_probed.append(analysis.vulnerability_exposed)

    state.difficulty = _recompute_difficulty(state)

    stop_reason = _check_stopping_condition(state)

    next_question_text = None
    if stop_reason is not None:
        state.status = SessionStatus.completed
        state.stop_reason = stop_reason
        state.current_question = None
    else:
        question = generate_next_question(state)
        state.round += 1
        state.current_question = question.question
        state.current_question_topic = question.topic
        state.current_question_targets = question.targets_vulnerability
        state.conversation_history.append(
            ConversationTurn(role=Role.investor, message=question.question, round=state.round)
        )
        if question.topic and question.topic not in state.topics_covered:
            state.topics_covered.append(question.topic)
        if question.targets_vulnerability and (
            question.targets_vulnerability not in state.vulnerabilities_probed
        ):
            state.vulnerabilities_probed.append(question.targets_vulnerability)
        next_question_text = question.question

    manager.save(state)

    return AnswerResponse(
        session_id=state.session_id,
        round=state.round,
        question=next_question_text,
        answer_analysis=analysis,
        status=state.status,
        stop_reason=state.stop_reason,
    )


def _recompute_difficulty(state) -> int:
    from app.agents.investor_agent import compute_difficulty

    return compute_difficulty(state.round + 1, state.max_rounds)


@router.get("/session/{session_id}", response_model=SessionView)
def get_session(session_id: str):
    manager = get_session_manager()
    try:
        state = manager.get(session_id)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return SessionView(
        session_id=state.session_id,
        startup_id=state.startup_id,
        round=state.round,
        max_rounds=state.max_rounds,
        status=state.status,
        conversation_history=state.conversation_history,
        topics_covered=state.topics_covered,
        weak_areas=state.weak_areas,
        unsupported_claims=state.unsupported_claims,
        evidence_found=state.evidence_found,
    )


@router.post("/end", response_model=FinalResult)
def end_session(payload: dict):
    session_id = payload.get("session_id") if isinstance(payload, dict) else None
    if not session_id:
        raise HTTPException(status_code=422, detail="session_id is required.")

    manager = get_session_manager()
    try:
        state = manager.get(session_id)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if state.status != SessionStatus.completed:
        state.status = SessionStatus.completed
        state.stop_reason = StopReason.manually_ended
        state.current_question = None
        manager.save(state)

    return _build_final_result(state)
