import json
from typing import Optional
from src.utils.config import get_rules
from src.utils.logging import get_logger

logger = get_logger(__name__)


class RefereeAgent:
    def __init__(self):
        self.rules = get_rules()
        self.score = {"fencer": 0, "opponent": 0}
        self.penalty_stack = []
        self.current_call = None
        self.exchange_history = []

    def reset(self):
        self.score = {"fencer": 0, "opponent": 0}
        self.penalty_stack = []
        self.current_call = None
        self.exchange_history = []

    def judge_action(self, fencer_action: dict, opponent_action: dict) -> dict:
        fencer_type = fencer_action.get("type", "")
        opponent_type = opponent_action.get("type", "")

        fencer_target = fencer_action.get("target", "torso")
        opponent_target = opponent_action.get("target", "torso")

        call = self._determine_winner(fencer_type, opponent_type)

        fencer_hit = call in ["fencer", "both"]
        opponent_hit = call in ["opponent", "both"]

        fencer_valid = self._is_valid_target(fencer_target)
        opponent_valid = self._is_valid_target(opponent_target)

        fencer_score = 1 if fencer_hit and fencer_valid else 0
        opponent_score = 1 if opponent_hit and opponent_valid else 0

        if fencer_score:
            self.score["fencer"] += fencer_score
        if opponent_score:
            self.score["opponent"] += opponent_score

        result = {
            "call": call,
            "fencer_hit": fencer_hit,
            "opponent_hit": opponent_hit,
            "fencer_valid": fencer_valid,
            "opponent_valid": opponent_valid,
            "fencer_score": fencer_score,
            "opponent_score": opponent_score,
            "score": self.score.copy(),
            "reason": self._get_call_reason(call, fencer_type, opponent_type),
            "is_match_over": self._is_match_over()
        }

        self.current_call = result
        self.exchange_history.append({
            "fencer_action": fencer_action,
            "opponent_action": opponent_action,
            "result": result
        })

        logger.info(f"Referee call: {call} - Score: {self.score}")
        return result

    def _determine_winner(self, fencer_type: str, opponent_type: str) -> str:
        priority_actions = self.rules["right_of_way_rules"]["priority_attacks"]
        secondary_actions = self.rules["right_of_way_rules"]["secondary_actions"]

        fencer_priority = priority_actions.index(fencer_type) if fencer_type in priority_actions else 999
        opponent_priority = priority_actions.index(opponent_type) if opponent_type in priority_actions else 999

        if fencer_type in priority_actions and opponent_type not in priority_actions:
            return "fencer"
        elif opponent_type in priority_actions and fencer_type not in priority_actions:
            return "opponent"
        elif fencer_priority < opponent_priority:
            return "fencer"
        elif opponent_priority < fencer_priority:
            return "opponent"
        else:
            return "both"

    def _is_valid_target(self, target: str) -> bool:
        valid_areas = self.rules["valid_target_areas"]
        return target in valid_areas

    def _get_call_reason(self, call: str, fencer_type: str, opponent_type: str) -> str:
        reasons = {
            "fencer": f"Fencer's {fencer_type} has priority over opponent's {opponent_type}",
            "opponent": f"Opponent's {opponent_type} has priority over fencer's {fencer_type}",
            "both": f"Simultaneous actions - both fencers score"
        }
        return reasons.get(call, "Unable to determine")

    def _is_match_over(self) -> bool:
        from src.utils.config import WINNING_SCORE
        return self.score["fencer"] >= WINNING_SCORE or self.score["opponent"] >= WINNING_SCORE

    def get_halt_command(self) -> str:
        commands = self.rules["referee_commands"]["halts"]
        return commands[0]

    def get_match_result(self) -> dict:
        return {
            "winner": "fencer" if self.score["fencer"] > self.score["opponent"] else "opponent",
            "final_score": self.score.copy()
        }