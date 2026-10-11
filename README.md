# Paul — Policy Simulation Chamber

Paul is a multi-agent policy deliberation tool. You submit a policy proposal; a set of Singapore government agency agents deliberate on it from their institutional perspectives; an orchestrator synthesises fault lines, unexpected consensus, and blind spots.

It is not a consensus machine. It is a structured way to surface the tensions inside a proposal before it goes anywhere near a real room.

---

## How it works

1. Enter a policy proposal in the web interface — type it, or upload a document (PDF, Word, TXT or Markdown)
2. Choose a synthesis mode: **Standard** (fault lines, consensus, blind spots) or **Synergies** (where agencies can work together)
3. Select which agencies should deliberate, or leave all unselected and let the orchestrator choose 2–4 based on relevance. The Ministry of Finance always takes part and always responds last
4. Each selected agency responds in sequence — later agencies can see what earlier ones said
5. The orchestrator synthesises the full set of responses (see [Synthesis modes](#synthesis-modes))
6. Responses stream to the browser as they arrive, formatted as they would be in a document — you do not wait for all agents to finish before seeing output
7. When the simulation finishes, download the whole thing as a Word report

---

## Features

### Document upload

Click **⇪ Upload document** above the proposal box, or drag a file onto it. Supported formats:

| Format | Notes |
|--------|-------|
| PDF | Text-based PDFs only — scanned PDFs (images of pages) contain no text to extract |
| Word (`.docx`) | Paragraphs and tables, in document order. Older `.doc` files are not supported — save as `.docx` first |
| Text / Markdown (`.txt`, `.md`) | Read as UTF-8 |

The extracted text is placed in the proposal box so you can check or edit it before running. Uploads are limited to 20 MB.

### Synthesis modes

- **Standard** — the orchestrator maps the deliberative terrain across four dimensions: fault lines, unexpected consensus, unanswered questions, and missing actors.
- **Synergies** — the orchestrator looks for collaboration instead: shared objectives, complementary capabilities, natural coalitions, and quick wins.

### Ministry of Finance always responds last

Cost is always a factor, so MOF takes part in every simulation and always responds last, just before the orchestrator. Because agencies see earlier responses, MOF weighs the cost implications of every other agency's position. In the UI, MOF appears as a locked chip marked "always last". See [Orchestrator auto-selection](#orchestrator-auto-selection).

### Formatted output

Agency and orchestrator responses are rendered from Markdown — headings, lists, bold, tables — rather than shown as raw text. Rendering uses [marked](https://marked.js.org/) and [DOMPurify](https://github.com/cure53/DOMPurify), loaded from a CDN; if they cannot load (for example, offline), responses fall back to plain text.

### Word report export

When a simulation completes, a **⬇ Download report (.docx)** button appears. The report contains:

- A title section with the date, agencies consulted, and synthesis mode
- The full policy proposal
- Each agency's response, under its own heading
- The orchestrator synthesis

Markdown in the responses is converted to native Word formatting, so headings show up in Word's navigation pane.

### Sample proposals

Two test proposals are included in `samples/`:

| File | Scope |
|------|-------|
| `heat_resilience_proposal.docx` | Detailed, multi-agency: work-rest rules, dormitory cooling, an urban cooling levy, heat alerts, shifted working hours, with a cost table |
| `senior_transport_proposal.docx` | Short and simple: free off-peak public transport for seniors. Designed for three agencies — MOT, MSF and MOF |

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

If no agencies are selected before running, the orchestrator reads a concise mandate summary for each of the 17 agents and picks 2–4 whose jurisdictions are most directly engaged by the proposal. MOF is then added automatically, giving 3–5 agencies in total. The selected agencies are shown in the UI before the simulation begins.

MOF is always included and always responds last — whether agencies are picked manually or by the orchestrator — so it can weigh the cost implications of every other agency's position. This is set by `FINAL_AGENT` in `orchestrator.py`.

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

Open `http://localhost:5001` in your browser. Keep the terminal open while you use Paul; press `Ctrl+C` to stop the server.

To start Paul again later:

```bash
cd paul
source venv/bin/activate
python app.py
```

---

## Project structure

```
paul/
├── app.py                  # Flask server — routes, SSE streaming, upload extraction
├── orchestrator.py         # Agent calls, simulation loop, auto-selection, MOF-last rule
├── export.py               # Builds the Word report from a finished simulation
├── agents/
│   ├── base.py             # AgentProfile dataclass
│   ├── summaries.json      # Concise mandate summaries for auto-selection
│   ├── mti.py              # ... and one file per agency agent
│   └── ...
├── frontend/
│   └── index.html          # Single-page UI
├── samples/                # Test proposals to upload
└── requirements.txt
```

---

## API endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/agents` | List all agents |
| `POST` | `/select-agents` | Orchestrator picks agencies for a proposal (MOF always added, last) |
| `POST` | `/simulate` | Run a simulation; streams server-sent events |
| `POST` | `/extract` | Upload a file (`multipart/form-data`, field `file`); returns its text |
| `POST` | `/export` | Send a finished simulation as JSON; returns a `.docx` report |

---

## Adding or modifying agents

Each agent is defined in `agents/<id>.py` as an `AgentProfile` with four fields: `id`, `name`, `role`, and `system_prompt`. To add a new agent:

1. Create `agents/<id>.py` following the pattern of any existing agent file
2. Import and add it to the `AGENTS` list in `agents/__init__.py`
3. Add a one-line mandate summary to `agents/summaries.json`

To adjust how an agent deliberates, edit its `system_prompt`. To adjust whether it gets auto-selected for a given proposal type, edit its entry in `summaries.json`.

---

## Model

All agents and the orchestrator use `claude-sonnet-4-6`. Agent responses are capped at 2,000 tokens; the orchestrator synthesis at 8,000.
