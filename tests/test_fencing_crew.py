"""Comprehensive test suite for FencingCrew orchestration."""

from src.agents.coach import CoachAgent
from src.agents.fencer import FencerAgent
from src.agents.opponent import OpponentAgent
from src.agents.referee import RefereeAgent
from src.crew.fencing_crew import FencingCrew


class TestFencingCrew:
    """Test the FencingCrew orchestration layer."""

    def test_start_new_match_resets_all_agents(self):
        crew = FencingCrew()
        # Play an exchange first to dirty state
        crew.execute_exchange("direct_attack", "torso")

        crew.start_new_match()

        assert crew.referee.score == {"fencer": 0, "opponent": 0}
        assert crew.exchange_number == 0
        assert crew.fencer.action_history == []
        assert crew.referee.exchange_history == []
        # Opponent has 1 action from _generate_opponent_intent
        assert len(crew.opponent.action_history) == 1

    def test_start_new_match_returns_expected_keys(self):
        crew = FencingCrew()
        result = crew.start_new_match()

        assert result["status"] == "match_started"
        assert "winning_score" in result
        assert "score" in result
        assert result["score"] == {"fencer": 0, "opponent": 0}

    def test_get_opponent_intent_returns_valid_structure(self):
        crew = FencingCrew()
        crew.start_new_match()
        intent = crew.get_opponent_intent()

        assert "action" in intent
        assert "distance" in intent
        assert intent["action"] is not None
        assert intent["distance"] in ["close", "medium", "far"]

    def test_execute_exchange_increments_counter(self):
        crew = FencingCrew()
        crew.start_new_match()

        assert crew.exchange_number == 0
        crew.execute_exchange("direct_attack", "torso")
        assert crew.exchange_number == 1
        crew.execute_exchange("fleche", "torso")
        assert crew.exchange_number == 2

    def test_execute_exchange_returns_all_required_keys(self):
        crew = FencingCrew()
        crew.start_new_match()
        result = crew.execute_exchange("direct_attack", "torso")

        assert "exchange_number" in result
        assert "fencer_action" in result
        assert "opponent_action" in result
        assert "referee_call" in result
        assert "score" in result

    def test_execute_exchange_updates_referee_score(self):
        crew = FencingCrew()
        crew.start_new_match()

        result = crew.execute_exchange("direct_attack", "torso")

        # Score may or may not change depending on opponent action,
        # but the score dict should be updated
        assert result["score"] == crew.referee.score
        assert isinstance(result["score"]["fencer"], int)
        assert isinstance(result["score"]["opponent"], int)

    def test_execute_exchange_adds_to_exchange_history(self):
        crew = FencingCrew()
        crew.start_new_match()
        initial_history_len = len(crew.referee.exchange_history)

        crew.execute_exchange("direct_attack", "torso")
        assert len(crew.referee.exchange_history) == initial_history_len + 1

    def test_referee_and_result_score_consistency(self):
        """Critical: referee.score and result['score'] must always match."""
        crew = FencingCrew()
        crew.start_new_match()

        for i in range(5):
            result = crew.execute_exchange("direct_attack", "torso")
            assert crew.referee.score == result["score"], (
                f"Inconsistent at exchange {i + 1}: referee={crew.referee.score}, result={result['score']}"
            )
            if result.get("match_over"):
                break

    def test_match_over_triggers_coach_feedback(self):
        crew = FencingCrew()
        crew.start_new_match()

        # Play until match ends
        while True:
            result = crew.execute_exchange("direct_attack", "torso")
            if result.get("match_over"):
                break

        assert "coach_feedback" in result
        assert "summary" in result["coach_feedback"]
        assert "technical" in result["coach_feedback"]
        assert "strategic" in result["coach_feedback"]
        assert "tactical" in result["coach_feedback"]
        assert "recommendations" in result["coach_feedback"]

    def test_get_current_state_returns_all_fields(self):
        crew = FencingCrew()
        crew.start_new_match()
        crew.execute_exchange("fleche", "torso")

        state = crew.get_current_state()

        assert "score" in state
        assert "exchange_count" in state
        assert "exchange_history" in state
        assert "match_over" in state
        assert state["exchange_count"] == 1

    def test_get_valid_actions_delegates_to_fencer(self):
        crew = FencingCrew()
        actions = crew.get_valid_actions()

        assert isinstance(actions, list)
        assert "direct_attack" in actions
        assert "fleche" in actions
        assert "parry_and_riposte" in actions

    def test_get_valid_targets_delegates_to_fencer(self):
        crew = FencingCrew()
        targets = crew.get_valid_targets()

        assert isinstance(targets, list)
        assert "torso" in targets


