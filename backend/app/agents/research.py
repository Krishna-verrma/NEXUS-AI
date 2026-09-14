from app.agents.research_agent import ResearchAgent as NewResearchAgent

class ResearchAgent(NewResearchAgent):
    def __init__(self):
        super().__init__(agent_id="research")
