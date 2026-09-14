from app.agents.report_agent import ReportAgent as NewReportAgent

class ReportAgent(NewReportAgent):
    def __init__(self):
        super().__init__(agent_id="report")
