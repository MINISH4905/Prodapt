# Module 7 — Investor Simulation: Presentation & Testing Guide

---

## 1. Simple Explanation — How This Module Works

Think of it like a **mock investor interview simulator**, but the investor is an AI that actually
remembers what you said and gets tougher over time.

**The flow, in plain English:**

1. You feed it a startup pitch + a list of known weaknesses (produced by earlier modules in the
   pipeline — the "attackers").
2. The **Investor Agent** asks a question — starting simple ("What problem are you solving?").
3. The founder answers.
4. The **Answer Analyzer** silently grades that answer: Was it specific? Did it have evidence? Did
   it contradict something said earlier? Is it vague?
5. Based on that grade, the Investor Agent decides what to ask next:
   - If the answer was weak → it presses harder on the *same* topic.
   - If the answer was solid → it moves to a new topic.
   - If there's an unresolved weakness from the vulnerability map (e.g. "customer acquisition cost
     is unvalidated") → it steers the conversation there, without ever saying "the system flagged
     this."
6. This repeats for a fixed number of rounds (or stops early if the founder has clearly proven
   their case).
7. At the end, it outputs a structured report: how strong the founder's defense was, which claims
   were unsupported, which areas are still weak, and an overall recommendation.

**The key trick:** there are two separate AI "brains," not one blob:
- **Agent A (Investor)** — decides *what to ask*.
- **Agent B (Analyzer)** — decides *how good the last answer was*.

And all the memory (what's been asked, what's been covered, how many rounds are left) is tracked
explicitly in plain Python — the AI is never trusted to "remember" on its own. This makes the
conversation reliable and debuggable instead of a black box.

---

## 2. Step-by-Step: How to Test This Module Before Integrating

### Step 1 — Install dependencies
```bash
cd investor_simulation
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2 — Set up environment variables
```bash
cp .env.example .env
```
Open `.env` and paste your `GEMINI_API_KEY`. (If you skip this, the module still runs — it just
uses simpler fallback logic instead of the LLM. Good for a quick smoke test.)

### Step 3 — Run the automated test suite
```bash
pytest -v
```
This checks the core logic without needing a real API key (the LLM is mocked in tests):
- Session creation and duplicate-ID handling
- Question generation + fallback behavior
- Progressive difficulty calculation
- Vulnerability-probing logic
- Answer analysis + fallback behavior
- Round increments and max-round stopping
- Session retrieval and termination

✅ All tests passing = the internal logic is sound before you touch the API layer.

### Step 4 — Run the terminal demo (no server needed)
```bash
python demo.py
```
This runs the whole loop end-to-end in your terminal — you play the founder, type answers, and
watch the investor question, analysis, and final report happen live. Fastest way to "feel" the
module working.

Non-interactive version (auto-answers, useful for quick checks):
```bash
python demo.py --auto
```

### Step 5 — Start the actual API server
```bash
uvicorn app.main:app --reload --port 8000
```
Open `http://localhost:8000/docs` — this gives you an interactive Swagger UI where you can literally
click "Try it out" on each endpoint without writing any code.

### Step 6 — Test the API endpoints manually (curl or Swagger UI)
Test in this order (see Section 3 for exact payloads):
1. `POST /investor/start` → confirm you get back round 1 and a question.
2. `POST /investor/answer` → submit an answer, confirm round increments and analysis looks sane.
3. `GET /investor/session/{id}` → confirm conversation history is accumulating correctly.
4. Repeat `POST /investor/answer` until max rounds is hit → confirm `status` becomes `"completed"`.
5. `POST /investor/end` → confirm you get the final structured report.

### Step 7 — Test edge cases (robustness check)
- Submit an answer with **no active session** → should return `404`.
- Submit an answer to an **already-completed session** → should return `400`.
- Submit an **empty answer** → should be rejected by validation.
- Submit an answer **way too long** (9000+ characters) → should be rejected (`422`).
- Temporarily remove `GEMINI_API_KEY` from `.env` and restart → module should still respond using
  fallback logic instead of crashing.

### Step 8 — Only now, integrate
Once steps 1–7 pass cleanly, plug it into the upstream Refinement Module (feed its real
`refined_pitch` / `vulnerability_map` output into `/investor/start`) and the downstream
Conversation Analysis module (consume the output of `/investor/end`).

---

## 3. Sample Input & Output

### `POST /investor/start`

**Sample Input:**
```json
{
  "session_id": "demo-001",
  "startup_id": "startup-001",
  "refined_pitch": "FreshCart AI scans a user's fridge via photo, auto-generates a weekly grocery list, compares prices across nearby stores, and lets users order through partnered delivery apps.",
  "vulnerability_map": {
    "critical_vulnerabilities": [
      {"area": "Customer Acquisition", "severity": "HIGH", "reason": "CAC has not been validated"},
      {"area": "Competition", "severity": "HIGH", "reason": "Instacart already offers similar features"}
    ],
    "medium_vulnerabilities": [],
    "strengths": ["Clear problem statement", "Working price-comparison prototype"]
  },
  "founder_concerns": ["Not sure our computer vision accuracy is good enough yet"],
  "max_rounds": 6
}
```

