from src.utils.logging import get_logger

logger = get_logger(__name__)


class FencerAgent:
    def __init__(self):
        self.action_history = []

    def execute_action(self, action_type: str, target: str = None) -> dict:
        action = {
            "type": action_type,
            "target": target or "torso",
            "side": "right" if not self.action_history else self._get_opposite_side()
        }
        self.action_history.append(action)
        logger.info(f"Fencer executed: {action}")
        return action

    def _get_opposite_side(self) -> str:
        if not self.action_history:
            return "right"
        return "left" if self.action_history[-1]["side"] == "right" else "right"

    def get_valid_actions(self) -> list:
        return [
            "direct_attack",
            "compound_attack",
            "fleche",
            "parry_and_riposte",
            "counter_attack",
            "remise",
            "prise_de_fer"
        ]

    def get_valid_targets(self) -> list:
        return ["torso", "back", "shoulders"]

    def reset(self):
        self.action_history = []