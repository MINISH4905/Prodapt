from pydantic import BaseModel, Field
from typing import Literal


Severity = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
AttackerType = Literal["market", "business", "technology"]


class Vulnerability(BaseModel):
    title: str
    severity: Severity
    category: str
    reason: str
    attack_question: str
    suggested_area_to_fix: str


class VulnerabilityMapEntry(Vulnerability):
    attacker: AttackerType


class VulnerabilityMap(BaseModel):
    critical: list[VulnerabilityMapEntry]
    high: list[VulnerabilityMapEntry]
    medium: list[VulnerabilityMapEntry]
    low: list[VulnerabilityMapEntry]


class AttackRequest(BaseModel):
    idea: str


class AttackResponse(BaseModel):
    idea: str
    attackers: dict[str, list[Vulnerability]]
    vulnerability_map: VulnerabilityMap