**Sample Output:**
```json
{
  "session_id": "demo-001",
  "round": 1,
  "question": "What specific problem are you solving, and for whom?",
  "status": "active"
}
```

---

### `POST /investor/answer` (founder gives a weak, unsupported answer)

**Sample Input:**
```json
{
  "session_id": "demo-001",
  "answer": "We're solving grocery planning for busy families. We think demand is really high."
}
```

**Sample Output:**
```json
{
  "session_id": "demo-001",
  "round": 2,
  "question": "What evidence do you have that busy families are actually willing to pay for this?",
  "answer_analysis": {
    "strength": 0.35,
    "evidence": false,
    "specificity": 0.4,
    "confidence": 0.5,
    "relevance": 0.7,
    "unsupported_claims": ["Claimed high demand without customer evidence"],
    "contradictions": [],
    "weak_areas": ["customer_validation", "evidence"],
    "vulnerability_exposed": null,
    "follow_up_required": true
  },
  "status": "active",
  "stop_reason": null
}
```

Notice: the investor didn't move to a brand-new topic — it pressed for evidence because the answer
was vague ("we think") with no proof.

---

### `POST /investor/end` (after all rounds)

**Sample Input:**
```json
{ "session_id": "demo-001" }
```

**Sample Output:**
```json
{
  "session_id": "demo-001",
  "status": "completed",
  "total_rounds": 6,
  "conversation": [ "...full back-and-forth transcript..." ],
  "founder_performance": {
    "overall_strength": 0.58,
    "evidence_quality": 0.4,
    "clarity": 0.6,
    "consistency": 0.75
  },
  "weak_areas": ["customer_validation", "evidence"],
  "unsupported_claims": ["Claimed high demand without customer evidence"],
  "investor_concerns": ["Customer Acquisition", "Competition"],
  "recommendation": "NEEDS_IMPROVEMENT"
}
```

This is exactly the shape the next module (Conversation Analysis → Defense Score) expects.

---

## 4. How to Demonstrate This Module to the Jury

**Recommended demo format (5–7 minutes):**

1. **Set the stage (30 sec).** Say: "This is Module 7 of VentureX-Ray. Earlier modules already
   attacked the idea and refined it. This module puts the founder in the hot seat with a live,
   memory-aware investor."
2. **Show the architecture diagram** (from README) for 20 seconds — two agents, explicit state,
   no hard-coded startup.
