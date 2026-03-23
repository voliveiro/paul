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

with open(os.path.join(os.path.dirname(__file__), "agents", "summaries.json")) as _f:
    AGENT_SUMMARIES = json.load(_f)


def select_agents(proposal):
    """Ask Claude to pick 3–5 most relevant agents for this proposal."""
    agent_profiles = []
    for a in AGENTS:
        summary = AGENT_SUMMARIES.get(a.id, a.role)
        agent_profiles.append(f"[{a.id}] {a.name}: {summary}")

    profiles_text = "\n\n".join(agent_profiles)

    prompt = f"""You are selecting which government agencies should deliberate on a policy proposal.

PROPOSAL:
"{proposal}"

AVAILABLE AGENCIES:
{profiles_text}

Select between 3 and 5 agencies whose mandates make them most directly and substantively relevant to this proposal. Prioritise agencies with genuine jurisdictional stakes, not peripheral interest.

Return ONLY a JSON array of agency IDs (lowercase strings), e.g. ["mti", "mha", "msf"]. No explanation, no other text."""

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=80,
        messages=[{"role": "user", "content": prompt}]
    )

    text = response.content[0].text.strip()
    selected = json.loads(text)
    known = {a.id for a in AGENTS}
    selected = [aid for aid in selected if aid in known]
    # Clamp to 3–5
    return selected[:5] if len(selected) >= 3 else selected


def load_proposal(path="proposal.txt"):
    with open(path, "r") as f:
        return f.read().strip()

def call_agent(system_prompt, user_message, max_tokens=2000):
    response = client.messages.create(
        model="claude-sonnet-4-5",
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


def run_simulation_stream(proposal, selected_ids=None):
    """Generator that yields SSE-formatted events as each agent responds."""
    agents = AGENTS
    if selected_ids is not None:
        id_set = set(selected_ids)
        agents = [a for a in AGENTS if a.id in id_set]

    responses = []

    for agent in agents:
        context = build_context(proposal, responses)
        text = call_agent(agent.system_prompt, context)

        print(f"\n=== {agent.name} ===\n{text}")

        r = {"id": agent.id, "name": agent.name, "role": agent.role, "text": text}
        responses.append(r)

        yield f"data: {json.dumps({'type': 'agent', **r})}\n\n"

    # Synthesis pass
    synthesis_input = f"Policy proposal:\n\"{proposal}\"\n\nAgency responses:\n\n"
    for r in responses:
        synthesis_input += f"=== {r['name']} ({r['role']}) ===\n{r['text']}\n\n"
    synthesis_input += "Please provide your analytical synthesis."

    synthesis = call_agent(ORCHESTRATOR_PROMPT, synthesis_input, max_tokens=8000)

    print(f"\n=== SYNTHESIS ===\n{synthesis}")

    save_output(proposal, responses, synthesis)

    yield f"data: {json.dumps({'type': 'synthesis', 'text': synthesis})}\n\n"
    yield f"data: {json.dumps({'type': 'done'})}\n\n"


if __name__ == "__main__":
    proposal = load_proposal()
    for event in run_simulation_stream(proposal):
        print(event, end="")
