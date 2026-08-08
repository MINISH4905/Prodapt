"""
Pydantic models for Module 7 - Investor Simulation.

These models define:
  - The API request/response contracts (schemas prefixed with nothing special,
    used directly by FastAPI routes).
  - The internal conversation state that is kept in the session manager.
  - The structured objects that the LLM is instructed to return (AnswerAnalysis,
    InvestorQuestion) so we can validate model output instead of trusting raw text.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Shared enums / small value objects
# ---------------------------------------------------------------------------

class Role(str, Enum):
    investor = "investor"
    founder = "founder"


class SessionStatus(str, Enum):
    active = "active"
    completed = "completed"


class StopReason(str, Enum):
    max_rounds_reached = "max_rounds_reached"
    sufficient_evidence = "sufficient_evidence"
    manually_ended = "manually_ended"


class Vulnerability(BaseModel):
    """A single vulnerability entry, matching the Vulnerability Map format
    produced by the upstream Attacker modules."""

    area: str
    severity: str = Field(default="MEDIUM", description="LOW | MEDIUM | HIGH")
    reason: str = ""


class VulnerabilityMap(BaseModel):
    critical_vulnerabilities: List[Vulnerability] = Field(default_factory=list)
    medium_vulnerabilities: List[Vulnerability] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)

    def all_vulnerabilities(self) -> List[Vulnerability]:
        return self.critical_vulnerabilities + self.medium_vulnerabilities


class ConversationTurn(BaseModel):
    role: Role
    message: str
    round: Optional[int] = None
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# ---------------------------------------------------------------------------
# Structured LLM outputs
# ---------------------------------------------------------------------------

class AnswerAnalysis(BaseModel):
    """Structured output produced by the Answer Analyzer agent."""

    strength: float = Field(ge=0.0, le=1.0, default=0.5)
    evidence: bool = False
    specificity: float = Field(ge=0.0, le=1.0, default=0.5)
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    relevance: float = Field(ge=0.0, le=1.0, default=0.5)
    unsupported_claims: List[str] = Field(default_factory=list)
    contradictions: List[str] = Field(default_factory=list)
    weak_areas: List[str] = Field(default_factory=list)
    vulnerability_exposed: Optional[str] = None
    follow_up_required: bool = True

    @field_validator("strength", "specificity", "confidence", "relevance", mode="before")
    @classmethod
    def _clamp_scores(cls, v):
        try:
            v = float(v)
        except (TypeError, ValueError):
            return 0.5
        return max(0.0, min(1.0, v))


class InvestorQuestion(BaseModel):
    """Structured output produced by the Investor Agent."""

    question: str
    topic: str = "general"
    targets_vulnerability: Optional[str] = None
    rationale: Optional[str] = None


# ---------------------------------------------------------------------------
# Internal session state (kept explicitly in Python, NOT relying on LLM memory)
# ---------------------------------------------------------------------------

class SessionState(BaseModel):
    session_id: str
    startup_id: str

    round: int = 0
    max_rounds: int = 8
    difficulty: int = 1

    refined_pitch: str
    vulnerability_map: VulnerabilityMap = Field(default_factory=VulnerabilityMap)
    founder_concerns: List[str] = Field(default_factory=list)

    conversation_history: List[ConversationTurn] = Field(default_factory=list)

    current_question: Optional[str] = None
    current_question_topic: Optional[str] = None
    current_question_targets: Optional[str] = None

    last_answer_analysis: Optional[AnswerAnalysis] = None

    topics_covered: List[str] = Field(default_factory=list)
    vulnerabilities_probed: List[str] = Field(default_factory=list)
    unsupported_claims: List[str] = Field(default_factory=list)
    evidence_found: List[str] = Field(default_factory=list)
    weak_areas: List[str] = Field(default_factory=list)

    status: SessionStatus = SessionStatus.active
    stop_reason: Optional[StopReason] = None

    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# ---------------------------------------------------------------------------
# API request / response models
# ---------------------------------------------------------------------------

class StartSessionRequest(BaseModel):
    session_id: str
    startup_id: str
    refined_pitch: str = Field(min_length=1, max_length=20000)
    vulnerability_map: VulnerabilityMap = Field(default_factory=VulnerabilityMap)
    founder_concerns: List[str] = Field(default_factory=list)
    max_rounds: Optional[int] = Field(default=None, ge=1, le=30)


class StartSessionResponse(BaseModel):
    session_id: str
    round: int
    question: str
    status: SessionStatus = SessionStatus.active


class AnswerRequest(BaseModel):
    session_id: str
    answer: str = Field(min_length=1, max_length=8000)


class AnswerResponse(BaseModel):
    session_id: str
    round: int
    question: Optional[str] = None
    answer_analysis: AnswerAnalysis
    status: SessionStatus
    stop_reason: Optional[StopReason] = None


class SessionView(BaseModel):
    session_id: str
    startup_id: str
    round: int
    max_rounds: int
    status: SessionStatus
    conversation_history: List[ConversationTurn]
    topics_covered: List[str]
    weak_areas: List[str]
    unsupported_claims: List[str]
    evidence_found: List[str]


class FounderPerformance(BaseModel):
    overall_strength: float = 0.0
    evidence_quality: float = 0.0
    clarity: float = 0.0
    consistency: float = 0.0


class FinalResult(BaseModel):
    session_id: str
    status: SessionStatus
    total_rounds: int
    conversation: List[ConversationTurn]
    founder_performance: FounderPerformance
    weak_areas: List[str]
    unsupported_claims: List[str]
    investor_concerns: List[str]
    recommendation: str
