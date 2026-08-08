"""
Integration tests for the FastAPI investor simulation endpoints.

The LLM-backed agent functions are monkeypatched so tests are deterministic
and do not require a real GEMINI_API_KEY or network access.
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import AnswerAnalysis, InvestorQuestion
from app.services.session_manager import get_session_manager

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_sessions():
    """Ensure each test starts with a clean in-memory session store."""
    manager = get_session_manager()
    for sid in manager.all_session_ids():
        manager.delete(sid)
    yield
    for sid in manager.all_session_ids():
        manager.delete(sid)


@pytest.fixture(autouse=True)
def patch_agents(monkeypatch):
    """Patch out real LLM calls in the route module with deterministic stubs."""

    question_counter = {"n": 0}

    def fake_generate_next_question(state, llm_client=None):
        question_counter["n"] += 1
        return InvestorQuestion(
            question=f"Stub investor question #{question_counter['n']}?",
            topic=f"topic_{question_counter['n']}",
            targets_vulnerability=None,
        )

    def fake_analyze_answer(**kwargs):
        return AnswerAnalysis(
            strength=0.7,
            evidence=True,
            specificity=0.6,
            confidence=0.6,
            relevance=0.7,
            unsupported_claims=[],
            contradictions=[],
            weak_areas=[],
            vulnerability_exposed=None,
            follow_up_required=False,
        )

    monkeypatch.setattr(
        "app.api.investor_routes.generate_next_question", fake_generate_next_question
    )
    monkeypatch.setattr("app.api.investor_routes.analyze_answer", fake_analyze_answer)
    yield


def sample_start_payload(session_id=None, max_rounds=3):
    return {
        "session_id": session_id or f"test-{uuid.uuid4().hex[:8]}",
        "startup_id": "startup-1",
        "refined_pitch": "We help X do Y using Z.",
        "vulnerability_map": {
            "critical_vulnerabilities": [
                {"area": "Customer Acquisition", "severity": "HIGH", "reason": "CAC unvalidated"}
            ],
            "medium_vulnerabilities": [],
            "strengths": [],
        },
        "founder_concerns": ["Not sure about pricing"],
        "max_rounds": max_rounds,
    }


def test_start_session_returns_first_question():
    payload = sample_start_payload()
    resp = client.post("/investor/start", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == payload["session_id"]
    assert data["round"] == 1
    assert data["question"]
    assert data["status"] == "active"


def test_start_session_duplicate_id_conflicts():
    payload = sample_start_payload(session_id="dup-session")
    resp1 = client.post("/investor/start", json=payload)
    assert resp1.status_code == 200
    resp2 = client.post("/investor/start", json=payload)
    assert resp2.status_code == 409


def test_answer_advances_round_and_returns_analysis():
    payload = sample_start_payload(max_rounds=5)
    start_resp = client.post("/investor/start", json=payload)
    session_id = start_resp.json()["session_id"]

    answer_resp = client.post(
        "/investor/answer", json={"session_id": session_id, "answer": "We validated with 50 users."}
    )
    assert answer_resp.status_code == 200
    data = answer_resp.json()
    assert data["round"] == 2
    assert data["status"] == "active"
    assert data["answer_analysis"]["strength"] == 0.7
    assert data["question"]


def test_session_stops_at_max_rounds():
    payload = sample_start_payload(max_rounds=2)
    start_resp = client.post("/investor/start", json=payload)
    session_id = start_resp.json()["session_id"]

    # Round 1 -> answer -> should move to round 2
    r1 = client.post("/investor/answer", json={"session_id": session_id, "answer": "Answer 1"})
    assert r1.json()["status"] == "active"

    # Round 2 -> answer -> should complete (max_rounds=2)
    r2 = client.post("/investor/answer", json={"session_id": session_id, "answer": "Answer 2"})
    body = r2.json()
    assert body["status"] == "completed"
    assert body["stop_reason"] == "max_rounds_reached"
    assert body["question"] is None


def test_answer_on_missing_session_returns_404():
    resp = client.post(
        "/investor/answer", json={"session_id": "does-not-exist", "answer": "hello"}
    )
    assert resp.status_code == 404


def test_answer_on_completed_session_returns_400():
    payload = sample_start_payload(max_rounds=1)
    start_resp = client.post("/investor/start", json=payload)
    session_id = start_resp.json()["session_id"]

    r1 = client.post("/investor/answer", json={"session_id": session_id, "answer": "Answer 1"})
    assert r1.json()["status"] == "completed"

    r2 = client.post("/investor/answer", json={"session_id": session_id, "answer": "Answer 2"})
    assert r2.status_code == 400


def test_get_session_returns_state():
    payload = sample_start_payload()
    start_resp = client.post("/investor/start", json=payload)
    session_id = start_resp.json()["session_id"]

    resp = client.get(f"/investor/session/{session_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == session_id
    assert data["round"] == 1
    assert len(data["conversation_history"]) == 1


def test_get_session_not_found():
    resp = client.get("/investor/session/nonexistent")
    assert resp.status_code == 404


def test_end_session_returns_final_result():
    payload = sample_start_payload(max_rounds=5)
    start_resp = client.post("/investor/start", json=payload)
    session_id = start_resp.json()["session_id"]

    client.post("/investor/answer", json={"session_id": session_id, "answer": "Answer 1"})

    resp = client.post("/investor/end", json={"session_id": session_id})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert "founder_performance" in data
    assert "recommendation" in data
    assert data["recommendation"] in {"STRONG", "NEEDS_IMPROVEMENT", "WEAK"}


def test_end_session_not_found():
    resp = client.post("/investor/end", json={"session_id": "nope"})
    assert resp.status_code == 404


def test_answer_max_length_validation():
    payload = sample_start_payload()
    start_resp = client.post("/investor/start", json=payload)
    session_id = start_resp.json()["session_id"]

    too_long_answer = "x" * 9000  # exceeds pydantic AnswerRequest max_length=8000
    resp = client.post(
        "/investor/answer", json={"session_id": session_id, "answer": too_long_answer}
    )
    assert resp.status_code == 422
