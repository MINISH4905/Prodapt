import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.attackers.attack_engine import run_attack
from backend.models.schemas import AttackRequest

load_dotenv()

app = FastAPI(title="VentureX-Ray Attacker Module")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/demo-mode")
def demo_mode_status():
    return {"demo_mode": DEMO_MODE}


@app.post("/api/attack")
def attack(request: AttackRequest):
    idea = request.idea.strip()

    if not idea:
        raise HTTPException(status_code=400, detail="Please enter a startup idea.")

    try:
        result = run_attack(idea)
        return result.model_dump()
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to complete attack analysis.",
        )


frontend_path = Path(__file__).resolve().parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
