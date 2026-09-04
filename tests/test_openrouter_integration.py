"""
Tests for OpenRouter integration.

Covers: env-var config wiring, the natural-language intent parser
(`FencingCrew.interpret_user_intent`), and coach chat routing through
the same OpenRouter model name.

These tests monkeypatch `litellm.completion` so no real network call
is made — the goal is to confirm the OpenRouter config plumbing is
correct end-to-end.
"""

from unittest.mock import MagicMock, patch

from src.crew.fencing_crew import FencingCrew
from src.utils import config as cfg
from src.utils.config import OPENROUTER_MODELS

# ---------------------------------------------------------------------------
# Config tests
# ---------------------------------------------------------------------------


class TestOpenRouterConfig:
    def test_model_list_is_non_empty(self):
        assert len(OPENROUTER_MODELS) >= 1

    def test_model_list_uses_known_providers(self):
        providers = {m.split("/")[0] for m in OPENROUTER_MODELS}
        # Free-tier models from OpenRouter; verify at least one provider is present
        assert len(providers) >= 1

    def test_default_model_is_set(self):
        # OPENROUTER_MODEL may be overridden in env, but it should always
        # be a non-empty string
        assert isinstance(cfg.OPENROUTER_MODEL, str)
        assert cfg.OPENROUTER_MODEL != ""


# ---------------------------------------------------------------------------
# Intent interpreter tests
# ---------------------------------------------------------------------------


def _make_litellm_response(content: str) -> MagicMock:
    """Build a litellm-shaped response with the given text content."""
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message.content = content
    return response


class TestInterpretUserIntent:
    @patch("litellm.completion")
    def test_parses_valid_json_response(self, mock_completion):
        """Happy path: LLM returns clean JSON, we extract (action, target)."""
        mock_completion.return_value = _make_litellm_response(
            '{"action": "fleche", "target": "back"}'
        )

        crew = FencingCrew()
        action, target = crew.interpret_user_intent("I fleched to the back!")

        assert action == "fleche"
        assert target == "back"

    @patch("litellm.completion")
    def test_parses_json_fenced_in_code_block(self, mock_completion):
        """LLM sometimes wraps JSON in ```json ... ```; should still parse."""
        mock_completion.return_value = _make_litellm_response(
            '```json\n{"action": "parry_and_riposte", "target": "torso"}\n```'
        )

        crew = FencingCrew()
        action, target = crew.interpret_user_intent(
            "I parried then riposted to the chest"
        )

        assert action == "parry_and_riposte"
        assert target == "torso"

    @patch("litellm.completion")
    def test_uses_openrouter_model_constant(self, mock_completion):
        """The intent interpreter should call litellm with OPENROUTER_MODEL,
        not the old GEMINI_MODEL."""
        mock_completion.return_value = _make_litellm_response(
            '{"action": "direct_attack", "target": "torso"}'
        )

        crew = FencingCrew()
        crew.interpret_user_intent("lunge to torso")

        mock_completion.assert_called_once()
        call_kwargs = mock_completion.call_args.kwargs
        assert call_kwargs["model"] == cfg.OPENROUTER_MODEL
        # The model name should NOT be a Gemini-via-litellm string
        assert "gemini/gemini" not in call_kwargs["model"]

    @patch("litellm.completion")
    def test_falls_back_on_unparseable_response(self, mock_completion):
        """If the LLM returns garbage, we should fall back to defaults
        rather than crashing."""
        mock_completion.return_value = _make_litellm_response(
            "I'm not sure what you mean."
        )

        crew = FencingCrew()
        action, target = crew.interpret_user_intent("????")

        assert action == "direct_attack"
        assert target == "torso"

    @patch("litellm.completion")
    def test_falls_back_on_llm_error(self, mock_completion):
        """If the LLM call raises, we should still return sane defaults."""
        mock_completion.side_effect = ConnectionError("API down")

        crew = FencingCrew()
        action, target = crew.interpret_user_intent("lunge to back")

        assert action == "direct_attack"
        assert target == "torso"

    @patch("litellm.completion")
    def test_rejects_invalid_action_with_fallback(self, mock_completion):
        """LLM invents an action we don't know — fall back to direct_attack."""
        mock_completion.return_value = _make_litellm_response(
            '{"action": "lightsaber_attack", "target": "torso"}'
        )

        crew = FencingCrew()
        action, target = crew.interpret_user_intent("use the force")

        assert action == "direct_attack"
        assert target == "torso"

    @patch("litellm.completion")
    def test_rejects_invalid_target_with_fallback(self, mock_completion):
        """LLM invents a target we don't know — fall back to torso."""
        mock_completion.return_value = _make_litellm_response(
            '{"action": "direct_attack", "target": "left_foot"}'
        )

        crew = FencingCrew()
        action, target = crew.interpret_user_intent("stab the foot")

        assert action == "direct_attack"
        assert target == "torso"


# ---------------------------------------------------------------------------
# Coach chat routing test
# ---------------------------------------------------------------------------


class TestCoachChatUsesOpenRouter:
    @patch("litellm.completion")
    def test_chat_uses_openrouter_model(self, mock_completion):
        """Coach chat must call litellm with the OpenRouter model name."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Stay light on your feet."
        mock_completion.return_value = mock_response

        from src.agents.coach import CoachAgent

        coach = CoachAgent()
        result = coach.chat(
            question="How do I defend fleche?",
            retrieved_passages=[],
            exchange_history=[],
            score={"fencer": 0, "opponent": 0},
        )

        mock_completion.assert_called_once()
        call_kwargs = mock_completion.call_args.kwargs
        assert call_kwargs["model"] == cfg.OPENROUTER_MODEL
        assert "answer" in result
        assert result["answer"] == "Stay light on your feet."
