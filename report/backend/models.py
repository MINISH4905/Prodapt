from pydantic import BaseModel
from typing import Any, Dict, List


class ReportRequest(BaseModel):
    startup: Dict[str, Any]
    refined_idea: Dict[str, Any]
    attacker_results: List[Dict[str, Any]]
    vulnerabilities: List[Dict[str, Any]]
    defense_score: float
    investor_conversation: List[Dict[str, Any]]
    decision: str