class TestFencerAgent:
    """Test the FencerAgent."""

    def test_execute_action_with_default_target(self):
        fencer = FencerAgent()
        action = fencer.execute_action("direct_attack")

        assert action["type"] == "direct_attack"
        assert action["target"] == "torso"

    def test_execute_action_with_custom_target(self):
        fencer = FencerAgent()
        action = fencer.execute_action("fleche", "back")

        assert action["type"] == "fleche"
        assert action["target"] == "back"

    def test_execute_action_appends_to_history(self):
        fencer = FencerAgent()
        assert len(fencer.action_history) == 0

        fencer.execute_action("direct_attack", "torso")
        assert len(fencer.action_history) == 1

        fencer.execute_action("fleche", "back")
        assert len(fencer.action_history) == 2

    def test_side_alternation(self):
        fencer = FencerAgent()
        fencer.execute_action("direct_attack")
        first_side = fencer.action_history[0]["side"]

        fencer.execute_action("fleche")
        second_side = fencer.action_history[1]["side"]

        assert first_side != second_side

    def test_reset_clears_history(self):
        fencer = FencerAgent()
        fencer.execute_action("direct_attack")
        fencer.execute_action("fleche")
        assert len(fencer.action_history) == 2

        fencer.reset()
        assert len(fencer.action_history) == 0

    def test_valid_actions_list(self):
        fencer = FencerAgent()
        actions = fencer.get_valid_actions()

        expected = [
            "direct_attack",
            "compound_attack",
            "fleche",
            "parry_and_riposte",
            "counter_attack",
            "remise",
            "prise_de_fer",
        ]
        assert set(actions) == set(expected)

    def test_valid_targets_list(self):
        fencer = FencerAgent()
        targets = fencer.get_valid_targets()

        assert "torso" in targets
        assert "back" in targets
        assert "shoulders" in targets


class TestOpponentAgent:
    """Test the OpponentAgent with pattern learning."""

    def test_init_exchange_resets_history(self):
        opponent = OpponentAgent()
        opponent.action_history = ["old_action"]
        opponent.init_exchange()

        assert opponent.action_history == []

    def test_execute_action_without_fencer_action(self):
        opponent = OpponentAgent()
        action = opponent.execute_action()

        assert "type" in action
        assert "target" in action
        assert action["type"] in opponent.get_valid_actions()

    def test_execute_action_with_fencer_action_learns_pattern(self):
        opponent = OpponentAgent()
        opponent.execute_action({"type": "fleche"})

        assert "fleche" in opponent.fencer_patterns
        assert opponent.pattern_counts.get("fleche") == 1

    def test_pattern_learning_accumulates(self):
        opponent = OpponentAgent()
        opponent._learn_pattern({"type": "direct_attack"})
        opponent._learn_pattern({"type": "direct_attack"})
        opponent._learn_pattern({"type": "fleche"})

        assert opponent.pattern_counts["direct_attack"] == 2
        assert opponent.pattern_counts["fleche"] == 1

    def test_exploit_weakness_mappings(self):
        opponent = OpponentAgent()

        exploit_map = {
            "direct_attack": "counter_attack",
            "fleche": "parry_and_riposte",
            "counter_attack": "compound_attack",
            "parry_and_riposte": "fleche",
            "compound_attack": "direct_attack",
        }

        for fencer_action, expected_exploit in exploit_map.items():
            opponent.pattern_counts = {fencer_action: 5}
            action = opponent._exploit_weakness(fencer_action)
            assert action["type"] == expected_exploit, (
                f"Expected exploit of {fencer_action} to be {expected_exploit}, got {action['type']}"
            )

    def test_adaptive_phase_after_exchanges(self):
        opponent = OpponentAgent()
        opponent.exchange_count = 0

        opponent.init_exchange()
        assert opponent.phase == "learning"

        opponent.exchange_count = 3
        opponent.init_exchange()
        assert opponent.phase == "adapting"

    def test_reset_clears_all_state(self):
        opponent = OpponentAgent()
        opponent.execute_action({"type": "fleche"})
        opponent.execute_action({"type": "direct_attack"})

        opponent.reset()
        assert opponent.action_history == []
        assert opponent.fencer_patterns == []
        assert opponent.pattern_counts == {}
        assert opponent.exchange_count == 0


