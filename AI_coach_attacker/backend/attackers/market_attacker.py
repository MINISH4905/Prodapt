import json
import os

from backend.attackers.llm_client import get_client, get_model
from backend.models.schemas import Vulnerability

SYSTEM_PROMPT = """You are a Hostile Market Analyst / Skeptical Investor for VentureX-Ray.

Your ONLY job is to ATTACK a startup idea. Do NOT improve it, solve problems, or rewrite the idea.

MAIN QUESTION: "Is there actually a market for this, and why would customers choose this startup?"

Analyze ONLY these dimensions:
1. Customer
2. Demand
3. Competition
4. Differentiation
5. Customer acquisition

Look for:
- unclear target customer
- weak customer pain
- weak demand
- existing competitors (only mention if logically implied by the idea — do NOT invent specific competitors or statistics)
- substitute solutions
- weak differentiation
- easy-to-copy value proposition
- unrealistic customer acquisition assumptions
- unclear first customers

RULES:
- Be adversarial and specific. Avoid generic statements like "The market could be competitive."
- Do NOT invent statistics, market data, or named competitors.
- If information is missing, say "Evidence not provided." or "Assumption is unsupported."
- Return exactly 3 to 5 vulnerabilities. Prioritize quality over quantity.

Return ONLY valid JSON with this exact structure:
{
    "vulnerabilities": [
        {
            "title": "<vulnerability title>",
            "severity": "<LOW|MEDIUM|HIGH|CRITICAL>",
            "category": "<one of: customer|demand|competition|differentiation|acquisition>",
            "reason": "<specific reason this is a vulnerability>",
            "attack_question": "<tough question exposing the weakness>",
            "suggested_area_to_fix": "<area that needs attention>"
        }
    ]
}"""


def _get_demo_vulnerabilities() -> list[dict]:
    return [
        {
            "title": "Weak differentiation",
            "severity": "HIGH",
            "category": "competition",
            "reason": "Existing internship platforms already provide the core discovery functionality, while the proposed AI capability does not yet establish a compelling switching reason.",
            "attack_question": "Why would students switch from existing platforms?",
            "suggested_area_to_fix": "Competitive differentiation",
        },
        {
            "title": "Unclear target customer",
            "severity": "MEDIUM",
            "category": "customer",
            "reason": "The idea references college students broadly without defining which segment has the strongest pain or willingness to adopt a new platform.",
            "attack_question": "Which specific student segment is your first customer, and why?",
            "suggested_area_to_fix": "Customer segmentation",
        },
        {
            "title": "Unsupported demand evidence",
            "severity": "HIGH",
            "category": "demand",
            "reason": "Evidence not provided that students actively seek a new solution beyond what existing platforms already offer.",
            "attack_question": "What evidence shows unmet demand that current platforms fail to address?",
            "suggested_area_to_fix": "Demand validation",
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
