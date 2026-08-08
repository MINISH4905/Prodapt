"""
Unit tests for Agent A (Investor Agent) and Agent B (Answer Analyzer).

The LLM is mocked wherever possible so tests run deterministically without
requiring a real GEMINI_API_KEY.
"""

from unittest.mock import MagicMock

import pytest

from app.agents.answer_analyzer import analyze_answer, _keyword_fallback_analysis
from app.agents.investor_agent import (
    compute_difficulty,
    decide_focus,
    generate_next_question,
)
from app.models.schemas import (
    AnswerAnalysis,
    ConversationTurn,
    InvestorQuestion,
    Role,
    SessionState,
    Vulnerability,
    VulnerabilityMap,
)
from app.services.llm_client import LLMError


def make_state(**overrides) -> SessionState:
    defaults = dict(
        session_id="test-session",
        startup_id="test-startup",
        refined_pitch="A pitch about solving X for Y.",
        vulnerability_map=VulnerabilityMap(
            critical_vulnerabilities=[
                Vulnerability(area="Customer Acquisition", severity="HIGH", reason="CAC unvalidated")
            ]
        ),
        founder_concerns=["Not sure about pricing."],
        max_rounds=8,
    )
    defaults.update(overrides)
    return SessionState(**defaults)


class FakeLLMClient:
    """Minimal fake client satisfying the GeminiClient interface used by agents."""

    def __init__(self, response: dict = None, raise_error: bool = False):
        self.response = response or {}
        self.raise_error = raise_error
        self.calls = []

    def generate_json(self, prompt: str, max_output_tokens: int = 1024) -> dict:
        self.calls.append(prompt)
        if self.raise_error:
            raise LLMError("simulated failure")
        return self.response


# ---------------------------------------------------------------------------
# compute_difficulty
# ---------------------------------------------------------------------------

def test_compute_difficulty_increases_with_round():
    d1 = compute_difficulty(1, 8)
    d_mid = compute_difficulty(4, 8)
    d_last = compute_difficulty(8, 8)
    assert d1 <= d_mid <= d_last
    assert 1 <= d1 <= 5
    assert 1 <= d_last <= 5


def test_compute_difficulty_bounds():
    assert compute_difficulty(1, 1) in range(1, 6)
    assert compute_difficulty(100, 8) == 5


# ---------------------------------------------------------------------------
# decide_focus
# ---------------------------------------------------------------------------

def test_decide_focus_round_1_is_problem():
    state = make_state(round=0)
    focus = decide_focus(state)
    assert "problem" in focus.lower()


def test_decide_focus_round_2_is_customer():
    state = make_state(round=1)
    focus = decide_focus(state)
    assert "who" in focus.lower() or "customer" in focus.lower()


def test_decide_focus_follows_up_on_unsupported_claim():
    state = make_state(
        round=3,
        last_answer_analysis=AnswerAnalysis(
            strength=0.4,
            evidence=False,
            unsupported_claims=["claimed high demand"],
            follow_up_required=True,
        ),
    )
    focus = decide_focus(state)
    assert focus is not None
    assert "evidence" in focus.lower() or "proof" in focus.lower() or "claim" in focus.lower()


def test_decide_focus_targets_unprobed_vulnerability():
    state = make_state(round=3, last_answer_analysis=None)
    focus = decide_focus(state)
    assert focus is not None
    assert "customer acquisition" in focus.lower()


# ---------------------------------------------------------------------------
# generate_next_question
# ---------------------------------------------------------------------------

def test_generate_next_question_uses_llm_output():
    fake_client = FakeLLMClient(
        response={
            "question": "What is your CAC?",
            "topic": "unit_economics",
            "targets_vulnerability": "Customer Acquisition",
            "rationale": "testing",
        }
    )
    state = make_state(round=2)
    question = generate_next_question(state, llm_client=fake_client)
    assert isinstance(question, InvestorQuestion)
    assert question.question == "What is your CAC?"
    assert len(fake_client.calls) == 1


def test_generate_next_question_falls_back_on_llm_error():
    fake_client = FakeLLMClient(raise_error=True)
    state = make_state(round=0)
    question = generate_next_question(state, llm_client=fake_client)
    assert isinstance(question, InvestorQuestion)
    assert question.question  # non-empty fallback question
    assert "problem" in question.question.lower()


def test_generate_next_question_round_2_fallback():
    fake_client = FakeLLMClient(raise_error=True)
    state = make_state(round=1)
    question = generate_next_question(state, llm_client=fake_client)
    assert "who" in question.question.lower()


# ---------------------------------------------------------------------------
# Answer analyzer
# ---------------------------------------------------------------------------

def test_analyze_answer_uses_llm_output():
    fake_client = FakeLLMClient(
        response={
            "strength": 0.9,
            "evidence": True,
            "specificity": 0.8,
            "confidence": 0.8,
            "relevance": 0.9,
            "unsupported_claims": [],
            "contradictions": [],
            "weak_areas": [],
            "vulnerability_exposed": None,
            "follow_up_required": False,
        }
    )
    state = make_state()
    analysis = analyze_answer(
        refined_pitch=state.refined_pitch,
        current_question="What problem do you solve?",
        founder_answer="We surveyed 200 customers and 80% said they'd pay $10/mo.",
        conversation_history=[],
        vulnerability_map=state.vulnerability_map,
        llm_client=fake_client,
    )
    assert isinstance(analysis, AnswerAnalysis)
    assert analysis.strength == 0.9
    assert analysis.evidence is True


def test_analyze_answer_falls_back_on_llm_error():
    fake_client = FakeLLMClient(raise_error=True)
    analysis = analyze_answer(
        refined_pitch="pitch",
        current_question="question?",
        founder_answer="I think maybe it will work out fine.",
        conversation_history=[],
        vulnerability_map=VulnerabilityMap(),
        llm_client=fake_client,
    )
    assert isinstance(analysis, AnswerAnalysis)
    assert 0.0 <= analysis.strength <= 1.0


def test_keyword_fallback_detects_evidence():
    analysis = _keyword_fallback_analysis(
        "We ran a pilot with 50 customers and saw a 30% conversion rate.",
        "What evidence do you have?",
    )
    assert analysis.evidence is True


def test_keyword_fallback_detects_hedging_and_low_confidence():
    analysis = _keyword_fallback_analysis(
        "I think maybe we could probably get some customers eventually.",
        "How will you acquire customers?",
    )
    assert analysis.confidence <= 0.5


def test_keyword_fallback_flags_unsupported_claim():
    analysis = _keyword_fallback_analysis(
        "Our product is clearly the best solution on the market for everyone.",
        "Why would customers choose you?",
    )
    assert len(analysis.unsupported_claims) >= 1


def test_answer_analysis_score_clamping():
    analysis = AnswerAnalysis(strength=1.5, specificity=-0.2, confidence=0.5, relevance=0.5)
    assert 0.0 <= analysis.strength <= 1.0
    assert 0.0 <= analysis.specificity <= 1.0
