import random
from typing import Dict, List
from src.utils.logging import get_logger

logger = get_logger(__name__)


class OpponentAgent:
    def __init__(self):
        self.action_history = []
        self.fencer_patterns = []
        self.phase = "learning"
        self.exchange_count = 0
        self.pattern_counts = {}

    def init_exchange(self):
        self.action_history = []
        self.exchange_count += 1
        if self.exchange_count <= 2:
            self.phase = "learning"
        else:
            self.phase = "adapting"

    def execute_action(self, fencer_action: dict = None) -> dict:
        if fencer_action:
            self._learn_pattern(fencer_action)

        if self.phase == "learning" or not self.fencer_patterns:
            action = self._random_action()
        else:
            action = self._adaptive_action()

        self.action_history.append(action)
        logger.info(f"Opponent executed: {action}")
        return action

    def _random_action(self) -> dict:
        actions = [
            {"type": "direct_attack", "target": "torso"},
            {"type": "fleche", "target": "torso"},
            {"type": "counter_attack", "target": "shoulders"},
            {"type": "parry_and_riposte", "target": "torso"},
            {"type": "compound_attack", "target": "back"},
        ]
        return random.choice(actions)

    def _learn_pattern(self, fencer_action: dict):
        action_type = fencer_action.get("type", "unknown")
        self.fencer_patterns.append(action_type)
        self.pattern_counts[action_type] = self.pattern_counts.get(action_type, 0) + 1

    def _adaptive_action(self) -> dict:
        if not self.pattern_counts:
            return self._random_action()

        most_common = max(self.pattern_counts.items(), key=lambda x: x[1])
        predictability = most_common[1] / sum(self.pattern_counts.values())

        if random.random() < min(predictability, 0.7):
            return self._exploit_weakness(most_common[0])
        else:
            return self._strategic_action()

    def _exploit_weakness(self, common_action: str) -> dict:
        exploit_map = {
            "direct_attack": {"type": "counter_attack", "target": "shoulders"},
            "fleche": {"type": "parry_and_riposte", "target": "torso"},
            "counter_attack": {"type": "compound_attack", "target": "back"},
            "parry_and_riposte": {"type": "fleche", "target": "torso"},
            "compound_attack": {"type": "direct_attack", "target": "torso"},
        }
        return exploit_map.get(common_action, self._random_action())

    def _strategic_action(self) -> dict:
        actions = [
            {"type": "direct_attack", "target": "torso"},
            {"type": "fleche", "target": "back"},
            {"type": "counter_attack", "target": "shoulders"},
            {"type": "compound_attack", "target": "torso"},
            {"type": "parry_and_riposte", "target": "back"},
        ]
        return random.choice(actions)

    def get_valid_actions(self) -> list:
        return [
            "direct_attack",
            "compound_attack",
            "fleche",
            "parry_and_riposte",
            "counter_attack",
            "remise"
        ]

    def reset(self):
        self.action_history = []