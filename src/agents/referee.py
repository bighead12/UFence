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

        fencer_hit = call == "fencer"
        opponent_hit = call == "opponent"
        is_simultaneous = call == "simultaneous"

        fencer_valid = self._is_valid_target(fencer_target)
        opponent_valid = self._is_valid_target(opponent_target)

        # In foil, simultaneous = no one scores
        if is_simultaneous:
            fencer_score = 0
            opponent_score = 0
        else:
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
            "is_match_over": self._is_match_over(),
        }

        self.current_call = result
        self.exchange_history.append(
            {
                "fencer_action": fencer_action,
                "opponent_action": opponent_action,
                "result": result,
            }
        )

        logger.info(f"Referee call: {call} - Score: {self.score}")
        return result

    def _normalize_action(self, action: str) -> str:
        return action.replace("_", "-")

    def _determine_winner(self, fencer_type: str, opponent_type: str) -> str:
        priority_actions = self.rules["right_of_way_rules"]["priority_attacks"]
        secondary_actions = self.rules["right_of_way_rules"]["secondary_actions"]

        fencer_type_norm = self._normalize_action(fencer_type)
        opponent_type_norm = self._normalize_action(opponent_type)

        fencer_is_priority = fencer_type_norm in priority_actions
        opponent_is_priority = opponent_type_norm in priority_actions

        fencer_is_secondary = fencer_type_norm in secondary_actions
        opponent_is_secondary = opponent_type_norm in secondary_actions

        # Priority action beats everything
        if fencer_is_priority and not opponent_is_priority:
            return "fencer"
        if opponent_is_priority and not fencer_is_priority:
            return "opponent"

        # Secondary beats non-priority non-secondary
        if fencer_is_secondary and not opponent_is_secondary:
            return "fencer"
        if opponent_is_secondary and not fencer_is_secondary:
            return "opponent"

        # Both priority - check action priority order
        if fencer_is_priority and opponent_is_priority:
            fencer_idx = (
                priority_actions.index(fencer_type_norm)
                if fencer_type_norm in priority_actions
                else 999
            )
            opponent_idx = (
                priority_actions.index(opponent_type_norm)
                if opponent_type_norm in priority_actions
                else 999
            )
            if fencer_idx < opponent_idx:
                return "fencer"
            elif opponent_idx < fencer_idx:
                return "opponent"
            else:
                return "simultaneous"

        # Both secondary - compare indices
        if fencer_is_secondary and opponent_is_secondary:
            fencer_idx = (
                secondary_actions.index(fencer_type_norm)
                if fencer_type_norm in secondary_actions
                else 999
            )
            opponent_idx = (
                secondary_actions.index(opponent_type_norm)
                if opponent_type_norm in secondary_actions
                else 999
            )
            if fencer_idx < opponent_idx:
                return "fencer"
            elif opponent_idx < fencer_idx:
                return "opponent"
            else:
                return "simultaneous"

        # Non-priority vs non-priority = simultaneous
        return "simultaneous"

    def _is_valid_target(self, target: str) -> bool:
        valid_areas = self.rules["valid_target_areas"]
        return target in valid_areas

    def _get_call_reason(self, call: str, fencer_type: str, opponent_type: str) -> str:
        reasons = {
            "fencer": f"Fencer's {fencer_type} has priority over opponent's {opponent_type}",
            "opponent": f"Opponent's {opponent_type} has priority over fencer's {fencer_type}",
            "simultaneous": "Simultaneous actions - no touch awarded",
        }
        return reasons.get(call, "Unable to determine")

    def _is_match_over(self) -> bool:
        from src.utils.config import WINNING_SCORE

        return (
            self.score["fencer"] >= WINNING_SCORE
            or self.score["opponent"] >= WINNING_SCORE
        )

    def get_halt_command(self) -> str:
        commands = self.rules["referee_commands"]["halts"]
        return commands[0]

    def get_match_result(self) -> dict:
        return {
            "winner": "fencer"
            if self.score["fencer"] > self.score["opponent"]
            else "opponent",
            "final_score": self.score.copy(),
        }
