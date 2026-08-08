"""
VentureX-Ray Defense Module - AI LLM Agents & Engine (agents.py)
----------------------------------------------------------------
This module implements the core AI intelligence engine for the Defense & Refinement phase
of VentureX-Ray (Modules 4, 5, and 6).

Key Components:
1. `get_model()`: Factory function that initializes the Google Gemini LLM API client (`gemini-1.5-flash`)
   or enables deterministic Mock Fallback Mode if credentials are missing or invalid.
2. `clean_and_parse_json()`: Utility to extract and parse raw JSON payloads from LLM markdown responses.
3. `RefinementAgent` (Module 4): Constructive AI agent that takes original startup pitches and vulnerability maps,
   producing refined strategic pillars (Problem, Solution, Customer, Business Model, Tech) and explicit change logs.
4. `ConcernQuestionGenerator` (Module 5): Probing agent that combines refined models, original vulnerabilities,
   and founder feedback to construct 3 non-generic, challenging clarity questions.
5. `ClarityEvaluator` (Module 6): Analytical evaluator that grades founder answers across three dimensions
   (Specificity, Logical Consistency, Operational Groundedness) and identifies weak areas with remedies.
"""

import os
import json
import logging
import google.generativeai as genai
from typing import List
from .schemas import (
    StartupProfile, 
    VulnerabilityMap, 
    RefinedStartup, 
    RefinementChange, 
    ClarityQuestion, 
    ClarityEvaluation, 
    FounderResponse, 
    WeakArea
)

# Logger instance configured to output via uvicorn standard error
logger = logging.getLogger("uvicorn.error")

# ==========================================
# GEMINI LLM INITIALIZATION & MOCK ENGINE HELPERS
# ==========================================

def get_model(api_key: str = None) -> tuple:
    """
    Initializes and returns the Gemini GenerativeModel instance alongside a mock mode boolean flag.
    
    Logic Flow:
    1. Resolves API key from parameter or environment variable `GEMINI_API_KEY`.
    2. If key is missing or configuration fails, logs a warning and returns (None, True) to trigger Mock Mode.
    3. If valid, configures `google.generativeai` with `gemini-1.5-flash` and returns (model, False).
    """
    key = api_key or os.getenv("GEMINI_API_KEY")
    if not key:
        logger.warning("VentureX-Ray: Gemini API Key is missing. Entering Mock Fallback Mode for demonstration.")
        return None, True
    
    try:
        genai.configure(api_key=key)
        return genai.GenerativeModel("gemini-1.5-flash"), False
    except Exception as e:
        logger.error(f"VentureX-Ray: Failed to initialize Gemini API: {str(e)}. Entering Mock Fallback Mode.")
        return None, True

def clean_and_parse_json(text: str) -> dict:
    """
    Safely sanitizes raw text returned by LLMs by stripping markdown code block fences (e.g. ```json ... ```)
    and parsing the sanitized string into a Python dictionary or list.
    """
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    return json.loads(text)

# ==========================================
# MODULE 4: REFINEMENT AGENT IMPLEMENTATION
# ==========================================

