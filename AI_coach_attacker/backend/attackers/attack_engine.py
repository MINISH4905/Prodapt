from backend.attackers import market_attacker, business_attacker, technology_attacker
from backend.models.schemas import (
    AttackResponse,
    Vulnerability,
    VulnerabilityMap,
    VulnerabilityMapEntry,
)


def _build_vulnerability_map(
    market: list[Vulnerability],
    business: list[Vulnerability],
    technology: list[Vulnerability],
) -> VulnerabilityMap:
    critical: list[VulnerabilityMapEntry] = []
    high: list[VulnerabilityMapEntry] = []
    medium: list[VulnerabilityMapEntry] = []
    low: list[VulnerabilityMapEntry] = []

    for attacker, vulns in [
        ("market", market),
        ("business", business),
        ("technology", technology),
    ]:
        for vuln in vulns:
            entry = VulnerabilityMapEntry(
                attacker=attacker,
                title=vuln.title,
                severity=vuln.severity,
                category=vuln.category,
                reason=vuln.reason,
                attack_question=vuln.attack_question,
                suggested_area_to_fix=vuln.suggested_area_to_fix,
            )
            bucket = {
                "CRITICAL": critical,
                "HIGH": high,
                "MEDIUM": medium,
                "LOW": low,
            }[vuln.severity]
            bucket.append(entry)

    return VulnerabilityMap(
        critical=critical,
        high=high,
        medium=medium,
        low=low,
    )


def run_attack(idea: str) -> AttackResponse:
    market_result = market_attacker.attack(idea)
    business_result = business_attacker.attack(idea)
    technology_result = technology_attacker.attack(idea)

    vulnerability_map = _build_vulnerability_map(
        market_result, business_result, technology_result
    )

    return AttackResponse(
        idea=idea,
        attackers={
            "market": market_result,
            "business": business_result,
            "technology": technology_result,
        },
        vulnerability_map=vulnerability_map,
    )