class TestRefereeAgent:
    """Test the RefereeAgent scoring logic."""

    def test_judge_action_priority_attack_beats_parry(self):
        referee = RefereeAgent()
        result = referee.judge_action(
            {"type": "fleche", "target": "torso"}, {"type": "parry", "target": "torso"}
        )

        # Priority attack should win or tie (not lose)
        assert result["call"] in ["fencer", "simultaneous"]

    def test_judge_action_counter_against_direct(self):
        referee = RefereeAgent()
        result = referee.judge_action(
            {"type": "direct_attack", "target": "torso"},
            {"type": "counter_attack", "target": "torso"},
        )

        # Both are priority, check by index
        # Both should be valid outcomes
        assert result["call"] in ["fencer", "opponent", "simultaneous"]

    def test_valid_target_awards_score(self):
        referee = RefereeAgent()
        # Fencer has priority attack (direct_attack) to valid target,
        # opponent has secondary action (parry) to valid target
        result = referee.judge_action(
            {"type": "direct_attack", "target": "torso"},
            {"type": "parry", "target": "torso"},
        )

        # Fencer should win with valid target
        assert result["call"] == "fencer"
        assert result["fencer_score"] == 1
        assert result["opponent_score"] == 0

    def test_invalid_target_no_score(self):
        referee = RefereeAgent()
        # Fencer's fleche (priority) targets head (invalid), opponent's
        # fleche (priority) targets torso (valid) -> simultaneous, no score
        result = referee.judge_action(
            {"type": "fleche", "target": "head"},  # Invalid target
            {"type": "fleche", "target": "torso"},  # Valid target
        )

        # Simultaneous means no one scores
        assert result["call"] == "simultaneous"
        assert result["fencer_score"] == 0
        assert result["opponent_score"] == 0

    def test_invalid_target_fencer_no_score_when_opponent_wins(self):
        referee = RefereeAgent()
        # Opponent priority attack (fleche) to valid target beats
        # fencer secondary action (parry) to invalid target
        result = referee.judge_action(
            {"type": "parry", "target": "head"},  # Invalid
            {"type": "fleche", "target": "torso"},  # Valid, wins
        )

        assert result["call"] == "opponent"
        assert result["opponent_valid"] is True
        assert result["fencer_score"] == 0
        assert result["opponent_score"] == 1

    def test_score_accumulates(self):
        referee = RefereeAgent()
        initial = referee.score.copy()

        referee.judge_action(
            {"type": "fleche", "target": "torso"}, {"type": "parry", "target": "torso"}
        )
        # Score may or may not change depending on call

        current = referee.score
        total_diff = (current["fencer"] - initial["fencer"]) + (
            current["opponent"] - initial["opponent"]
        )
        # At most one point should be awarded
        assert total_diff <= 1

    def test_exchange_history_records_all_exchanges(self):
        referee = RefereeAgent()
        assert len(referee.exchange_history) == 0

        referee.judge_action(
            {"type": "direct_attack", "target": "torso"},
            {"type": "parry", "target": "torso"},
        )
        assert len(referee.exchange_history) == 1

        referee.judge_action(
            {"type": "fleche", "target": "torso"}, {"type": "fleche", "target": "torso"}
        )
        assert len(referee.exchange_history) == 2

    def test_current_call_stored(self):
        referee = RefereeAgent()
        result = referee.judge_action(
            {"type": "direct_attack", "target": "torso"},
            {"type": "parry", "target": "torso"},
        )

        assert referee.current_call is not None
        assert referee.current_call["call"] == result["call"]

    def test_reset_clears_state(self):
        referee = RefereeAgent()
        referee.judge_action(
            {"type": "fleche", "target": "torso"}, {"type": "parry", "target": "torso"}
        )
        referee.penalty_stack = ["yellow"]

        referee.reset()
        assert referee.score == {"fencer": 0, "opponent": 0}
        assert referee.penalty_stack == []
        assert referee.exchange_history == []
        assert referee.current_call is None

    def test_match_over_detection(self):
        referee = RefereeAgent()
        assert referee._is_match_over() is False

        referee.score = {"fencer": 5, "opponent": 3}
        assert referee._is_match_over() is True

        referee.score = {"fencer": 3, "opponent": 5}
        assert referee._is_match_over() is True

    def test_get_match_result_returns_winner(self):
        referee = RefereeAgent()
        referee.score = {"fencer": 5, "opponent": 3}
        result = referee.get_match_result()

        assert result["winner"] == "fencer"
        assert result["final_score"] == {"fencer": 5, "opponent": 3}

    def test_normalize_action_converts_underscores(self):
        referee = RefereeAgent()
        assert referee._normalize_action("direct_attack") == "direct-attack"
        assert referee._normalize_action("fleche") == "fleche"

    def test_get_halt_command(self):
        referee = RefereeAgent()
        command = referee.get_halt_command()

        assert command in ["Halt!", "En garde!", "Allez!", "Ecart!"]


