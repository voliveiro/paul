import os
import json
import anthropic
from agents import AGENTS
from datetime import datetime

client = anthropic.Anthropic()

ORCHESTRATOR_PROMPT = """You are a senior policy analyst facilitating an inter-agency consultation. Given responses from several ministries, map the deliberative terrain across four dimensions:

1. FAULT LINES — Where do agencies genuinely disagree, and is it about values, evidence, or jurisdiction?
2. UNEXPECTED CONSENSUS — Where do agencies agree despite different framings?
3. UNANSWERED QUESTIONS — What has the proposal failed to address?
4. MISSING ACTORS — Which stakeholders are absent but materially affected?

Be analytically sharp. Name things precisely. Avoid diplomatic smoothing. Write like a senior civil servant, not an academic. Short sentences. Plain words. No jargon. If you can cut a word, cut it. Flag problems directly — do not soften them."""

SYNERGIES_PROMPT = """You are a senior policy analyst facilitating an inter-agency consultation. Given responses from several ministries, identify where agencies can work together and where their objectives reinforce each other. Structure your analysis across four dimensions:

1. SHARED OBJECTIVES — Where do agencies have overlapping goals that could be pursued jointly rather than in parallel?
2. COMPLEMENTARY CAPABILITIES — Which agencies bring different but compatible tools, resources, or powers that, combined, would produce better outcomes than either acting alone?
3. NATURAL COALITIONS — Which groupings of two or three agencies have the strongest case for a joint programme, task force, or co-funding arrangement? Name the specific grouping and the specific opportunity.
4. QUICK WINS — What collaborative actions could begin immediately, without new legislation or structural change?

Be concrete. Name the agencies, the mechanism, and the outcome. Avoid vague calls for "coordination". If genuine collaboration is unlikely, say so and explain why. Write like a senior civil servant: short sentences, plain words, no jargon."""

# MOF always deliberates, and always speaks last so it can weigh the cost of every other position
FINAL_AGENT = "mof"


def order_agent_ids(ids):
    """Drop unknown ids and duplicates, ensure FINAL_AGENT is included, and move it to the end."""
    known = {a.id for a in AGENTS}
    seen = set()
    ordered = [i for i in ids if i in known and i != FINAL_AGENT and not (i in seen or seen.add(i))]
    return ordered + [FINAL_AGENT]


with open(os.path.join(os.path.dirname(__file__), "agents", "summaries.json")) as _f:
    AGENT_SUMMARIES = json.load(_f)


def select_agents(proposal):
    """Ask Claude to pick the most relevant agents; MOF is always added, last (3–5 in total)."""
    agent_profiles = []
    for a in AGENTS:
        if a.id == FINAL_AGENT:
            continue
        summary = AGENT_SUMMARIES.get(a.id, a.role)
        agent_profiles.append(f"[{a.id}] {a.name}: {summary}")

    profiles_text = "\n\n".join(agent_profiles)

    prompt = f"""You are selecting which government agencies should deliberate on a policy proposal.

PROPOSAL:
"{proposal}"

AVAILABLE AGENCIES:
{profiles_text}

The Ministry of Finance is always included automatically, so do not select it. Select between 2 and 4 further agencies whose mandates make them most directly and substantively relevant to this proposal. Prioritise agencies with genuine jurisdictional stakes, not peripheral interest.

Return ONLY a JSON array of agency IDs (lowercase strings), e.g. ["mti", "mha", "msf"]. No explanation, no other text."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=80,
        messages=[{"role": "user", "content": prompt}]
    )

    text = response.content[0].text.strip()
    selected = json.loads(text)
    others = order_agent_ids(selected)[:-1][:4]  # at most 4 others + MOF = 5 in total
    return others + [FINAL_AGENT]


def load_proposal(path="proposal.txt"):
    with open(path, "r") as f:
        return f.read().strip()

def call_agent(system_prompt, user_message, max_tokens=2000):
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}]
    )
    return response.content[0].text


def build_context(proposal, prior_responses):
    context = f"Policy proposal under consultation:\n\n\"{proposal}\"\n\n"
    if prior_responses:
        context += "Prior agency positions:\n\n"
        for r in prior_responses:
            context += f"{r['name']} ({r['role']}):\n{r['text']}\n\n"
        context += "Please provide your ministry's assessment, taking note of positions already stated."
    else:
        context += "Please provide your ministry's assessment of this proposal."
    return context


def save_output(proposal, responses, synthesis):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"simulation_{timestamp}.txt"
    with open(path, "w") as f:
        f.write("POLICY SIMULATION OUTPUT\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"PROPOSAL:\n{proposal}\n\n")
        f.write("=" * 60 + "\n\n")
        for r in responses:
            f.write(f"=== {r['name']} ({r['role']}) ===\n\n")
            f.write(r['text'] + "\n\n")
            f.write("-" * 60 + "\n\n")
        f.write("=== ORCHESTRATOR SYNTHESIS ===\n\n")
        f.write(synthesis + "\n")
    print(f"\nOutput saved to {path}")


def run_simulation_stream(proposal, selected_ids=None, synthesis_mode="standard"):
    """Generator that yields SSE-formatted events as each agent responds."""
    if selected_ids is None:
        selected_ids = [a.id for a in AGENTS]
    by_id = {a.id: a for a in AGENTS}
    agents = [by_id[i] for i in order_agent_ids(selected_ids)]

    responses = []

    for agent in agents:
        context = build_context(proposal, responses)
        text = call_agent(agent.system_prompt, context)

        print(f"\n=== {agent.name} ===\n{text}")

        r = {"id": agent.id, "name": agent.name, "role": agent.role, "text": text}
        responses.append(r)

        yield f"data: {json.dumps({'type': 'agent', **r})}\n\n"

    # Synthesis pass
    prompt = SYNERGIES_PROMPT if synthesis_mode == "synergies" else ORCHESTRATOR_PROMPT

    synthesis_input = f"Policy proposal:\n\"{proposal}\"\n\nAgency responses:\n\n"
    for r in responses:
        synthesis_input += f"=== {r['name']} ({r['role']}) ===\n{r['text']}\n\n"
    synthesis_input += "Please provide your analytical synthesis."

    synthesis = call_agent(prompt, synthesis_input, max_tokens=8000)

    print(f"\n=== SYNTHESIS ===\n{synthesis}")

    save_output(proposal, responses, synthesis)

    yield f"data: {json.dumps({'type': 'synthesis', 'text': synthesis})}\n\n"
    yield f"data: {json.dumps({'type': 'done'})}\n\n"


if __name__ == "__main__":
    proposal = load_proposal()
    for event in run_simulation_stream(proposal):
        print(event, end="")
