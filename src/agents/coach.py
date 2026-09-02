from typing import List
from src.utils.logging import get_logger

logger = get_logger(__name__)


class CoachAgent:
    def __init__(self):
        self.feedback_history = []

    def analyze_exchange(self, exchange_history: List[dict], score: dict) -> dict:
        if not exchange_history:
            return {"error": "No exchange data to analyze"}

        fencer_actions = [h["fencer_action"] for h in exchange_history]
        referee_calls = [h["result"]["call"] for h in exchange_history]

        fencer_wins = referee_calls.count("fencer")
        opponent_wins = referee_calls.count("opponent")
        ties = referee_calls.count("simultaneous")

        feedback = {
            "summary": self._generate_summary(score, fencer_wins, opponent_wins),
            "technical": self._analyze_technical(fencer_actions),
            "strategic": self._analyze_strategic(fencer_actions),
            "tactical": self._analyze_tactical(fencer_actions, referee_calls),
            "recommendations": self._generate_recommendations(fencer_actions, fencer_wins, opponent_wins),
            "score_analysis": {
                "fencer_points": fencer_wins,
                "opponent_points": opponent_wins,
                "ties": ties,
                "total_rounds": len(exchange_history)
            }
        }

        self.feedback_history.append(feedback)
        logger.info(f"Coach provided feedback: {feedback['summary']}")
        return feedback

    def _generate_summary(self, score: dict, fencer_wins: int, opponent_wins: int) -> str:
        winner = "You" if score["fencer"] > score["opponent"] else "Opponent"
        return f"Match ended {score['fencer']}-{score['opponent']}. {winner} won. You scored {fencer_wins} out of {fencer_wins + opponent_wins} decisions."

    def _analyze_technical(self, fencer_actions: List[dict]) -> List[str]:
        feedback = []
        action_types = [a.get("type", "") for a in fencer_actions]

        if action_types.count("fleche") > len(fencer_actions) * 0.3:
            feedback.append("Over-reliance on fleche attacks. Consider varying your attack patterns.")

        if action_types.count("direct_attack") > len(fencer_actions) * 0.5:
            feedback.append("Too predictable with direct attacks. Add compound attacks to keep opponent guessing.")

        parry_riposte_count = action_types.count("parry_and_riposte")
        if parry_riposte_count == 0:
            feedback.append("No defensive ripostes observed. Work on parry-riposte combinations.")

        if action_types.count("counter_attack") > 2:
            feedback.append("Good counter-attack instincts, but ensure proper distance management.")

        if not feedback:
            feedback.append("Good variety in technical actions. Continue practicing all attack types.")
        return feedback

    def _analyze_strategic(self, fencer_actions: List[dict]) -> List[str]:
        feedback = []
        targets = [a.get("target", "") for a in fencer_actions]

        if targets.count("torso") > len(fencer_actions) * 0.7:
            feedback.append("Target selection is limited. Experiment with back and shoulder targets.")

        if len(set(targets)) == 1:
            feedback.append("Your target patterns are highly predictable. Add more variety.")

        side_changes = sum(1 for i in range(1, len(fencer_actions))
                          if fencer_actions[i].get("side") != fencer_actions[i-1].get("side"))

        if side_changes == 0 and len(fencer_actions) > 2:
            feedback.append("No lateral movement observed. Work on changing lines of attack.")

        if not feedback:
            feedback.append("Good strategic awareness in target selection.")
        return feedback

    def _analyze_tactical(self, fencer_actions: List[dict], referee_calls: List[str]) -> List[str]:
        feedback = []
        action_types = [a.get("type", "") for a in fencer_actions]

        fencer_wins = referee_calls.count("fencer")
        win_rate = fencer_wins / len(referee_calls) if referee_calls else 0

        if win_rate < 0.4:
            feedback.append("Low success rate. Focus on high-percentage actions like direct attacks.")

        compound_count = action_types.count("compound_attack")
        if compound_count == 0 and len(fencer_actions) < 4:
            feedback.append("Consider using compound attacks to set up opportunities.")

        simultaneous = referee_calls.count("both")
        if simultaneous > len(referee_calls) * 0.3:
            feedback.append("Too many simultaneous hits. Improve your reaction time and distance control.")

        priority_actions = ["fleche", "direct_attack", "counter_attack"]
        priority_count = sum(1 for a in action_types if a in priority_actions)
        if priority_count < len(action_types) * 0.5:
            feedback.append("Focus on priority actions that establish right of way.")

        if not feedback:
            feedback.append("Strong tactical execution. Your decision-making was solid.")
        return feedback

    def _generate_recommendations(self, fencer_actions: List[dict], fencer_wins: int, opponent_wins: int) -> List[str]:
        recommendations = []

        if fencer_wins < opponent_wins:
            recommendations.extend([
                "Practice attack combinations to improve scoring efficiency",
                "Work on parry-riposte timing with your coach",
                "Review match footage to identify tactical patterns"
            ])
        else:
            recommendations.extend([
                "Maintain current form but add more variety to your attack arsenal",
                "Continue working on distance and timing",
                "Consider adding more compound attacks to become less predictable"
            ])

        action_types = [a.get("type", "") for a in fencer_actions]
        if "fleche" not in action_types:
            recommendations.append("Add fleche to your arsenal for closing distance")

        return recommendations[:5]

    def reset(self):
        self.feedback_history = []