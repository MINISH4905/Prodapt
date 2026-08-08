"""
VentureX-Ray Defense Module - Main FastAPI Application (main.py)
----------------------------------------------------------------
This module serves as the primary entry point and API router for the Defense & Refinement Engine
(Modules 4, 5, and 6) in the VentureX-Ray platform.

Architecture & Responsibilities:
1. REST API Routing:
   - GET  /api/startups: Exposes template startup pitches and pre-calculated vulnerability maps.
   - POST /api/refine: Module 4 - Refines startup pitches using Gemini LLM or mock fallbacks based on risk maps.
   - POST /api/generate-questions: Module 5 - Captures founder concerns and generates targeted clarity questions.
   - POST /api/evaluate-clarity: Module 6 - Evaluates founder responses to calculate clarity metrics and weak areas.
2. Middleware & CORS: Configures Cross-Origin Resource Sharing for seamless frontend integration.
3. Static File Delivery: Serves the modern Single Page Application (SPA) dashboard UI (`index.html` & static assets).
4. API Key Resolution: Prioritizes user-provided headers (`X-Gemini-API-Key`) over server `.env` credentials.
"""

import os
from fastapi import FastAPI, HTTPException, Header, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from .schemas import (
    StartupProfile, 
    VulnerabilityMap, 
    RefinedStartup, 
    FounderResponse, 
    ClarityEvaluation,
    ClarityQuestion
)
from .mock_inputs import MOCK_STARTUPS
from .agents import RefinementAgent, ConcernQuestionGenerator, ClarityEvaluator

# ==========================================
# ENVIRONMENT & APP CONFIGURATION
# ==========================================

# Load environment variables from local .env file if present
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path)

# Initialize FastAPI application instance with OpenAPI documentation metadata
app = FastAPI(
    title="VentureX-Ray - Defense Module API",
    description="Backend service for AI Refinement Agent (Module 4), Founder Concern Module (Module 5), and Founder Clarity Test (Module 6)."
)

# Enable CORS middleware to support local frontend development and cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# API REQUEST PAYLOAD MODELS
# ==========================================

class RefineRequest(BaseModel):
    """Payload for POST /api/refine. Accepts either a pre-configured startup_key or custom profile + vulnerabilities."""
    startup_key: Optional[str] = None
    profile: Optional[StartupProfile] = None
    vulnerabilities: Optional[VulnerabilityMap] = None

class QuestionsRequest(BaseModel):
    """Payload for POST /api/generate-questions. Requires refined startup model, vulnerabilities, and founder concerns."""
    refined: RefinedStartup
    vulnerabilities: VulnerabilityMap
    concerns: str

class EvaluateRequest(BaseModel):
    """Payload for POST /api/evaluate-clarity. Requires refined startup model and founder answers to clarity questions."""
    refined: RefinedStartup
    responses: List[FounderResponse]

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def select_api_key(header_key: Optional[str]) -> Optional[str]:
    """
    Resolves the Gemini API key to use for LLM agent calls.
    Prioritizes the client-supplied header `X-Gemini-API-Key`, falling back to the server environment variable.
    """
    return header_key or os.getenv("GEMINI_API_KEY")

# ==========================================
# REST API ENDPOINTS
# ==========================================

@app.get("/api/startups")
async def get_startups():
    """
    Retrieve available pre-loaded template startups and their associated vulnerability risk maps.
    Used by the frontend to populate the startup selection grid.
    """
    return [
        {
            "key": key,
            "name": val["profile"].name,
            "profile": val["profile"],
            "vulnerabilities": val["vulnerabilities"]
        }
        for key, val in MOCK_STARTUPS.items()
    ]

@app.post("/api/refine", response_model=RefinedStartup)
async def refine_startup(req: RefineRequest, x_gemini_api_key: Optional[str] = Header(None)):
    """
    Module 4 Endpoint: Refines the startup idea based on identified vulnerabilities.
    
    Processing Steps:
    1. Validates input parameters (startup_key or raw profile/vulnerabilities).
    2. Invokes RefinementAgent.refine_startup() using Gemini API or deterministic mock fallback.
    3. Returns the structured RefinedStartup model containing refined fields, change logs, and rationale.
    """
    api_key = select_api_key(x_gemini_api_key)
    
    # Identify target startup profile and vulnerabilities
    profile = None
    vulnerabilities = None
    
    if req.startup_key:
        if req.startup_key in MOCK_STARTUPS:
            profile = MOCK_STARTUPS[req.startup_key]["profile"]
            vulnerabilities = MOCK_STARTUPS[req.startup_key]["vulnerabilities"]
        else:
            raise HTTPException(status_code=400, detail="Invalid startup_key. Startup not found.")
    else:
        profile = req.profile
        vulnerabilities = req.vulnerabilities
        
    if not profile or not vulnerabilities:
        raise HTTPException(
            status_code=400, 
            detail="Must provide either a valid startup_key or both profile and vulnerabilities."
        )
        
    try:
        refined = RefinementAgent.refine_startup(profile, vulnerabilities, api_key=api_key)
        return refined
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Agent refinement failed: {str(e)}")

@app.post("/api/generate-questions", response_model=List[ClarityQuestion])
async def generate_questions(req: QuestionsRequest, x_gemini_api_key: Optional[str] = Header(None)):
    """
    Module 5 Endpoint: Captures founder concerns and generates targeted clarity questions.
    
    Processing Steps:
    1. Accepts refined startup model, original risk findings, and founder concern text.
    2. Invokes ConcernQuestionGenerator.generate_questions() to construct 3 probing questions.
    3. Returns a list of ClarityQuestion objects with contextual tags.
    """
    api_key = select_api_key(x_gemini_api_key)
    try:
        questions = ConcernQuestionGenerator.generate_questions(
            req.refined, 
            req.vulnerabilities, 
            req.concerns, 
            api_key=api_key
        )
        return questions
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Agent question generation failed: {str(e)}")

@app.post("/api/evaluate-clarity", response_model=ClarityEvaluation)
async def evaluate_clarity(req: EvaluateRequest, x_gemini_api_key: Optional[str] = Header(None)):
    """
    Module 6 Endpoint: Evaluates founder answers to compute clarity scores and weak areas.
    
    Processing Steps:
    1. Accepts founder responses to clarity questions alongside the refined startup context.
    2. Invokes ClarityEvaluator.evaluate_responses() to grade specificity, consistency, and groundedness.
    3. Returns a ClarityEvaluation object with scores (0-100), weak areas, and actionable remedies.
    """
    api_key = select_api_key(x_gemini_api_key)
    try:
        evaluation = ClarityEvaluator.evaluate_responses(req.refined, req.responses, api_key=api_key)
        return evaluation
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Agent evaluation failed: {str(e)}")

# ==========================================
# STATIC FILE SERVING FOR FRONTEND DASHBOARD
# ==========================================

# Resolve directory path to frontend dashboard assets
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../frontend"))

@app.get("/")
async def get_index():
    """Serves the single-page application dashboard index.html."""
    index_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="index.html not found.")

# Mount static asset directory for JS and CSS files under `/static`
app.mount("/static", StaticFiles(directory=frontend_dir), name="frontend")

