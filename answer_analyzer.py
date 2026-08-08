"""
Agent B - Answer Analyzer.

Responsible ONLY for answering: "How strong was the founder's answer?"
Does not decide what to ask next - see agents/investor_agent.py for that.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from app.models.schemas import AnswerAnalysis, ConversationTurn, VulnerabilityMap
from app.prompts.analyzer_prompt import build_analyzer_prompt
from app.services.llm_client import GeminiClient, LLMError, get_llm_client

logger = logging.getLogger(__name__)

MAX_HISTORY_TURNS_FOR_PROMPT = 12


def _format_history(history: List[ConversationTurn], max_turns: int) -> str:
    trimmed = history[-max_turns:] if max_turns else history
    lines = []
    for turn in trimmed:
        speaker = "INVESTOR" if turn.role.value == "investor" else "FOUNDER"
        lines.append(f"{speaker}: {turn.message}")
    return "\n".join(lines)


def _format_vulnerability_map(vmap: VulnerabilityMap) -> str:
    lines = []
    for v in vmap.critical_vulnerabilities:
        lines.append(f"- [CRITICAL] {v.area}: {v.reason}")
    for v in vmap.medium_vulnerabilities:
        lines.append(f"- [MEDIUM] {v.area}: {v.reason}")
    if vmap.strengths:
        lines.append("Strengths: " + "; ".join(vmap.strengths))
    return "\n".join(lines) if lines else "No known vulnerabilities recorded."


def _keyword_fallback_analysis(
    founder_answer: str, current_question: str
) -> AnswerAnalysis:
    """Deterministic fallback used when the LLM is unavailable or fails.

    Very simple heuristics so the API never breaks even without an LLM key.
    """
    text = founder_answer.lower().strip()
    word_count = len(text.split())

    evidence_markers = [
        "%", "data", "pilot", "customers", "users", "survey", "interview",
        "revenue", "signed", "letter of intent", "loi", "beta", "tested",
        "study", "results", "metric", "conversion", "retention",
    ]
    hedge_markers = [
        "i think", "probably", "maybe", "we believe", "should be",
        "hopefully", "not sure", "i guess", "kind of", "sort of",
    ]

    has_evidence = any(marker in text for marker in evidence_markers)
    is_hedgy = any(marker in text for marker in hedge_markers)

    specificity = min(1.0, word_count / 60.0)
    confidence = 0.3 if is_hedgy else 0.65
    relevance = 0.5 if word_count > 3 else 0.2
    strength = round(
        max(0.05, min(0.95, (specificity * 0.4) + (0.3 if has_evidence else 0.0) + (confidence * 0.3))),
        2,
    )

    unsupported = []
    if not has_evidence and word_count > 5:
        unsupported.append("Claim made without supporting evidence or data.")

    weak_areas = []
    if not has_evidence:
        weak_areas.append("evidence")
    if is_hedgy:
        weak_areas.append("confidence")
    if word_count < 8:
        weak_areas.append("specificity")

    return AnswerAnalysis(
        strength=strength,
        evidence=has_evidence,
        specificity=round(specificity, 2),
        confidence=round(confidence, 2),
        relevance=round(relevance, 2),
        unsupported_claims=unsupported,
        contradictions=[],
        weak_areas=weak_areas,
        vulnerability_exposed=None,
        follow_up_required=strength < 0.6,
    )


def analyze_answer(
    refined_pitch: str,
    current_question: str,
    founder_answer: str,
    conversation_history: List[ConversationTurn],
    vulnerability_map: VulnerabilityMap,
    llm_client: Optional[GeminiClient] = None,
) -> AnswerAnalysis:
    """Analyze the founder's latest answer using the LLM, with a safe fallback."""

    client = llm_client or get_llm_client()

    prompt = build_analyzer_prompt(
        refined_pitch=refined_pitch,
        current_question=current_question,
        founder_answer=founder_answer,
        conversation_history_text=_format_history(
            conversation_history, MAX_HISTORY_TURNS_FOR_PROMPT
        ),
        vulnerability_map_summary=_format_vulnerability_map(vulnerability_map),
    )

    try:
        raw = client.generate_json(prompt)
        return AnswerAnalysis.model_validate(raw)
    except LLMError as exc:
        logger.warning("Answer analyzer LLM call failed, using fallback: %s", exc)
    except Exception as exc:  # noqa: BLE001 - validation errors etc.
        logger.warning("Answer analyzer response invalid, using fallback: %s", exc)

    return _keyword_fallback_analysis(founder_answer, current_question)
