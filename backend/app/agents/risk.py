from app.agents.security_agent import SecurityAgent as NewSecurityAgent

class RiskAgent(NewSecurityAgent):
    def __init__(self):
        super().__init__(agent_id="risk")
