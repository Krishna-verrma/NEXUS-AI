from app.agents.data_agent import DataAgent as NewDataAgent

class DataAnalystAgent(NewDataAgent):
    def __init__(self):
        super().__init__(agent_id="data_analyst")