class TestCoachAgent:
    """Test the CoachAgent analysis logic."""

    def test_analyze_exchange_empty_history_returns_error(self):
        coach = CoachAgent()
        result = coach.analyze_exchange([], {"fencer": 0, "opponent": 0})

        assert "error" in result

    def test_analyze_exchange_returns_all_feedback_types(self):
        coach = CoachAgent()
        exchange = [
            {
                "fencer_action": {"type": "direct_attack", "target": "torso"},
                "opponent_action": {"type": "counter_attack", "target": "torso"},
                "result": {"call": "fencer", "fencer_score": 1, "opponent_score": 0},
            }
        ]
        score = {"fencer": 1, "opponent": 0}

        feedback = coach.analyze_exchange(exchange, score)

        assert "summary" in feedback
        assert "technical" in feedback
        assert "strategic" in feedback
        assert "tactical" in feedback
        assert "recommendations" in feedback
        assert "score_analysis" in feedback

    def test_score_analysis_counts_correctly(self):
        coach = CoachAgent()
        exchange = [
            {"fencer_action": {}, "opponent_action": {}, "result": {"call": "fencer"}},
            {"fencer_action": {}, "opponent_action": {}, "result": {"call": "fencer"}},
            {
                "fencer_action": {},
                "opponent_action": {},
                "result": {"call": "opponent"},
            },
        ]
        score = {"fencer": 2, "opponent": 1}

        feedback = coach.analyze_exchange(exchange, score)

        assert feedback["score_analysis"]["fencer_points"] == 2
        assert feedback["score_analysis"]["opponent_points"] == 1
        assert feedback["score_analysis"]["total_rounds"] == 3

    def test_technical_feedback_for_fleche_overuse(self):
        coach = CoachAgent()
        exchange = [
            {
                "fencer_action": {"type": "fleche", "target": "torso"},
                "opponent_action": {},
                "result": {"call": "fencer"},
            },
            {
                "fencer_action": {"type": "fleche", "target": "torso"},
                "opponent_action": {},
                "result": {"call": "fencer"},
            },
            {
                "fencer_action": {"type": "fleche", "target": "torso"},
                "opponent_action": {},
                "result": {"call": "opponent"},
            },
        ]

        feedback = coach.analyze_exchange(exchange, {"fencer": 2, "opponent": 1})
        technical_text = " ".join(feedback["technical"])

        assert "fleche" in technical_text.lower()

    def test_strategic_feedback_for_limited_targets(self):
        coach = CoachAgent()
        exchange = [
            {
                "fencer_action": {"type": "direct_attack", "target": "torso"},
                "opponent_action": {},
                "result": {"call": "fencer"},
            },
            {
                "fencer_action": {"type": "direct_attack", "target": "torso"},
                "opponent_action": {},
                "result": {"call": "fencer"},
            },
            {
                "fencer_action": {"type": "direct_attack", "target": "torso"},
                "opponent_action": {},
                "result": {"call": "fencer"},
            },
            {
                "fencer_action": {"type": "direct_attack", "target": "torso"},
                "opponent_action": {},
                "result": {"call": "fencer"},
            },
            {
                "fencer_action": {"type": "direct_attack", "target": "torso"},
                "opponent_action": {},
                "result": {"call": "fencer"},
            },
            {
                "fencer_action": {"type": "direct_attack", "target": "torso"},
                "opponent_action": {},
                "result": {"call": "fencer"},
            },
        ]

        feedback = coach.analyze_exchange(exchange, {"fencer": 6, "opponent": 0})
        strategic_text = " ".join(feedback["strategic"])

        assert "target" in strategic_text.lower() or "torso" in strategic_text.lower()

    def test_tactical_feedback_for_low_win_rate(self):
        coach = CoachAgent()
        exchange = [
            {
                "fencer_action": {},
                "opponent_action": {},
                "result": {"call": "opponent"},
            },
            {
                "fencer_action": {},
                "opponent_action": {},
                "result": {"call": "opponent"},
            },
            {
                "fencer_action": {},
                "opponent_action": {},
                "result": {"call": "opponent"},
            },
        ]

        feedback = coach.analyze_exchange(exchange, {"fencer": 0, "opponent": 3})
        tactical_text = " ".join(feedback["tactical"])

        assert len(tactical_text) > 0

    def test_recommendations_for_losing_player(self):
        coach = CoachAgent()
        exchange = [
            {
                "fencer_action": {},
                "opponent_action": {},
                "result": {"call": "opponent"},
            },
            {
                "fencer_action": {},
                "opponent_action": {},
                "result": {"call": "opponent"},
            },
        ]

        feedback = coach.analyze_exchange(exchange, {"fencer": 0, "opponent": 2})

        assert len(feedback["recommendations"]) > 0

    def test_recommendations_for_winning_player(self):
        coach = CoachAgent()
        exchange = [
            {"fencer_action": {}, "opponent_action": {}, "result": {"call": "fencer"}},
            {"fencer_action": {}, "opponent_action": {}, "result": {"call": "fencer"}},
        ]

        feedback = coach.analyze_exchange(exchange, {"fencer": 2, "opponent": 0})

        assert len(feedback["recommendations"]) > 0

    def test_recommendations_include_fleche_if_not_used(self):
        coach = CoachAgent()
        exchange = [
            {
                "fencer_action": {"type": "direct_attack"},
                "opponent_action": {},
                "result": {"call": "fencer"},
            },
        ]

        feedback = coach.analyze_exchange(exchange, {"fencer": 1, "opponent": 0})

        assert any("fleche" in rec.lower() for rec in feedback["recommendations"])

    def test_feedback_history_accumulates(self):
        coach = CoachAgent()
        exchange = [
            {"fencer_action": {}, "opponent_action": {}, "result": {"call": "fencer"}}
        ]

        coach.analyze_exchange(exchange, {"fencer": 1, "opponent": 0})
        assert len(coach.feedback_history) == 1

        coach.analyze_exchange(exchange, {"fencer": 1, "opponent": 0})
        assert len(coach.feedback_history) == 2

    def test_reset_clears_history(self):
        coach = CoachAgent()
        coach.feedback_history = ["old_feedback"]

        coach.reset()
        assert coach.feedback_history == []