class RefinementAgent:
    """
    Constructive Refinement Agent (Module 4).
    Analytically evolves the original startup pitch to mitigate vulnerabilities identified in Modules 1-3
    while strictly preserving the startup's core identity and value proposition.
    """
    
    @staticmethod
    def refine_startup(profile: StartupProfile, vmap: VulnerabilityMap, api_key: str = None) -> RefinedStartup:
        """
        Executes startup idea refinement. Uses Gemini LLM if configured; otherwise uses deterministic mock fallback.
        """
        model, is_mock = get_model(api_key)
        
        # Trigger Mock Mode if API key is absent or invalid
        if is_mock:
            return RefinementAgent._get_mock_refinement(profile)
            
        # Format vulnerabilities into structured prompt text
        vulns_text = ""
        for i, f in enumerate(vmap.findings):
            vulns_text += f"{i+1}. [{f.category} - Severity: {f.severity}]\n"
            vulns_text += f"   Reasoning: {f.reasoning}\n"
            vulns_text += f"   Investor Question: {f.attack_question}\n"
            vulns_text += f"   Suggested Mitigation: {f.suggested_mitigation}\n\n"
            
        # Prompt Strategy: Instruct Gemini to modify fields realistically, keep startup name identical,
        # and enforce strict JSON schema output matching RefinedStartup.
        prompt = f"""You are the Constructive Refinement Agent for VentureX-Ray. Your job is to improve the original startup concept based on the vulnerability map while preserving the core value proposition.

DO NOT change the name of the startup. Make realistic and structured improvements to the solution, target customer, business model, and technology sections to mitigate the listed vulnerabilities.

Original Startup Profile:
- Name: {profile.name}
- Problem: {profile.problem}
- Solution: {profile.solution}
- Target Customer: {profile.target_customer}
- Business Model: {profile.business_model}
- Technology: {profile.technology}

Vulnerabilities & Risk Map:
{vulns_text}

Instructions:
1. Provide refined descriptions for 'problem', 'solution', 'target_customer', 'business_model', and 'technology'. Keep the improvements realistic—do not invent magical tech or completely change the startup's core premise.
2. Under 'changes', document the specific edits made. Each edit must specify the field name (problem, solution, target_customer, business_model, or technology), the original text ('before'), the new text ('after'), and a detailed 'explanation' of which vulnerability is addressed and why.
3. Write a high-level summary of your refinement strategy under 'change_rationale'.

Output your response STRICTLY as a single JSON object. Do not include any chat prefix or markdown formatting outside the JSON code block. The JSON must exactly match this structure:
{{
  "name": "{profile.name}",
  "problem": "Refined problem description...",
  "solution": "Refined solution description...",
  "target_customer": "Refined target customer description...",
  "business_model": "Refined business model description...",
  "technology": "Refined technology description...",
  "changes": [
    {{
      "field": "solution",
      "before": "Original solution...",
      "after": "Refined solution...",
      "explanation": "Addressed moisture sensitivity vulnerability by..."
    }}
  ],
  "change_rationale": "High-level summary of refinement strategy..."
}}
"""
        # Execute LLM call enforcing JSON response MIME type
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        
        parsed = clean_and_parse_json(response.text)
        changes = [RefinementChange(**c) for c in parsed.get("changes", [])]
        return RefinedStartup(
            name=parsed.get("name", profile.name),
            problem=parsed.get("problem", profile.problem),
            solution=parsed.get("solution", profile.solution),
            target_customer=parsed.get("target_customer", profile.target_customer),
            business_model=parsed.get("business_model", profile.business_model),
            technology=parsed.get("technology", profile.technology),
            changes=changes,
            change_rationale=parsed.get("change_rationale", "")
        )

    @staticmethod
    def _get_mock_refinement(profile: StartupProfile) -> RefinedStartup:
        """
        Deterministic Mock Fallback Engine for Refinement Agent (Module 4).
        Returns realistic, highly structured refinements for template startups (EcoPacker, MedRoute AI, OrbitLink).
        """
        name_lower = profile.name.lower()
        if "ecopacker" in name_lower:
            return RefinedStartup(
                name=profile.name,
                problem=profile.problem,
                solution="We manufacture highly durable, water-resistant, biodegradable packaging made from crop waste (corn husks and sugarcane bagasse). We apply a proprietary binder process matching plastic durability, layered with a patent-pending hydrophobic plant-wax coating that prevents packaging dissolution in high-humidity climates.",
                target_customer="Initially targeting premium boutique eco-conscious brands (margins above 50%) to absorb early scale costs, with a standardized 'Starter Pack' online interface for SMBs to generate immediate cash flow.",
                business_model="B2B contract recurring sales and custom setup design fees. Standardized starter packs are sold via card payment to guarantee quick cash runway during enterprise procurement.",
                technology="Proprietary organic binding formula with automated thermoforming machinery and a bio-wax heat-seal coating. We release audited humidity and tensile degradation test logs to verify stability.",
                changes=[
                    RefinementChange(
                        field="solution",
                        before=profile.solution,
                        after="We manufacture highly durable, water-resistant, biodegradable packaging... layered with a patent-pending hydrophobic plant-wax coating...",
                        explanation="Mitigates structural moisture vulnerability in humid environments by introducing a protective hydrophobic plant wax barrier."
                    ),
                    RefinementChange(
                        field="target_customer",
                        before=profile.target_customer,
                        after="Initially targeting premium boutique eco-conscious brands... with a standardized 'Starter Pack' online interface for SMBs...",
                        explanation="Mitigates high entry price sensitivity by starting with high-margin premium brands, and resolves long sales cycle runway risk by introducing standard SMB packs."
                    ),
                    RefinementChange(
                        field="business_model",
                        before=profile.business_model,
                        after="B2B contract recurring sales... Standardized starter packs are sold via card payment to guarantee quick cash runway...",
                        explanation="Protects runway cash flow from 9-12 month enterprise sales cycles by generating instant transactional cash from SMBs."
                    )
                ],
                change_rationale="Focused on protecting early cash flow through SMB transactions while validating long-term material stability with bio-wax coatings and third-party laboratory reports."
            )
        elif "medroute" in name_lower:
            return RefinedStartup(
                name=profile.name,
                problem=profile.problem,
                solution="An AI-powered clinical decision support routing engine. It processes symptoms via a restricted clinical NLP transformer, suggesting triage tiers that require mandatory clinical sign-offs from triage nurses, shielding hospital liability.",
                target_customer="Mid-sized urgent care networks and regional hospital systems looking to reduce nurse cognitive load and divert low-severity emergency traffic.",
                business_model="SaaS subscription license billed monthly based on emergency department patient slots, paired with an integrated pilot dashboard offering clear financial ROI tracking.",
                technology="Proprietary clinical NLP transformer models fine-tuned on clinical cases. Operates as an HL7/FHIR integration layer sitting alongside EHRs (Epic/Cerner) as a specialized routing orchestrator rather than a standalone platform.",
                changes=[
                    RefinementChange(
                        field="solution",
                        before=profile.solution,
                        after="An AI-powered clinical decision support routing engine... suggesting triage tiers that require mandatory clinical sign-offs...",
                        explanation="Resolves severe clinical malpractice legal liability by positioning the AI as a clinical support tool with a nurse sign-off safeguard."
                    ),
                    RefinementChange(
                        field="technology",
                        before=profile.technology,
                        after="Proprietary clinical NLP transformer... Operates as an HL7/FHIR integration layer sitting alongside EHRs...",
                        explanation="Mitigates platform-displacement risks from Epic/Cerner by acting as a lightweight cross-network middleware layer rather than competing directly as a portal."
                    )
                ],
                change_rationale="Refined to position the software as a supportive integration middleware tool with built-in medical clinical sign-off safeguards to eliminate liability risks."
            )
        else:
            # Default mock for OrbitLink or custom startups
            return RefinedStartup(
                name=profile.name,
                problem=profile.problem,
                solution="Ultra-low power, pocket-sized IoT sensors utilizing a self-healing LoRa mesh protocol with automatic path redirection. Units ship pre-configured as solar-powered 'plug-and-play' boxes to eliminate manual setup overhead.",
                target_customer="Industrial pipeline networks and remote agricultural distributors willing to install pre-configured telemetry node gateways.",
                business_model="Low-margin hardware gateway sales priced at cost, coupled with high-margin data subscriptions. Satellite bandwidth is aggregated via custom wholesale routing contracts.",
                technology="Custom ultra-narrowband radio transceivers, low-power LoRa mesh with failover pathing, and waterproof IP68-rated weatherproof enclosures.",
                changes=[
                    RefinementChange(
                        field="solution",
                        before=profile.solution,
                        after="Ultra-low power, pocket-sized IoT sensors... Units ship pre-configured as solar-powered 'plug-and-play' boxes...",
                        explanation="Mitigates high setup friction and slow customer adoption by using zero-configuration solar hardware."
                    ),
                    RefinementChange(
                        field="technology",
                        before=profile.technology,
                        after="Custom transceivers... with failover pathing, and waterproof IP68-rated weatherproof enclosures.",
                        explanation="Addresses outdoor weather durability concerns and mesh node failure risks via self-healing network routing."
                    )
                ],
                change_rationale="Refinement concentrates on zero-configuration hardware setups for non-technical users and self-healing radio mesh failovers for remote operations."
            )