3. **Run the live demo:** `python demo.py` in a terminal — this is far more compelling than static
   slides because the jury sees real questions being generated live.
   - Answer the first question **vaguely** on purpose (e.g. "we think people will like it").
   - Point out live: "Watch — it doesn't move on. It's calling out that I gave no evidence."
   - Answer a later question **with a fake-but-specific detail** ("we ran a pilot with 50 users, 30%
     converted") and point out the strength score jumps up.
   - Let it run 1–2 more rounds until it reaches a vulnerability-probing question (e.g. about
     Customer Acquisition) — point out it never says "the vulnerability map flagged this," it just
     asks naturally.
4. **Show the final report** printed at the end — weak areas, unsupported claims, recommendation.
5. **Optional (if time allows):** Open `http://localhost:8000/docs` and hit `/investor/start` live
   to show it's a real, working API ready to plug into the rest of the pipeline, not just a script.
6. **Close with the integration story:** "This takes JSON in from the Refinement module, and puts
   JSON out for the Defense Score module — no manual glue code needed."

**Backup plan if live LLM calls are slow/unavailable during the demo:** the module has built-in
fallback logic, so even without internet/API access it will still ask sensible questions and score
answers using deterministic rules — the demo will not visibly break.

---

## 5. Presentation Content (Bullet Points)

**Slide: Problem**
- Founders pitch to sound good — they rarely pressure-test their own idea the way a real investor
  will.
- VentureX-Ray flips the process: attack the idea first, refine it, then rehearse the hardest
  conversation — the investor Q&A — before it happens for real.

**Slide: What Module 7 Does**
- Simulates a skeptical investor conducting live due diligence.
- Remembers the full conversation — no repeated questions, real follow-ups.
- Grades every answer for evidence, specificity, and contradictions.
- Escalates difficulty round by round.
- Quietly steers toward unresolved weaknesses instead of announcing them.

**Slide: Architecture**
- Two specialized AI agents instead of one chatbot:
  - Investor Agent → decides *what to ask*.
  - Answer Analyzer → decides *how strong the answer was*.
- Explicit Python-managed conversation state (not LLM memory) — reliable, debuggable, auditable.
- Deterministic control logic + LLM-generated natural language = best of both worlds.

**Slide: Key Design Decisions**
- Fully dynamic input — no hard-coded startup, works for any idea from the upstream module.
- Graceful fallback — the module keeps working even if the LLM call fails.
- Configurable stopping — fixed number of rounds, or early stop on strong evidence.
- Clean JSON contracts in and out — plug-and-play with the rest of the pipeline.

**Slide: Tech Stack**
- FastAPI + Pydantic (validated schemas everywhere)
- Google Gemini API for natural language generation
- In-memory session store (hackathon-appropriate — swappable for a database later)
- Full test suite with mocked LLM calls

**Slide: Output**
- Structured final report: founder performance scores, weak areas, unsupported claims, investor
  concerns, and a Strong / Needs Improvement / Weak recommendation — ready for the next module.

---

## 6. Likely Jury Questions & Clean Answers

**Q1: Why two separate agents instead of one big prompt?**
> Separating "what to ask" from "how good was the answer" keeps each agent's job simple and
> testable. It also stops the model from grading its own question in the same breath it asks it —
> which tends to produce biased, softer scoring. It mirrors how a real due-diligence team works:
> one person interviews, someone else independently evaluates the answer.

**Q2: How does it "remember" the conversation — is that just the LLM's context window?**
> No — we deliberately don't rely on that. Every question, answer, topic covered, and vulnerability
> probed is stored explicitly in a Python session object. The LLM only ever sees what we choose to
> hand it. This means the conversation state is 100% inspectable and won't silently drift or forget
> things the way relying purely on model memory could.

**Q3: What happens if the LLM API fails or is slow during a live demo?**
> Both agents have deterministic fallback logic. If the LLM call errors out or returns unusable
> output, the module falls back to rule-based question selection and keyword-based answer scoring
> instead of crashing. The API always returns a valid response.

**Q4: How do you stop the investor from just asking random questions forever?**
> Two stopping conditions: a hard cap on rounds (configurable per session), and an early-stop rule —
> if the founder has given several consecutive rounds of strong, evidence-backed, non-contradictory
> answers, the session can end early as "sufficient evidence gathered."

**Q5: How does it know to ask about a specific weakness without giving it away?**
> The vulnerability map is passed to the Investor Agent as internal context only — the prompt
> explicitly instructs it to let that context shape the *phrasing* of a natural question, but never
> to say something like "the system flagged this as a risk." We tested this by checking the
> generated questions never reference the vulnerability map directly.

**Q6: How do you handle a founder who lies or gives inconsistent answers?**
> The Answer Analyzer checks every new answer against the full prior conversation for
> contradictions, not just the current question. If it detects one, that becomes the top-priority
> follow-up for the very next question — the investor directly challenges the inconsistency.

**Q7: Is this specific to one startup, or is it hard-coded?**
> Fully dynamic. Every session is initialized purely from what's passed in the API request —
> `refined_pitch`, `vulnerability_map`, `founder_concerns`. Nothing about any specific startup is
> hard-coded anywhere in the code. The demo script uses a sample only for demonstration purposes.

**Q8: How would this scale beyond a hackathon (production concerns)?**
> The session store is currently in-memory for simplicity — swapping it for Redis or a database
> would be a small, contained change since all state access goes through one `SessionManager`
> class. Similarly, the LLM client is a single reusable wrapper, so swapping providers or adding
> retry/rate-limiting is localized to one file.

**Q9: How do you validate the LLM's output — what if it returns malformed JSON?**
> Every LLM response is passed through Pydantic model validation (`AnswerAnalysis`,
> `InvestorQuestion`). If parsing or validation fails for any reason, we log it and fall back to the
> deterministic logic rather than propagating a broken response to the user.

**Q10: What's the actual output this module hands off, and why does that format matter?**
> It hands off a structured JSON report — founder performance scores, weak areas, unsupported
> claims, investor concerns, and a recommendation. That shape is designed to be consumed directly by
> the next pipeline stage (Conversation Analysis → Defense Score → Strong/Weak decision) without any
> manual reformatting — the modules are meant to chain together automatically.

**Q11: How is "difficulty" actually calculated — is it just random?**
> No, it's a deterministic function of the current round versus the total configured rounds — it
> scales linearly from level 1 (basic) to level 5 (aggressive) as the conversation progresses. That
> difficulty number is then fed into the prompt, along with instructions for what "aggressive"
> means (unit economics, defensibility, scaling risk), rather than any implicit level being decided
independently by the LLM.

**Q12: Could a founder "game" the system by just writing long, keyword-stuffed answers?**
> To a degree, any evaluator — human or AI — can be gamed by keyword-stuffing. We mitigate it by
> scoring across multiple independent dimensions (specificity, evidence, confidence, relevance) and
> cross-checking claims against the rest of the conversation for contradictions, rather than scoring
> on any single surface signal. It's not perfect, but it's meaningfully harder to game than a
> single relevance score.
