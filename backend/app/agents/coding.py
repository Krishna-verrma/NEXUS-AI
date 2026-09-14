from app.agents.coding_agent import CodingAgent as NewCodingAgent

class CodingAgent(NewCodingAgent):
    def __init__(self):
        super().__init__()
        self.agent_id = "coding"
