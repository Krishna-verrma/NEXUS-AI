from app.agents.reviewer_agent import ReviewerAgent as NewReviewerAgent

class ReviewerAgent(NewReviewerAgent):
    def __init__(self):
        super().__init__(agent_id="reviewer")
