import random
from src.agents.fencer import FencerAgent
from src.agents.opponent import OpponentAgent
from src.agents.referee import RefereeAgent
from src.agents.coach import CoachAgent
from src.utils.config import WINNING_SCORE
from src.utils.logging import get_logger

logger = get_logger(__name__)


class FencingCrew:
    def __init__(self):
        self.fencer = FencerAgent()
        self.opponent = OpponentAgent()
        self.referee = RefereeAgent()
        self.coach = CoachAgent()
        self.exchange_number = 0
        self.current_opponent_action = None
        self.current_distance = None

    def start_new_match(self):
        logger.info("Starting new fencing match")
        self.fencer.reset()
        self.opponent.reset()
        self.referee.reset()
        self.coach.reset()
        self.exchange_number = 0
        self._generate_opponent_intent()
        return {
            "status": "match_started",
            "winning_score": WINNING_SCORE,
            "score": self.referee.score.copy()
        }

    def _generate_opponent_intent(self):
        self.opponent.init_exchange()
        self.current_opponent_action = self.opponent.execute_action()
        self.current_distance = random.choice(["close", "medium", "far"])

    def get_opponent_intent(self) -> dict:
        return {
            "action": self.current_opponent_action,
            "distance": self.current_distance
        }

    def execute_exchange(self, fencer_action: str = None) -> dict:
        self.exchange_number += 1

        self.opponent.init_exchange()

        fencer_action_type = fencer_action if fencer_action else "direct_attack"
        fencer_action_dict = self.fencer.execute_action(fencer_action_type, "torso")

        opponent_action = self.opponent.execute_action(fencer_action_dict)

        result = self.referee.judge_action(fencer_action_dict, opponent_action)

        response = {
            "exchange_number": self.exchange_number,
            "fencer_action": fencer_action_dict,
            "opponent_action": opponent_action,
            "referee_call": result,
            "score": result["score"],
            "match_over": result["is_match_over"]
        }

        if result["is_match_over"]:
            match_result = self.referee.get_match_result()
            response["match_result"] = match_result
            exchange_history = self.referee.exchange_history
            coach_feedback = self.coach.analyze_exchange(exchange_history, result["score"])
            response["coach_feedback"] = coach_feedback
        else:
            self._generate_opponent_intent()

        return response

    def get_coach_feedback(self) -> dict:
        return self.coach.analyze_exchange(
            self.referee.exchange_history,
            self.referee.score
        )

    def get_current_state(self) -> dict:
        return {
            "score": self.referee.score.copy(),
            "exchange_count": self.exchange_number,
            "exchange_history": self.referee.exchange_history,
            "match_over": self.referee._is_match_over()
        }

    def get_valid_actions(self) -> list:
        return self.fencer.get_valid_actions()

    def get_valid_targets(self) -> list:
        return self.fencer.get_valid_targets()