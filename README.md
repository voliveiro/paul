# Paul — Policy Simulation Chamber

Paul is a multi-agent policy deliberation tool. You submit a policy proposal; a set of Singapore government agency agents deliberate on it from their institutional perspectives; an orchestrator synthesises fault lines, unexpected consensus, and blind spots.

It is not a consensus machine. It is a structured way to surface the tensions inside a proposal before it goes anywhere near a real room.

---

## How it works

1. Enter a policy proposal in the web interface
2. Select which agencies should deliberate, or leave all unselected and let the orchestrator choose 3–5 based on relevance
3. Each selected agency responds in sequence — later agencies can see what earlier ones said
4. The orchestrator analyses the full set of responses across four dimensions: fault lines, unexpected consensus, unanswered questions, and missing actors
5. Responses stream to the browser as they arrive — you do not wait for all agents to finish before seeing output

---

## Agents

17 agency agents are available:

| ID | Agency | Lens |
|----|--------|------|
| `mti` | Ministry of Trade and Industry | Economic competitiveness, investment, business regulation |
| `msf` | Ministry of Social and Family Development | Wellbeing, family, social inclusion, vulnerability |
| `mha` | Ministry of Home Affairs | Serious crime, national security, public order, border integrity |
| `mccy` | Ministry of Community, Culture and Youth | Community cohesion, inter-communal harmony, cultural identity |
| `moe` | Ministry of Education | Education, curriculum, skills, social mobility |
| `mindef` | Ministry of Defence | National defence, SAF, deterrence, Total Defence |
| `mforeign` | Ministry of Foreign Affairs | Diplomatic implications, international relations, treaty obligations |
| `mom` | Ministry of Manpower | Labour market, employment, foreign worker policy, workplace safety |
| `mse` | Ministry of Sustainability and the Environment | Environmental impact, climate policy, resource management |
| `mnd` | Ministry of National Development | Urban planning, land use, housing, infrastructure |
| `mot` | Ministry of Transport | Transport infrastructure, public transit, connectivity |
| `sndg` | Smart Nation and Digital Government Group | Digital government, GovTech, data governance |
| `minlaw` | Ministry of Law | Legal framework, legislation, rule of law, constitutional issues |
| `moh` | Ministry of Health | Public health, healthcare system, disease control |
| `comms` | Government Communications | Public trust, media ecosystem, information integrity |
| `psd` | Public Service Division | Implementation feasibility, inter-agency coordination, civil service |
| `mof` | Ministry of Finance | Fiscal sustainability, taxation, public expenditure |

Each agent has a system prompt that defines its institutional lens, priorities, and the questions it brings to any proposal. Agents are instructed to be analytically sharp, avoid diplomatic smoothing, and speak from their genuine jurisdiction — not to manufacture relevance.

---

## Orchestrator auto-selection

If no agencies are selected before running, the orchestrator reads a concise mandate summary for each of the 17 agents and picks 3–5 whose jurisdictions are most directly engaged by the proposal. The selected agencies are shown in the UI before the simulation begins.

Summaries used for selection are in `agents/summaries.json` — separate from the full system prompts, and editable independently.

---

## Setup

**Requirements:** Python 3.10+, an Anthropic API key.

```bash
git clone https://github.com/voliveiro/paul.git
cd paul
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```
ANTHROPIC_API_KEY=your_key_here
```

Run the server:

```bash
python app.py
```

Open `http://localhost:5001` in your browser.

---

## Project structure

```
paul/
├── app.py                  # Flask server — routes and SSE streaming
├── orchestrator.py         # Agent calls, simulation loop, auto-selection
├── agents/
│   ├── base.py             # AgentProfile dataclass
│   ├── summaries.json      # Concise mandate summaries for auto-selection
│   ├── mti.py              # ... and one file per agency agent
│   └── ...
├── frontend/
│   └── index.html          # Single-page UI
└── requirements.txt
```

---

## Adding or modifying agents

Each agent is defined in `agents/<id>.py` as an `AgentProfile` with four fields: `id`, `name`, `role`, and `system_prompt`. To add a new agent:

1. Create `agents/<id>.py` following the pattern of any existing agent file
2. Import and add it to the `AGENTS` list in `agents/__init__.py`
3. Add a one-line mandate summary to `agents/summaries.json`

To adjust how an agent deliberates, edit its `system_prompt`. To adjust whether it gets auto-selected for a given proposal type, edit its entry in `summaries.json`.

---

## Model

All agents and the orchestrator use `claude-sonnet-4-5`. Agent responses are capped at 2,000 tokens; the orchestrator synthesis at 8,000.
