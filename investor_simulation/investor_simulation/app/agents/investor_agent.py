"""
Agent A - Investor Agent.

Responsible for deciding: "What should I ask next?"

Design (per spec section 14): Python code controls state, safety constraints,
and the *strategy* (which topic/vulnerability to focus on next). The LLM is
responsible only for turning that strategy into a natural-language investor
question. This keeps the control flow deterministic and testable while still
getting natural, context-aware questions from the model.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from app.models.schemas import (
    AnswerAnalysis,
    ConversationTurn,
    InvestorQuestion,
    SessionState,
    Vulnerability,
    VulnerabilityMap,
)
from app.prompts.investor_prompt import build_investor_prompt
from app.services.llm_client import GeminiClient, LLMError, get_llm_client

logger = logging.getLogger(__name__)

MAX_HISTORY_TURNS_FOR_PROMPT = 12

# Fixed opening topics for the first two rounds, per spec section 6.
ROUND_1_FALLBACK = InvestorQuestion(
    question="What specific problem are you solving, and for whom?",
    topic="problem",
)
ROUND_2_FALLBACK = InvestorQuestion(
    question="Who exactly experiences this problem, and how did you validate that?",
    topic="customer_validation",
)


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


def _format_previous_analysis(analysis: Optional[AnswerAnalysis]) -> Optional[str]:
    if analysis is None:
        return None
    parts = [
        f"strength={analysis.strength}",
        f"evidence={analysis.evidence}",
        f"confidence={analysis.confidence}",
        f"follow_up_required={analysis.follow_up_required}",
    ]
    if analysis.unsupported_claims:
        parts.append("unsupported_claims=" + "; ".join(analysis.unsupported_claims))
    if analysis.contradictions:
        parts.append("contradictions=" + "; ".join(analysis.contradictions))
    if analysis.weak_areas:
        parts.append("weak_areas=" + "; ".join(analysis.weak_areas))
    if analysis.vulnerability_exposed:
        parts.append(f"vulnerability_exposed={analysis.vulnerability_exposed}")
    return "; ".join(parts)


def compute_difficulty(round_number: int, max_rounds: int) -> int:
    """Progressive difficulty on a 1-5 scale based on how far into the
    conversation we are."""
    if max_rounds <= 1:
        return 3
    ratio = (round_number - 1) / max(1, (max_rounds - 1))
    level = 1 + round(ratio * 4)
    return max(1, min(5, level))


def _next_unprobed_vulnerability(
    vmap: VulnerabilityMap, already_probed: List[str]
) -> Optional[Vulnerability]:
    """Pick the next highest-severity vulnerability that hasn't been probed yet."""
    ordered = list(vmap.critical_vulnerabilities) + list(vmap.medium_vulnerabilities)
    for v in ordered:
        if v.area not in already_probed:
            return v
    return None


def decide_focus(state: SessionState) -> Optional[str]:
    """Deterministic control logic (spec section 14) deciding what this
    turn's question should focus on. Returns a short instruction string for
    the LLM prompt, or None to let the LLM choose freely from context.
    """
    round_number = state.round + 1  # the round we are about to ask

    if round_number == 1:
        return "Ask about the core problem being solved and for whom."

    if round_number == 2:
        return "Ask who specifically experiences this problem and how that was validated."

    prev = state.last_answer_analysis
    if prev is not None:
        if prev.contradictions:
            return (
                "The founder's last answer appears to contradict something said earlier. "
                "Directly challenge this inconsistency before moving on."
            )
        if prev.unsupported_claims and not prev.evidence:
            return (
                "The founder's last answer made a claim without evidence. "
                "Press them for concrete proof or data before moving on."
            )
        if prev.follow_up_required and prev.strength < 0.5:
            return (
                "The founder's last answer was weak or vague. Follow up on the same "
                "topic and demand more specificity."
            )

    next_vuln = _next_unprobed_vulnerability(
        state.vulnerability_map, state.vulnerabilities_probed
    )
    if next_vuln is not None and round_number >= 3:
        return (
            f"Steer the question toward this area of concern (without naming it as a "
            f"'flagged vulnerability'): {next_vuln.area} - {next_vuln.reason}"
        )

    if state.difficulty >= 4:
        return "Ask a sharp business/scalability question: unit economics, CAC vs LTV, or defensibility at scale."

    return None


def _fallback_question(state: SessionState) -> InvestorQuestion:
    """Deterministic fallback question when the LLM is unavailable."""
    round_number = state.round + 1

    if round_number == 1:
        return ROUND_1_FALLBACK
    if round_number == 2:
        return ROUND_2_FALLBACK

    next_vuln = _next_unprobed_vulnerability(
        state.vulnerability_map, state.vulnerabilities_probed
    )
    if next_vuln is not None:
        return InvestorQuestion(
            question=(
                f"Let's talk about {next_vuln.area.lower()}. "
                f"What evidence do you have that this won't be a serious risk as you scale?"
            ),
            topic=next_vuln.area.lower().replace(" ", "_"),
            targets_vulnerability=next_vuln.area,
        )

    generic_by_round = {
        3: InvestorQuestion(
            question="What evidence do you have that customers are actually willing to pay for this?",
            topic="willingness_to_pay",
        ),
        4: InvestorQuestion(
            question="Existing companies already offer something similar. Why would customers switch to you?",
            topic="competition",
        ),
        5: InvestorQuestion(
            question="What does it cost you to acquire a customer, and how does that compare to their lifetime value?",
            topic="unit_economics",
        ),
    }
    return generic_by_round.get(
        round_number,
        InvestorQuestion(
            question="What is the biggest risk to this business, and what are you doing about it?",
            topic="general_risk",
        ),
    )


def generate_next_question(
    state: SessionState,
    llm_client: Optional[GeminiClient] = None,
) -> InvestorQuestion:
    """Generate the next investor question for the given session state."""

    client = llm_client or get_llm_client()
    round_number = state.round + 1
    difficulty = compute_difficulty(round_number, state.max_rounds)
    focus = decide_focus(state)

    prompt = build_investor_prompt(
        refined_pitch=state.refined_pitch,
        vulnerability_map_summary=_format_vulnerability_map(state.vulnerability_map),
        founder_concerns=state.founder_concerns,
        conversation_history_text=_format_history(
            state.conversation_history, MAX_HISTORY_TURNS_FOR_PROMPT
        ),
        current_round=round_number,
        max_rounds=state.max_rounds,
        difficulty=difficulty,
        previous_answer_analysis_text=_format_previous_analysis(
            state.last_answer_analysis
        ),
        topics_covered=state.topics_covered,
        suggested_focus=focus,
    )

    try:
        raw = client.generate_json(prompt)
        question = InvestorQuestion.model_validate(raw)
        if not question.question or not question.question.strip():
            raise ValueError("Empty question returned by LLM.")
        return question
    except LLMError as exc:
        logger.warning("Investor agent LLM call failed, using fallback: %s", exc)
    except Exception as exc:  # noqa: BLE001 - validation errors etc.
        logger.warning("Investor agent response invalid, using fallback: %s", exc)

    return _fallback_question(state)
