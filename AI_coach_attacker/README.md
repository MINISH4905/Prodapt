# VentureX-Ray — AI Attacker Module

AI Startup Stress Testing System. Three independent AI attackers analyze a startup idea and produce a structured vulnerability map.

## Architecture

```
STARTUP IDEA → HTML Frontend → FastAPI → Attack Engine → 3 AI Attackers → Vulnerability Map → JSON Output
```

## Attackers

| Attacker | Persona | Focus |
|----------|---------|-------|
| Market | Hostile Market Analyst | Customer, demand, competition, differentiation, acquisition |
| Business | Investor Skeptic | Revenue, pricing, costs, CAC, retention, unit economics, scalability |
| Technology | Skeptical CTO | Feasibility, AI dependency, scalability, security, reliability, technical moat |

## Setup

1. **Create virtual environment**

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Configure environment**

```bash
copy .env.example .env
```

Edit `.env`:

```
OPENAI_API_KEY=your_key_here
DEMO_MODE=false
```

Set `DEMO_MODE=true` to run without an OpenAI API key (returns sample data).

4. **Start the server**

```bash
uvicorn backend.main:app --reload --port 8000
```

5. **Open the UI**

Navigate to [http://localhost:8000](http://localhost:8000)

## API Endpoints

### `GET /api/health`

```json
{ "status": "ok" }
```

### `POST /api/attack`

**Request:**

```json
{
  "idea": "An AI platform that helps college students find internships."
}
```

**Response:**

```json
{
  "idea": "...",
  "attackers": {
    "market": { "attacker": "market", "score": 78, "risk_level": "HIGH", "summary": "...", "vulnerabilities": [...] },
    "business": { "attacker": "business", "score": 65, "risk_level": "HIGH", "summary": "...", "vulnerabilities": [...] },
    "technology": { "attacker": "technology", "score": 42, "risk_level": "MEDIUM", "summary": "...", "vulnerabilities": [...] }
  },
  "vulnerability_map": {
    "overall_risk": 61.7,
    "market_risk": 78,
    "business_risk": 65,
    "technology_risk": 42,
    "critical": [],
    "high": [],
    "medium": [],
    "low": []
  }
}
```

## Demo Mode

Set `DEMO_MODE=true` in `.env` to return pre-built sample responses without calling OpenAI. The UI displays a **DEMO MODE** badge when enabled.

## Integration Output

The JSON response from `POST /api/attack` is the integration contract for downstream modules. Do not modify the structure.

## Tech Stack

- **Frontend:** HTML, CSS, Vanilla JavaScript
- **Backend:** Python, FastAPI
- **AI:** OpenAI API (gpt-4o-mini)
