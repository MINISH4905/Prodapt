# VentureX-Ray — Scoring & Decision Module

> "Break Your Startup Before Investors Break It."

This repository contains **only** the **Scoring & Decision** module of the
larger VentureX-Ray project. It receives an investor ↔ founder conversation,
analyzes it with Claude, calculates a deterministic defense score, and
decides whether the startup's story is **STRONG** or **WEAK** — and if WEAK,
which attacker module should perform the targeted re-attack.

```
Investor Conversation
        │
        ▼
Conversation Analyzer (Claude)
        │
        ▼
   Defense Score (deterministic)
        │
        ▼
   Decision Engine (deterministic)
        │
        ▼
   STRONG / WEAK
        │
        ▼
If WEAK → target_attacker
```

---

## 1. What this module does

- Accepts a dynamic investor ↔ founder conversation over REST.
- Sends the conversation to Claude for structured analysis across 7
  dimensions (clarity, evidence, confidence, consistency, market/business/
  technology knowledge) plus a list of weak areas.
- Calculates a weighted **defense score** (0–100) using deterministic Python
  logic — Claude never computes the score.
- Applies a deterministic **decision engine** to output `STRONG` or `WEAK`.
- If `WEAK`, identifies the correct attacker (`MARKET_ATTACKER`,
  `BUSINESS_ATTACKER`, or `TECHNOLOGY_ATTACKER`) for a targeted re-attack.

This module does **not** implement the Attacker Module or the Final Report
Module — it only produces the correct output contract for those modules to
consume.

---

## 2. Architecture

```
FastAPI
   │
   ▼
Analyzer (analyzer.py)
   │
   ▼
LLM Client (llm_client.py)
   │
   ▼
Claude API
   │
   ▼
Structured Analysis (AnalysisResult)
   │
   ▼
Scorer (scorer.py)         ← deterministic, no LLM
   │
   ▼
Decision Engine (decision_engine.py)   ← deterministic, no LLM
```

Only `llm_client.py` ever touches the Anthropic SDK or the API key. No other
file in the project may import `anthropic` or read `ANTHROPIC_API_KEY`
directly.

---

## 3. Folder structure

```
backend/
│
├── main.py
├── requirements.txt
├── .env
├── .env.example
├── .gitignore
├── README.md
│
├── modules/
│   ├── __init__.py
│   │
│   └── scoring/
│       ├── __init__.py
│       ├── analyzer.py
│       ├── scorer.py
│       ├── decision_engine.py
│       ├── llm_client.py
│       ├── models.py
│       └── prompts.py
│
└── tests/
    └── test_scoring.py
```

---

## 4. Installation

```bash
cd backend
python -m venv venv
```

## 5. Activate the virtual environment

macOS / Linux:
```bash
source venv/bin/activate
```

Windows:
```bash
venv\Scripts\activate
```

Then install dependencies:

```bash
pip install -r requirements.txt
```

---

## 6. Environment variables

Copy the example file and fill in your own values:

```bash
cp .env.example .env
```

`.env` (already present in this repo as a placeholder) requires:

```
ANTHROPIC_API_KEY=your_api_key_here
CLAUDE_MODEL=your_claude_model_here
```

`.env` is listed in `.gitignore` and must **never** be committed.

## 7. How to add your Claude API key

Open `backend/.env` and replace the placeholder:

```
ANTHROPIC_API_KEY=YOUR_KEY_HERE
CLAUDE_MODEL=YOUR_MODEL_HERE
```

with your real key and model name, e.g.:

```
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxx
CLAUDE_MODEL=claude-sonnet-4-5
```

The key is read only inside `modules/scoring/llm_client.py` via
`os.getenv("ANTHROPIC_API_KEY")`. It is never hardcoded and never appears in
error messages or logs.

---

## 8. How to run FastAPI

From the `backend/` directory:

