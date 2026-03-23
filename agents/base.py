from dataclasses import dataclass

@dataclass
class AgentProfile:
    id: str          # e.g. "mti"
    name: str        # e.g. "MTI"
    role: str        # e.g. "Ministry of Trade and Industry"
    system_prompt: str
