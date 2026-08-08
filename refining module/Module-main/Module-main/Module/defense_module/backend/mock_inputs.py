"""
VentureX-Ray Defense Module - Preconfigured Mock Inputs (mock_inputs.py)
-------------------------------------------------------------------------
This module provides preconfigured mock datasets representing the outputs of Modules 1, 2, and 3
(Startup Input, Attacker Agent Analysis, and Vulnerability Risk Mapping).

Purpose:
Serves as the baseline demonstration dataset for the Defense Engine (Modules 4, 5, and 6),
enabling immediate testing and evaluation of startup refinement, concern handling, and clarity scoring
without requiring live upstream Attacker Agent runs.

Preconfigured Startups:
1. EcoPacker: Sustainable B2B packaging startup facing commodity pricing and moisture vulnerabilities.
2. MedRoute AI: Emergency triage NLP engine facing clinical legal liability and EHR vendor platform risk.
3. OrbitLink IoT: Remote agricultural satellite IoT mesh facing low unit margins and node failure risks.
"""

from typing import List, Dict, Any
from .schemas import StartupProfile, AttackerFinding, VulnerabilityMap

# ==========================================
# PRECONFIGURED STARTUPS & VULNERABILITY MAPS
# ==========================================

MOCK_STARTUPS: Dict[str, Dict[str, Any]] = {
    # ------------------------------------------
    # 1. EcoPacker (Sustainable Packaging)
    # ------------------------------------------
    "ecopacker": {
        "profile": StartupProfile(
            name="EcoPacker",
            problem="Single-use plastic packaging generates millions of tons of waste annually. Brands want to shift to sustainable alternatives but find current options fragile, expensive, and difficult to customize.",
            solution="We manufacture highly durable, water-resistant, biodegradable packaging made from agricultural crop waste (corn husks and sugarcane bagasse). We use a proprietary binding process that matches plastic durability at a lower cost.",
            target_customer="Mid-to-large e-commerce brands and food delivery platforms aiming for net-zero emissions.",
            business_model="B2B direct sales and recurring supply contracts. Tiered pricing based on volume (per unit) with custom branding setup fees.",
            technology="Proprietary organic binder formula combined with automated thermoforming machinery. Patent-pending heat-sealing coating."
        ),
        "vulnerabilities": VulnerabilityMap(
            overall_risk_score=78,
            findings=[
                AttackerFinding(
                    category="Market",
                    severity="High",
                    reasoning="The packaging market is highly commoditized. While mid-to-large e-commerce brands state net-zero goals, actual switching costs and price sensitivity are extremely high. Brands will revert to plastic if EcoPacker is even 10% more expensive.",
                    attack_question="How will you overcome the commodity pricing trap when major competitors can scale plastic production to keep prices significantly lower than yours?",
                    suggested_mitigation="Pivot marketing from 'sustainability only' to 'reduced shipping weight and damage rates' by demonstrating physical superiority, or target premium brands first where margins are higher."
                ),
                AttackerFinding(
                    category="Business",
                    severity="Medium",
                    reasoning="B2B sales to enterprise e-commerce and food delivery platforms typically have sales cycles of 9-12 months. This creates a severe cash flow runway risk for an early-stage startup.",
                    attack_question="How will your startup survive the long enterprise procurement cycles before securing recurring supply contracts?",
                    suggested_mitigation="Offer a standardized 'starter pack' online for immediate purchase by SMBs to generate cash flow, while pursuing longer enterprise deals in parallel."
                ),
                AttackerFinding(
                    category="Technology",
                    severity="High",
                    reasoning="Biodegradable materials made from sugarcane and corn husks naturally absorb moisture. Under high humidity or prolonged storage, the structural integrity of the box degrades, risking damage to shipped goods.",
                    attack_question="What guarantees can you give to food delivery clients that your packaging won't dissolve or lose structural integrity in high-humidity climates?",
                    suggested_mitigation="Introduce a hydrophobic, plant-based wax coating layer and publish third-party humidity degradation test logs."
                )
            ]
        )
    },
    # ------------------------------------------
    # 2. MedRoute AI (Healthcare AI Triage)
    # ------------------------------------------
    "medroute": {
        "profile": StartupProfile(
            name="MedRoute AI",
            problem="Emergency departments are overcrowded, leading to long wait times and high patient dissatisfaction. Existing triage systems are manual, slow, and prone to clinical errors.",
            solution="An AI-powered emergency department routing system. It uses patient vital inputs and a natural language description of symptoms to predict patient severity, triage them in real-time, and route them to the optimal care provider.",
            target_customer="Large metropolitan hospital systems and urgent care networks.",
            business_model="SaaS subscription license billed monthly per emergency department, based on average patient volume. Setup and EHR integration fee.",
            technology="Proprietary clinical NLP transformer models trained on anonymized EHR records. Real-time integration engine with Epic and Cerner APIs."
        ),
        "vulnerabilities": VulnerabilityMap(
            overall_risk_score=85,
            findings=[
                AttackerFinding(
                    category="Market",
                    severity="High",
                    reasoning="Hospital systems are highly risk-averse and dominated by EHR giants like Epic and Cerner. These giants are actively developing their own AI triage features, creating a severe platform-displacement risk.",
                    attack_question="Why wouldn't a hospital wait for Epic or Cerner to release their native AI triage updates rather than purchasing a third-party tool like MedRoute AI?",
                    suggested_mitigation="Position MedRoute AI as an orchestration layer that works across different hospital networks, or patent a unique real-time routing algorithm that outperforms standard EHR models."
                ),
                AttackerFinding(
                    category="Business",
                    severity="Medium",
                    reasoning="Hospital sales require multiple committee approvals (clinical, IT, legal, security). The pricing model is complex and hospitals expect clear, audited cost-reduction data prior to committing to recurring SaaS fees.",
                    attack_question="What clinical and financial evidence do you have to prove to hospital boards that MedRoute AI reduces operating costs?",
                    suggested_mitigation="Partner with a single hospital for a pilot program to gather direct ROI data (e.g., reduction in wait times and nurse cognitive load) before attempting to sell to large networks."
                ),
                AttackerFinding(
                    category="Technology",
                    severity="High",
                    reasoning="NLP models can hallucinate or fail to recognize rare, life-threatening symptoms (e.g. atypical presentations of myocardial infarction). A single misclassified patient could lead to fatal outcomes and catastrophic legal liabilities.",
                    attack_question="How does MedRoute AI prevent catastrophic clinical triage mistakes, and who bears the legal liability if the AI misclassifies a critical patient?",
                    suggested_mitigation="Implement a 'human-in-the-loop' safeguard where the AI suggestions must be signed off by a triage nurse, and position the AI as a clinical decision support tool rather than a final decision maker."
                )
            ]
        )
    },
    # ------------------------------------------
    # 3. OrbitLink IoT (Satellite Sensor Mesh)
    # ------------------------------------------
    "orbitlink": {
        "profile": StartupProfile(
            name="OrbitLink IoT",
            problem="Remote agricultural fields, oil pipelines, and environmental stations lack cellular coverage. Satellite IoT hardware is currently bulky, expensive, and requires high power consumption.",
            solution="Ultra-low power, pocket-sized IoT sensors that communicate via a proprietary mesh network over long distances (LoRa), routing data to a single satellite-linked gateway. This lowers satellite costs by 80%.",
            target_customer="Precision farming companies, oil & gas operators, and environmental research institutes.",
            business_model="Hardware sales for the sensors and gateway + monthly data subscription plan per active gateway for satellite uplink bandwidth.",
            technology="Custom ultra-narrowband radio transceivers, low-power LoRa mesh protocol, and compact satellite receiver modules."
        ),
        "vulnerabilities": VulnerabilityMap(
            overall_risk_score=72,
            findings=[
                AttackerFinding(
                    category="Market",
                    severity="Medium",
                    reasoning="Farmers and environmental researchers are notoriously slow to adopt hardware tech. The value proposition of continuous remote data is clear, but hardware installation and maintenance overhead remains a significant friction point.",
                    attack_question="How will you scale adoption among non-technical farm operators who refuse to spend days configuring and installing physical mesh gateways?",
                    suggested_mitigation="Ship pre-configured, 'plug-and-play' solar-powered units that require zero setup other than pressing a single button, and offer installation-as-a-service through regional agricultural distributors."
                ),
                AttackerFinding(
                    category="Business",
                    severity="High",
                    reasoning="Hardware manufacturing has low margins at small volumes. If OrbitLink cannot scale to tens of thousands of units quickly, high BOM (Bill of Materials) costs will eat up their cash, especially since they rely on third-party satellite networks for backhaul.",
                    attack_question="How do you plan to achieve unit economic profitability while paying third-party satellite providers for bandwidth at low initial customer volumes?",
                    suggested_mitigation="Negotiate volume-based wholesale satellite bandwidth contracts, and price hardware at cost or slightly above, relying on high-margin data subscriptions for profitability."
                ),
                AttackerFinding(
                    category="Technology",
                    severity="Medium",
                    reasoning="Remote environmental sensors must withstand freezing winters and extreme heat. LoRa mesh relies on daisy-chaining signals; if a single critical sensor node breaks, the entire network branch can go offline.",
                    attack_question="How does your mesh network maintain reliability in harsh weather if a single node fails, and what is your failover mechanism?",
                    suggested_mitigation="Implement self-healing mesh routing algorithms where nodes automatically search for alternative parent nodes, and utilize ultra-durable IP68-rated weatherproofing for all enclosures."
                )
            ]
        )
    }
}

