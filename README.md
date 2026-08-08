# VentureX-Ray — Module 7: Investor Simulation

Part of **PitchCraft AI**, an AI-powered startup stress-testing and refinement system.

## 1. What is VentureX-Ray?

Most founders prepare a pitch by focusing on why their idea sounds good. VentureX-Ray does the
opposite: it tries to **break the startup idea first**. Multiple AI "attackers" (market, technical,
business/investor) probe the idea for weaknesses, producing a **Vulnerability Map**. A refinement
step then strengthens the pitch using that map. The refined pitch is then handed to a simulated,
skeptical investor for a live due-diligence conversation — which is exactly what this module does.

## 2. What does Module 7 do?

Module 7 simulates a **skeptical investor conversation** with the founder, based dynamically on the
refined pitch and vulnerability map produced by earlier modules (it never hard-codes a startup idea).

The investor:

- Asks one question at a time, remembering the full conversation (state is kept explicitly in
  Python, not relied upon from LLM memory).
- Analyzes each founder answer for specificity, evidence, unsupported claims, and contradictions.
- Follows up on weak or unsupported answers before moving on.
- Probes unresolved vulnerabilities from the upstream Vulnerability Map — without ever revealing
  that it's following an internal "attacker" script.
- Increases question difficulty progressively across rounds.
- Stops after a configurable number of rounds, or earlier once evidence is judged sufficient.
- Produces structured output for the next module (Conversation Analysis → Defense Score →
  Strong/Weak Decision → Re-Attack Decision).

## 3. Architecture

Two logical AI agents, plus explicit Python-managed state:

```text
                     ┌─────────────────────────┐
                     │   Refinement Module      │
                     │  (upstream, not in this  │
                     │        repo)             │
                     └────────────┬─────────────┘
                                  │ refined_pitch, vulnerability_map,
                                  │ founder_concerns
                                  ▼
                     ┌─────────────────────────┐
                     │     Session Manager      │  <- explicit state, in-memory
                     │  (app/services)          │
                     └────────────┬─────────────┘
                                  │
                 ┌────────────────┴─────────────────┐
                 ▼                                   ▲
      ┌────────────────────┐              ┌─────────────────────┐
      │   Agent A:          │              │   Agent B:           │
      │   Investor Agent     │◄────────────│   Answer Analyzer     │
      │  "what to ask next?" │  analysis    │  "how strong was      │
      │  (app/agents)        │              │   that answer?"       │
      └──────────┬───────────┘              └──────────▲────────────┘
                 │ question                             │ founder answer
                 ▼                                       │
           ┌────────────┐                          ┌────────────┐
           │  Founder    │─────────────────────────▶│  Founder    │
           │ (question)  │        answers            │  (answer)   │
           └────────────┘                          └────────────┘
```

Agent A (`app/agents/investor_agent.py`) decides *what to ask*: Python control logic
(`decide_focus`) picks the strategic focus (opening questions, following up on a weak answer,
probing an unresolved vulnerability, or a general due-diligence question at high difficulty), and
the LLM turns that focus into a natural investor question via a structured JSON prompt.

Agent B (`app/agents/answer_analyzer.py`) decides *how strong the answer was*: specificity,
evidence, unsupported claims, contradictions, relevance, and whether follow-up is required.

Both agents fall back to deterministic, non-LLM logic if the LLM is unavailable or returns
unparseable output, so the API never hard-fails just because of an LLM hiccup.

## 4. Data flow

```text
INPUT (from Refinement Module)
{
  "refined_pitch": "...",
  "vulnerability_map": {...},
  "founder_concerns": [...]
}
        │
        ▼
POST /investor/start  →  first investor question
        │
        ▼
POST /investor/answer (loop) → answer analysis + next question, until stop condition
        │
        ▼
POST /investor/end  →  final structured result
        │
        ▼
OUTPUT (to Conversation Analysis Module)
{
  "conversation": [...],
  "founder_performance": {...},
  "weak_areas": [...],
  "unsupported_claims": [...],
  "investor_concerns": [...],
  "recommendation": "..."
}
```

## 5. Installation

Requires Python 3.10+.

```bash
cd investor_simulation
python -m venv .venv
source .venv/bin/activate   # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# then edit .env and set GEMINI_API_KEY
```

## 6. Environment variables

| Variable            | Required | Default            | Description                                             |
|----------------------|----------|---------------------|-----------------------------------------------------------|
| `GEMINI_API_KEY`     | No*      | (none)              | Google Gemini API key. Without it, agents use deterministic fallback logic instead of the LLM. |
| `GEMINI_MODEL`       | No       | `gemini-1.5-flash`  | Gemini model name.                                       |
| `MAX_ROUNDS`         | No       | `8`                 | Default max rounds per session if not set per-request.   |
| `MAX_ANSWER_LENGTH`  | No       | `4000`              | Max characters accepted per founder answer.               |
| `MAX_HISTORY_TURNS`  | No       | `12`                | Max prior turns sent to the LLM as context per call.      |

\* The module is fully runnable without an API key thanks to fallback logic, but responses will be
generic/templated rather than LLM-generated. Set `GEMINI_API_KEY` for the full experience.

## 7. Running the API

```bash
uvicorn app.main:app --reload --port 8000
```

Interactive docs: `http://localhost:8000/docs`