# ==========================================
# MODULE 5: CONCERN QUESTION GENERATOR IMPLEMENTATION
# ==========================================

class ConcernQuestionGenerator:
    """
    Founder Concern & Question Generator (Module 5).
    Evaluates founder inputs/concerns against the refined model and original risk findings to synthesize
    3 deep, probing clarity questions to test founder alignment and comprehension.
    """
    
    @staticmethod
    def generate_questions(refined: RefinedStartup, vmap: VulnerabilityMap, concerns: str, api_key: str = None) -> List[ClarityQuestion]:
        """
        Generates 3 customized clarity questions via Gemini LLM or mock fallback.
        """
        model, is_mock = get_model(api_key)
        
        if is_mock:
            return ConcernQuestionGenerator._get_mock_questions(refined, concerns)
            
        vulns_text = "\n".join([
            f"- [{f.category}] {f.reasoning} (Investor Question: {f.attack_question})"
            for f in vmap.findings
        ])
        
        # Prompt Strategy: Direct Gemini to synthesize specific, challenging questions
        # connecting founder concerns with vulnerability mitigations.
        prompt = f"""You are the Clarity Agent for VentureX-Ray.
The startup idea has been refined to address some critical vulnerabilities, and the founder has reviewed the refinement.
The founder has raised the following concerns, doubts, or areas of disagreement:
\"\"\"{concerns}\"\"\"

Refined Startup Concept:
- Name: {refined.name}
- Problem: {refined.problem}
- Solution: {refined.solution}
- Target Customer: {refined.target_customer}
- Business Model: {refined.business_model}
- Technology: {refined.technology}

Original Vulnerability Context:
{vulns_text}

Instructions:
Generate exactly 3 highly targeted, challenging questions for the founder. These questions must test whether the founder actually understands the refined concept, agrees with it, and can logically defend the business decisions made in the refinement.
- Do NOT ask generic questions (e.g. 'How will you make money?'). Make them specific to this startup's details.
- At least one question should address the founder's stated concerns directly.
- The other questions should probe if the founder is aligned with how the vulnerabilities were mitigated.

Output your response STRICTLY as a JSON array of objects. The JSON must exactly match this structure:
[
  {{
    "id": "q1",
    "question": "Targeted question text here...",
    "context": "Explanation of why this question is being asked (e.g. linked to founder's concern about manufacturing costs)"
  }},
  {{
    "id": "q2",
    "question": "Targeted question text here...",
    "context": "Context linking this to a specific technology vulnerability mitigation..."
  }},
  {{
    "id": "q3",
    "question": "Targeted question text here...",
    "context": "Context probing alignment on target customer changes..."
  }}
]
"""
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        
        parsed = clean_and_parse_json(response.text)
        return [ClarityQuestion(**q) for q in parsed]

    @staticmethod
    def _get_mock_questions(refined: RefinedStartup, concerns: str) -> List[ClarityQuestion]:
        """
        Deterministic Mock Fallback Engine for Question Generator (Module 5).
        Returns domain-tailored clarity questions based on startup key.
        """
        name_lower = refined.name.lower()
        if "ecopacker" in name_lower:
            return [
                ClarityQuestion(
                    id="q1",
                    question="Since you stated concerns about the cost of the hydrophobic coating, how will you price the SMB starter packs to remain competitive while absorbing this cost?",
                    context="Prompted by your concern regarding chemical coating costs."
                ),
                ClarityQuestion(
                    id="q2",
                    question="How will you ensure raw crop waste logistics stay stable during winter when agricultural processing facilities reduce operations?",
                    context="Probes raw material supply chain vulnerabilities."
                ),
                ClarityQuestion(
                    id="q3",
                    question="What specific conversion metrics or triggers will you use to graduate SMB starter-pack clients into high-volume recurring enterprise contracts?",
                    context="Tests alignment on the dual SMB/enterprise sales model."
                )
            ]
        elif "medroute" in name_lower:
            return [
                ClarityQuestion(
                    id="q1",
                    question="If triage nurses are mandatory sign-offs, how will you prevent MedRoute AI from becoming a bottleneck during peak ED surge hours?",
                    context="Linked to your concerns about nurse workflow impact and clinician burnout."
                ),
                ClarityQuestion(
                    id="q2",
                    question="Epic and Cerner have extensive sandbox programs. What prevents them from altering API access limits if your middleware routes too much traffic?",
                    context="Tests technology platform-dependence risks."
                ),
                ClarityQuestion(
                    id="q3",
                    question="What specific ROI metric will your pilot dashboard track to prove to hospital boards that clinical sign-off is reducing total wait times?",
                    context="Addresses the business value validation model."
                )
            ]
        else:
            return [
                ClarityQuestion(
                    id="q1",
                    question="If hardware gateways are priced at cost, how long does a customer subscription need to run before you break even on satellite bandwidth charges?",
                    context="Triggered by concerns on unit economic margins."
                ),
                ClarityQuestion(
                    id="q2",
                    question="If a remote agricultural LoRa gateway loses power, what local storage failover does a sensor node have to prevent data loss?",
                    context="Addresses physical reliability and mesh vulnerabilities."
                ),
                ClarityQuestion(
                    id="q3",
                    question="How do you plan to handle gateway replacement logistics for non-technical users in extremely remote farming zones?",
                    context="Tests customer support scalability assumptions."
                )
            ]

