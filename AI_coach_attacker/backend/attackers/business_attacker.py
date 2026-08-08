import json
import os

from backend.attackers.llm_client import get_client, get_model
from backend.models.schemas import Vulnerability

SYSTEM_PROMPT = """You are a Hostile Business Analyst / Investor Skeptic for VentureX-Ray.

Your ONLY job is to ATTACK a startup idea. Do NOT improve it, solve problems, or rewrite the idea.

MAIN QUESTION: "Even if customers want this, how does the company actually make money and survive?"

Analyze ONLY these dimensions:
1. Revenue
2. Pricing
3. Costs
4. CAC (Customer Acquisition Cost)
5. Retention
6. Unit economics
7. Scalability

Look for:
- unclear monetization
- unrealistic pricing
- high costs
- unknown CAC
- weak retention
- poor unit economics
- unrealistic margins
- non-scalable operations

RULES:
- Be adversarial and specific. Avoid generic statements.
- Do NOT invent statistics, financial data, or market benchmarks.
- If information is missing, say "Evidence not provided." or "Assumption is unsupported."
- Return exactly 3 to 5 vulnerabilities. Prioritize quality over quantity.

Return ONLY valid JSON with this exact structure:
{
    "vulnerabilities": [
        {
            "title": "<vulnerability title>",
            "severity": "<LOW|MEDIUM|HIGH|CRITICAL>",
            "category": "<one of: revenue|pricing|costs|cac|retention|unit_economics|scalability>",
            "reason": "<specific reason this is a vulnerability>",
            "attack_question": "<tough question exposing the weakness>",
            "suggested_area_to_fix": "<area that needs attention>"
        }
    ]
}"""


def _get_demo_vulnerabilities() -> list[dict]:
    return [
        {
            "title": "Unclear customer economics",
            "severity": "HIGH",
            "category": "unit_economics",
            "reason": "The startup does not establish whether customer revenue can cover acquisition and AI infrastructure costs.",
            "attack_question": "How much will it cost to acquire one paying customer, and how does that compare with customer lifetime value?",
            "suggested_area_to_fix": "Unit economics",
        },
        {
            "title": "Unspecified monetization",
            "severity": "HIGH",
            "category": "revenue",
            "reason": "Evidence not provided on how the platform generates revenue — subscriptions, employer fees, or advertising are all possible but none are defined.",
            "attack_question": "What is your primary revenue stream and why will customers or partners pay?",
            "suggested_area_to_fix": "Revenue model",
        },
        {
            "title": "Retention assumptions unsupported",
            "severity": "MEDIUM",
            "category": "retention",
            "reason": "Assumption is unsupported that students will remain active users after securing an internship, limiting recurring revenue potential.",
            "attack_question": "What keeps users engaged after they achieve their primary goal?",
            "suggested_area_to_fix": "Retention strategy",
        },
        {
            "title": "Scalability of operations unclear",
            "severity": "MEDIUM",
            "category": "scalability",
            "reason": "If the platform relies on personalized AI matching, per-user AI costs may grow linearly without economies of scale.",
            "attack_question": "How do margins improve as user volume increases?",
            "suggested_area_to_fix": "Operational scalability",
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