## 8. API endpoints

### `POST /investor/start`

Starts a new investor simulation session.

**Request**

```json
{
  "session_id": "demo-001",
  "startup_id": "startup-001",
  "refined_pitch": "FreshCart AI helps users ...",
  "vulnerability_map": {
    "critical_vulnerabilities": [
      {"area": "Customer Acquisition", "severity": "HIGH", "reason": "CAC has not been validated"}
    ],
    "medium_vulnerabilities": [],
    "strengths": []
  },
  "founder_concerns": ["Not sure about pricing"],
  "max_rounds": 8
}
```

**Response**

```json
{
  "session_id": "demo-001",
  "round": 1,
  "question": "What specific problem are you solving, and for whom?",
  "status": "active"
}
```

### `POST /investor/answer`

Submits the founder's answer to the current question and receives the analysis plus the next
question (or a completion signal).

**Request**

```json
{
  "session_id": "demo-001",
  "answer": "We're solving grocery planning for busy families..."
}
```

**Response**

```json
{
  "session_id": "demo-001",
  "round": 2,
  "question": "Who specifically experiences this problem, and how did you validate it?",
  "answer_analysis": {
    "strength": 0.65,
    "evidence": false,
    "specificity": 0.5,
    "confidence": 0.6,
    "relevance": 0.7,
    "unsupported_claims": ["Founder claims strong demand without evidence"],
    "contradictions": [],
    "weak_areas": ["customer_validation"],
    "vulnerability_exposed": null,
    "follow_up_required": true
  },
  "status": "active",
  "stop_reason": null
}
```

When the session completes (max rounds reached or sufficient evidence gathered), `question` is
`null`, `status` is `"completed"`, and `stop_reason` is `"max_rounds_reached"` or
`"sufficient_evidence"`.

### `GET /investor/session/{session_id}`

Returns the full current session state (conversation history, topics covered, weak areas,
unsupported claims, evidence found).

### `POST /investor/end`

Ends the session (if not already completed) and returns the final structured result for the next
module.

**Request**

```json
{"session_id": "demo-001"}
```

**Response**

```json
{
  "session_id": "demo-001",
  "status": "completed",
  "total_rounds": 8,
  "conversation": [ { "role": "investor", "message": "..." }, { "role": "founder", "message": "..." } ],
  "founder_performance": {
    "overall_strength": 0.68,
    "evidence_quality": 0.55,
    "clarity": 0.72,
    "consistency": 0.80
  },
  "weak_areas": ["Customer acquisition", "Market validation"],
  "unsupported_claims": ["Claimed high demand without customer evidence"],
  "investor_concerns": ["Customer acquisition cost", "Competitive differentiation"],
  "recommendation": "NEEDS_IMPROVEMENT"
}
```

## 9. Demo script (no frontend needed)

```bash
python demo.py          # interactive: type founder answers yourself
python demo.py --auto   # non-interactive: uses a canned answer each round
```

The demo loads a sample refined pitch and vulnerability map, runs 5 rounds of the simulation, and
prints a final assessment as JSON.

## 10. Testing

```bash
pytest -v
```

Tests cover: session creation/duplication, question generation (including LLM fallback),
progressive-difficulty and vulnerability-probing focus logic, answer analysis (including keyword
fallback), round increment, max-rounds stopping, session retrieval, and session termination. The
LLM is mocked in tests so no API key is required to run the suite.

## 11. Integration with the rest of VentureX-Ray

**Upstream (Refinement Module → this module):** POST the refinement module's output
(`refined_pitch`, `vulnerability_map`, `founder_concerns`) directly to `/investor/start`. No
hard-coded startup data is used anywhere in this module — everything comes from the request body.

**Downstream (this module → Conversation Analysis):** The JSON returned by `/investor/end` is
designed to be passed directly into the next module (Conversation Analysis → Defense Score →
Strong/Weak Decision → Re-Attack Decision).

## 12. Project structure

```text
investor_simulation/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── demo.py
│
├── app/
│   ├── main.py                     # FastAPI app entrypoint
│   │
│   ├── agents/
│   │   ├── investor_agent.py       # Agent A: decides what to ask next
│   │   └── answer_analyzer.py      # Agent B: scores the founder's answer
│   │
│   ├── api/
│   │   └── investor_routes.py      # /investor/* endpoints
│   │
│   ├── models/
│   │   └── schemas.py              # Pydantic request/response/state models
│   │
│   ├── services/
│   │   ├── llm_client.py           # Reusable Gemini API client
│   │   └── session_manager.py      # In-memory session state store
│   │
│   └── prompts/
│       ├── investor_prompt.py      # Agent A prompt template
│       └── analyzer_prompt.py      # Agent B prompt template
│
└── tests/
    ├── test_investor_agent.py      # Agent-level unit tests
    └── test_api.py                 # API integration tests
```

## 13. Notes on scope

This is a hackathon MVP by design (see spec section 20): in-memory session storage only, no
database, no Redis, no Docker/Kubernetes, no LangChain/LangGraph, no auth. All of the required
functionality — dynamic input, conversation memory, answer analysis, progressive difficulty,
vulnerability probing, and clean FastAPI endpoints — is implemented directly in plain Python +
FastAPI + Pydantic for clarity and easy grading/demo.
