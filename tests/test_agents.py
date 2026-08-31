from src.agents.coach import CoachAgent
from src.agents.fencer import FencerAgent
from src.agents.opponent import OpponentAgent
from src.agents.referee import RefereeAgent


class TestFencerAgent:
    def test_execute_action_returns_valid_dict(self):
        fencer = FencerAgent()
        action = fencer.execute_action("direct_attack", "torso")

        assert "type" in action
        assert "target" in action
        assert action["type"] == "direct_attack"
        assert action["target"] == "torso"

    def test_get_valid_actions(self):
        fencer = FencerAgent()
        actions = fencer.get_valid_actions()

        assert isinstance(actions, list)
        assert len(actions) > 0
        assert "direct_attack" in actions

    def test_get_valid_targets(self):
        fencer = FencerAgent()
        targets = fencer.get_valid_targets()

        assert isinstance(targets, list)
        assert "torso" in targets


class TestOpponentAgent:
    def test_execute_action_returns_valid_dict(self):
        opponent = OpponentAgent()
        action = opponent.execute_action()

        assert "type" in action
        assert "target" in action

    def test_adaptive_learning(self):
        opponent = OpponentAgent()
        opponent._learn_pattern({"type": "direct_attack"})

        assert len(opponent.fencer_patterns) == 1
        assert "direct_attack" in opponent.pattern_counts

    def test_exploit_weakness_different_actions(self):
        opponent = OpponentAgent()
        opponent.pattern_counts = {"direct_attack": 5}

        action = opponent._exploit_weakness("direct_attack")
        assert action["type"] == "counter_attack"


class TestRefereeAgent:
    def test_judge_action_fencer_priority(self):
        referee = RefereeAgent()
        result = referee.judge_action(
            {"type": "fleche", "target": "torso"},
            {"type": "parry", "target": "torso"}
        )

        assert result["call"] in ["fencer", "both"]

    def test_score_updates(self):
        referee = RefereeAgent()
        referee.judge_action(
            {"type": "direct_attack", "target": "torso"},
            {"type": "counter_attack", "target": "torso"}
        )

        assert "fencer" in referee.score
        assert "opponent" in referee.score

    def test_valid_target_detection(self):
        referee = RefereeAgent()
        assert referee._is_valid_target("torso") is True
        assert referee._is_valid_target("head") is False

    def test_match_over_detection(self):
        referee = RefereeAgent()
        referee.score = {"fencer": 5, "opponent": 3}
        assert referee._is_match_over() is True


class TestCoachAgent:
    def test_analyze_exchange_returns_feedback(self):
        coach = CoachAgent()
        exchange = [
            {
                "fencer_action": {"type": "direct_attack", "target": "torso"},
                "opponent_action": {"type": "counter_attack", "target": "shoulders"},
                "result": {"call": "fencer", "fencer_score": 1, "opponent_score": 0}
            }
        ]
        score = {"fencer": 1, "opponent": 0}

        feedback = coach.analyze_exchange(exchange, score)

        assert "summary" in feedback
        assert "technical" in feedback
        assert "strategic" in feedback
        assert "tactical" in feedback

    def test_analyze_exchange_empty_history(self):
        coach = CoachAgent()
        feedback = coach.analyze_exchange([], {"fencer": 0, "opponent": 0})

        assert "error" in feedback