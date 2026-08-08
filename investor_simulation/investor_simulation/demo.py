"""
PitchCraft AI- Module 7 Demo Script.

Runs the Investor Simulation end-to-end from the terminal, without needing a
frontend. Uses the in-process agents directly (no HTTP server required),
though the same logic backs the FastAPI endpoints in app/api/investor_routes.py.

Usage:
    python demo.py
"""

from __future__ import annotations

import json
import sys
import uuid

from app.agents.answer_analyzer import analyze_answer
from app.agents.investor_agent import compute_difficulty, generate_next_question
from app.models.schemas import (
    ConversationTurn,
    Role,
    SessionState,
    Vulnerability,
    VulnerabilityMap,
)

SAMPLE_REFINED_PITCH = """\
FreshCart AI is a grocery-list assistant that uses computer vision on a user's fridge \
photos to automatically generate a weekly shopping list, cross-references it with the \
cheapest nearby store prices, and lets users order directly through partnered grocery \
delivery apps. Early refinement added a "price watch" feature that resolved the initial \
concern about differentiation from generic list apps.
"""

SAMPLE_VULNERABILITIES = VulnerabilityMap(
    critical_vulnerabilities=[
        Vulnerability(
            area="Customer Acquisition",
            severity="HIGH",
            reason="CAC has not been validated; relies on paid social ads with no benchmark.",
        ),
        Vulnerability(
            area="Competition",
            severity="HIGH",
            reason="Instacart and existing grocery apps already offer list + price comparison features.",
        ),
    ],
    medium_vulnerabilities=[
        Vulnerability(
            area="Technical Feasibility",
            severity="MEDIUM",
            reason="Fridge-photo computer vision accuracy has not been benchmarked on real user data.",
        ),
    ],
    strengths=["Clear, relatable problem statement", "Working prototype for price comparison"],
)

SAMPLE_FOUNDER_CONCERNS = [
    "Not sure if our computer vision accuracy is good enough yet.",
    "Worried investors will compare us directly to Instacart.",
]


def print_header(text: str) -> None:
    print("\n" + "=" * 70)
    print(text)
    print("=" * 70)


def run_demo(num_rounds: int = 5, interactive: bool = True) -> None:
    session_id = f"demo-{uuid.uuid4().hex[:8]}"

    print_header("VentureX-Ray - Module 7: Investor Simulation Demo")
    print(f"Session ID: {session_id}")
    print("\nRefined Pitch:\n" + SAMPLE_REFINED_PITCH)

    state = SessionState(
        session_id=session_id,
        startup_id="startup-demo-001",
        refined_pitch=SAMPLE_REFINED_PITCH,
        vulnerability_map=SAMPLE_VULNERABILITIES,
        founder_concerns=SAMPLE_FOUNDER_CONCERNS,
        max_rounds=num_rounds,
    )

    for round_number in range(1, num_rounds + 1):
        state.difficulty = compute_difficulty(round_number, state.max_rounds)
        question = generate_next_question(state)
        state.round = round_number
        state.current_question = question.question

        print(f"\n--- Round {round_number}/{num_rounds} (difficulty {state.difficulty}) ---")
        print(f"INVESTOR: {question.question}")

        state.conversation_history.append(
            ConversationTurn(role=Role.investor, message=question.question, round=round_number)
        )
        if question.topic and question.topic not in state.topics_covered:
            state.topics_covered.append(question.topic)
        if question.targets_vulnerability:
            state.vulnerabilities_probed.append(question.targets_vulnerability)

        if interactive:
            try:
                answer = input("FOUNDER (you): ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n[Input closed - ending demo early.]")
                break
            if not answer:
                answer = "(no answer provided)"
        else:
            answer = "We believe demand is strong based on early user interviews."
            print(f"FOUNDER (auto): {answer}")

        state.conversation_history.append(
            ConversationTurn(role=Role.founder, message=answer, round=round_number)
        )

        analysis = analyze_answer(
            refined_pitch=state.refined_pitch,
            current_question=question.question,
            founder_answer=answer,
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
            state.evidence_found.append(answer[:200])

        print(
            "  [analysis] strength={:.2f} evidence={} follow_up_required={}".format(
                analysis.strength, analysis.evidence, analysis.follow_up_required
            )
        )
        if analysis.unsupported_claims:
            print(f"  [analysis] unsupported_claims: {analysis.unsupported_claims}")

    print_header("Final Investor Assessment")
    result = {
        "session_id": state.session_id,
        "total_rounds": state.round,
        "weak_areas": list(dict.fromkeys(state.weak_areas)),
        "unsupported_claims": list(dict.fromkeys(state.unsupported_claims)),
        "topics_covered": state.topics_covered,
        "last_answer_strength": (
            state.last_answer_analysis.strength if state.last_answer_analysis else None
        ),
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    interactive = "--auto" not in sys.argv
    run_demo(num_rounds=5, interactive=interactive)
