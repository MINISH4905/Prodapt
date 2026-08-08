import json
import os

from backend.attackers.llm_client import get_client, get_model
from backend.models.schemas import Vulnerability

SYSTEM_PROMPT = """You are a Skeptical CTO / Technical Architect for VentureX-Ray.

Your ONLY job is to ATTACK a startup idea. Do NOT improve it, solve problems, or rewrite the idea.

MAIN QUESTION: "Can this actually be built, scaled, secured, operated reliably and defended?"

Analyze ONLY these dimensions:
1. Technical feasibility
2. Technology dependency
3. AI dependency
4. Scalability
5. Security
6. Reliability
7. Product feasibility
8. Technical moat

Look for:
- unrealistic technical assumptions
- excessive AI dependency
- external API dependency
- scalability problems
- security concerns
- privacy concerns
- reliability problems
- difficult implementation
- easy-to-copy technology

RULES:
- Be adversarial and specific. Avoid generic statements.
- Do NOT invent statistics, technical benchmarks, or vendor names unless logically implied.
- If information is missing, say "Evidence not provided." or "Assumption is unsupported."
- Return exactly 3 to 5 vulnerabilities. Prioritize quality over quantity.

Return ONLY valid JSON with this exact structure:
{
    "vulnerabilities": [
        {
            "title": "<vulnerability title>",
            "severity": "<LOW|MEDIUM|HIGH|CRITICAL>",
            "category": "<one of: feasibility|technology|ai_dependency|scalability|security|reliability|product|technical_moat>",
            "reason": "<specific reason this is a vulnerability>",
            "attack_question": "<tough question exposing the weakness>",
            "suggested_area_to_fix": "<area that needs attention>"
        }
    ]
}"""


def _get_demo_vulnerabilities() -> list[dict]:
    return [
        {
            "title": "Excessive AI dependency",
            "severity": "MEDIUM",
            "category": "ai_dependency",
            "reason": "The core value proposition relies on AI matching quality, but no validation approach for AI output accuracy is described.",
            "attack_question": "How will you validate and monitor AI-generated recommendations?",
            "suggested_area_to_fix": "AI validation and monitoring",
        },
        {
            "title": "No technical moat",
            "severity": "MEDIUM",
            "category": "technical_moat",
            "reason": "An AI-powered matching platform using standard LLM APIs can be replicated by competitors with similar infrastructure.",
            "attack_question": "What prevents a well-funded competitor from building the same product in weeks?",
            "suggested_area_to_fix": "Technical differentiation",
        },
        {
            "title": "Data privacy concerns",
            "severity": "HIGH",
            "category": "security",
            "reason": "Student profiles and application data require careful handling, but no privacy or security architecture is described.",
            "attack_question": "How will you protect sensitive student data and comply with privacy regulations?",
            "suggested_area_to_fix": "Security and privacy architecture",
        },
    ]


def attack(idea: str) -> list[Vulnerability]:
    demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"

    if demo_mode:
        return [Vulnerability(**v) for v in _get_demo_vulnerabilities()]

    client = get_client()

    response = client.chat.completions.create(
        model=get_model(),
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Attack this startup idea:\n\n{idea}"},
        ],
        response_format={"type": "json_object"},
        temperature=0.7,
    )

    raw = response.choices[0].message.content
    data = json.loads(raw)

    return [Vulnerability(**v) for v in data["vulnerabilities"]]