# ==========================================
# MODULE 6: CLARITY EVALUATOR IMPLEMENTATION
# ==========================================

class ClarityEvaluator:
    """
    Founder Clarity Evaluator (Module 6).
    Evaluates founder answers to clarity questions across specificity, consistency, and groundedness metrics,
    computing composite scores and highlighting actionable remedies for weak areas.
    """
    
    @staticmethod
    def evaluate_responses(refined: RefinedStartup, responses: List[FounderResponse], api_key: str = None) -> ClarityEvaluation:
        """
        Evaluates founder defensive responses via Gemini LLM or dynamic mock fallback.
        """
        model, is_mock = get_model(api_key)
        
        if is_mock:
            return ClarityEvaluator._get_mock_evaluation(refined, responses)
            
        answers_text = ""
        for r in responses:
            answers_text += f"Question ID: {r.question_id}\n"
            answers_text += f"Question: {r.question_text}\n"
            answers_text += f"Founder Answer: {r.answer}\n\n"
            
        # Prompt Strategy: Direct Gemini to compute 0-100 scores across Specificity,
        # Logical Consistency, and Operational Groundedness, and output detailed weak area remedies.
        prompt = f"""You are the Clarity Evaluator for VentureX-Ray.
Analyze the founder's responses to the clarity questions. Your job is to measure whether the founder can actually understand and defend the refined startup.
Evaluate whether the responses are specific (not vague), logically consistent with the refined startup's assumptions, and grounded in realistic business operations.

Refined Startup Concept:
- Name: {refined.name}
- Problem: {refined.problem}
- Solution: {refined.solution}
- Target Customer: {refined.target_customer}
- Business Model: {refined.business_model}
- Technology: {refined.technology}

Questions and Founder Answers:
{answers_text}

Instructions:
1. Grade the founder's answers in three dimensions (0 to 100):
   - specificity_score: Are the answers detailed and concrete, or vague/evasive?
   - consistency_score: Are the answers logically consistent with the refined startup model?
   - grounded_score: Are the answers realistic, or do they rely on magical thinking / unsupported claims?
2. Calculate the overall clarity_score (0-100) as a synthesised score of their readiness.
3. Identify 1 to 3 'weak_areas' (if any) where the founder failed to explain the concept clearly. For each weak area, provide:
   - category: 'Market', 'Business', or 'Technology'
   - weakness: Short summary of the weak point
   - details: Detailed analysis of what was lacking in their answer
   - remedy: Actionable advice on what they should learn, adjust, or change to defend it successfully
4. Provide a qualitative 'detailed_analysis' summarizing the overall outcome.

Output your response STRICTLY as a single JSON object. The JSON must exactly match this structure:
{{
  "clarity_score": 85,
  "specificity_score": 80,
  "consistency_score": 90,
  "grounded_score": 85,
  "weak_areas": [
    {{
      "category": "Market",
      "weakness": "Vague Customer Acquisition Plan",
      "details": "When asked how they would overcome commodity pricing, the founder simply said 'we will market better' without defining specific channels or partnerships.",
      "remedy": "Develop a detailed customer acquisition cost (CAC) plan targeting high-end eco-boutiques first."
    }}
  ],
  "detailed_analysis": "Comprehensive qualitative summary of the evaluation..."
}}
"""
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        
        parsed = clean_and_parse_json(response.text)
        weak_areas = [WeakArea(**wa) for wa in parsed.get("weak_areas", [])]
        return ClarityEvaluation(
            clarity_score=parsed.get("clarity_score", 0),
            specificity_score=parsed.get("specificity_score", 0),
            consistency_score=parsed.get("consistency_score", 0),
            grounded_score=parsed.get("grounded_score", 0),
            weak_areas=weak_areas,
            detailed_analysis=parsed.get("detailed_analysis", "")
        )

    @staticmethod
    def _get_mock_evaluation(refined: RefinedStartup, responses: List[FounderResponse]) -> ClarityEvaluation:
        """
        Dynamic Mock Fallback Engine for Clarity Evaluator (Module 6).
        Calculates dynamic scores proportional to founder response thoroughness and maps tailored weak areas.
        """
        # Calculate score metrics based on response character depth
        avg_len = sum(len(r.answer) for r in responses) / len(responses) if responses else 0
        
        specificity = min(95, max(45, int(40 + (avg_len / 4))))
        consistency = min(92, max(50, int(50 + (avg_len / 5))))
        grounded = min(90, max(40, int(45 + (avg_len / 6))))
        overall = int((specificity * 0.4) + (consistency * 0.3) + (grounded * 0.3))
        
        name_lower = refined.name.lower()
        if "ecopacker" in name_lower:
            weak_areas = [
                WeakArea(
                    category="Business",
                    weakness="SMB Conversion Metrics Lack Detail",
                    details="The answers show a plan to offer starter packs but fail to define key triggers or customer satisfaction loops needed to move users into enterprise supply contracts.",
                    remedy="Incorporate a dedicated feedback survey inside the starter pack delivery to qualify customers for subscription terms."
                )
            ]
            detailed_analysis = "The founder shows good understanding of raw material procurement logistics. However, translating transient SMB starter-pack sales into high-value contract lines needs a more concrete marketing plan."
        elif "medroute" in name_lower:
            weak_areas = [
                WeakArea(
                    category="Technology",
                    weakness="API Access Dependency Risk",
                    details="The response on Epic/Cerner API sandboxes relies heavily on developer agreements, overlooking platform-displacement strategies of major EHR systems.",
                    remedy="Design the middleware database to support local FHIR server caching to operate during network interruptions."
                )
            ]
            detailed_analysis = "Emergency department workflow integration is well understood, particularly human-in-the-loop sign-offs. Resolving dependence on EHR platform updates is the main remaining hurdle."
        else:
            weak_areas = [
                WeakArea(
                    category="Business",
                    weakness="Gateway Subsidy Break-Even Length",
                    details="Selling gateways at cost poses a working capital cash threat. The founder's response did not model subscription margins against satellite bandwidth fees.",
                    remedy="Run a cohort margin analysis and consider raising the hardware cost slightly above BOM costs."
                )
            ]
            detailed_analysis = "Mesh connectivity architecture is well defended. The business model, particularly regarding gateway hardware subsidies, requires further economic modeling."
            
        return ClarityEvaluation(
            clarity_score=overall,
            specificity_score=specificity,
            consistency_score=consistency,
            grounded_score=grounded,
            weak_areas=weak_areas,
            detailed_analysis=detailed_analysis
        )