class TestRightOfWayRules:
    """Test right-of-way priority rules."""

    def test_priority_action_beats_secondary(self):
        referee = RefereeAgent()
        # Priority actions vs secondary actions
        result = referee.judge_action(
            {"type": "direct_attack", "target": "torso"},
            {"type": "parry", "target": "torso"},
        )
        assert result["call"] == "fencer"

    def test_both_priority_uses_index_order(self):
        referee = RefereeAgent()
        # Both priority - direct_attack (index 0) beats compound_attack (index 1)
        result = referee.judge_action(
            {"type": "direct_attack", "target": "torso"},
            {"type": "compound_attack", "target": "torso"},
        )
        assert result["call"] == "fencer"

    def test_simultaneous_both_same_priority(self):
        referee = RefereeAgent()
        # Same action type
        result = referee.judge_action(
            {"type": "fleche", "target": "torso"}, {"type": "fleche", "target": "torso"}
        )
        assert result["call"] == "simultaneous"

    def test_prise_de_fer_priority(self):
        referee = RefereeAgent()
        result = referee.judge_action(
            {"type": "prise_de_fer", "target": "torso"},
            {"type": "parry", "target": "torso"},
        )
        assert result["call"] in ["fencer", "simultaneous"]


class TestEndToEndMatch:
    """End-to-end match scenarios."""

    def test_full_match_plays_to_completion(self):
        crew = FencingCrew()
        crew.start_new_match()

        exchanges = 0
        while True:
            result = crew.execute_exchange("direct_attack", "torso")
            exchanges += 1

            if result.get("match_over"):
                break

            # Safety valve to prevent infinite loop
            assert exchanges < 20, "Match did not complete in 20 exchanges"

        assert result["match_over"] is True
        assert "match_result" in result
        assert "coach_feedback" in result

    def test_score_at_match_end_is_correct(self):
        crew = FencingCrew()
        crew.start_new_match()

        final_result = None
        while True:
            result = crew.execute_exchange("fleche", "torso")
            if result.get("match_over"):
                final_result = result
                break

        final_score = crew.referee.score
        match_result = final_result["match_result"]["final_score"]

        assert final_score == match_result

    def test_multiple_matches_can_be_played(self):
        crew = FencingCrew()
        crew.start_new_match()

        # Play first match
        while True:
            result = crew.execute_exchange("direct_attack", "torso")
            if result.get("match_over"):
                break

        # Start second match
        result = crew.start_new_match()
        assert result["status"] == "match_started"
        assert crew.referee.score == {"fencer": 0, "opponent": 0}
        assert crew.exchange_number == 0
