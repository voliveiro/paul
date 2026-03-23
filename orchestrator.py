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

def load_proposal(path="proposal.txt"):
    with open(path, "r") as f:
        return f.read().strip()

def call_agent(system_prompt, user_message, max_tokens=1000):
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

def run_simulation(proposal, agents=None):
    if agents is None:
        agents = AGENTS

    responses = []

    for agent in agents:
        context = build_context(proposal, responses)
        text = call_agent(agent.system_prompt, context)

        print(f"\n=== {agent.name} ===")
        print(text)
        
        responses.append({
            "id": agent.id,
            "name": agent.name,
            "role": agent.role,
            "text": text
        })

    # Synthesis pass
    synthesis_input = f"Policy proposal:\n\"{proposal}\"\n\nAgency responses:\n\n"
    for r in responses:
        synthesis_input += f"=== {r['name']} ({r['role']}) ===\n{r['text']}\n\n"
    synthesis_input += "Please provide your analytical synthesis."

    synthesis = call_agent(ORCHESTRATOR_PROMPT, synthesis_input, max_tokens=8000)

    print("\n=== SYNTHESIS ===")
    print(synthesis)

    save_output(proposal, responses, synthesis)

    return {
        "proposal": proposal,
        "responses": responses,
        "synthesis": synthesis
    }

if __name__ == "__main__":
    proposal = load_proposal()
    run_simulation(proposal)