```bash
python -m uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## 9. Swagger URL

```
http://127.0.0.1:8000/docs
```

---

## 10. API endpoints

| Method | Path                          | Description                                             |
|--------|-------------------------------|-----------------------------------------------------------|
| GET    | `/`                            | Health check                                             |
| POST   | `/api/v1/scoring/analyze`      | Full pipeline: analysis → score → decision (main endpoint) |
| POST   | `/api/v1/scoring/score`        | Runs only Claude analysis, returns `AnalysisResult`        |
| POST   | `/api/v1/scoring/decision`     | Full pipeline, returns only the `DecisionResult`            |

All three POST endpoints accept the same request body: a `ConversationRequest`.

---

## 11. Example request

```http
POST /api/v1/scoring/analyze
Content-Type: application/json
```

```json
{
  "conversation": [
    {
      "investor": "Why will customers choose your product?",
      "founder": "Because our AI is better."
    },
    {
      "investor": "How is it better?",
      "founder": "It gives more accurate results."
    },
    {
      "investor": "What prevents competitors from copying you?",
      "founder": "Our technology is unique."
    }
  ]
}
```

---

## 12. Example response

```json
{
  "defense_score": 61.25,
  "analysis": {
    "clarity": 70,
    "evidence": 40,
    "confidence": 80,
    "consistency": 65,
    "market_knowledge": 50,
    "business_knowledge": 45,
    "technology_knowledge": 70,
    "weak_areas": ["business", "competitive_moat"],
    "reasoning": [
      "Founder responses were generally confident.",
      "Founder did not provide concrete evidence.",
      "Competitive differentiation was not clearly defended."
    ]
  },
  "decision": "WEAK",
  "next_action": "TARGETED_REATTACK",
  "target_attacker": "BUSINESS_ATTACKER",
  "weak_areas": ["business", "competitive_moat"],
  "reason": "The founder's business justification and competitive moat require further stress testing."
}
```

---

## 13. How other modules connect

Any other VentureX-Ray module (written in any language/framework) can
integrate purely over HTTP:

1. Build a `ConversationRequest` JSON body containing the investor ↔ founder
   turns collected so far.
2. `POST` it to `http://<host>:8000/api/v1/scoring/analyze`.
3. Read `decision`, `next_action`, `target_attacker`, `weak_areas`, and
   `reason` from the JSON response to decide what to do next:
   - If `decision == "STRONG"` → forward the result to the **Final Report
     module**.
   - If `decision == "WEAK"` → forward `target_attacker` and `weak_areas` to
     the **Attacker Module** for a targeted re-attack.

No shared database, message queue, or in-process import is required — the
REST contract below is the entire integration surface.

---

## 14. Targeted re-attack contract

When `decision` is `"WEAK"`, the response includes:

```json
{
  "decision": "WEAK",
  "next_action": "TARGETED_REATTACK",
  "target_attacker": "BUSINESS_ATTACKER",
  "weak_areas": ["business", "pricing"],
  "reason": "..."
}
```

`target_attacker` is always one of `MARKET_ATTACKER`, `BUSINESS_ATTACKER`, or
`TECHNOLOGY_ATTACKER`. This output is meant to be consumed directly by the
Attacker Module, which is **not** implemented in this repository.

---

## 15. Strong decision contract

When the startup passes:

```json
{
  "decision": "STRONG",
  "next_action": "FINAL_REPORT",
  "target_attacker": null,
  "weak_areas": [],
  "reason": "Founder demonstrated sufficient investor defense."
}
```

This output is meant to be consumed directly by the Final Report module,
which is **not** implemented in this repository.

---

## Running tests

From the `backend/` directory:

```bash
pytest
```

Tests cover: defense score calculation, STRONG decisions, WEAK decisions,
attacker selection (market/business/technology), tiebreak priority, and
empty-conversation validation (HTTP 400) — all without calling the real
Claude API, since scoring and decision logic are fully deterministic.
