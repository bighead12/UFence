from typing import List
from src.utils.logging import get_logger

logger = get_logger(__name__)


class CoachAgent:
    def __init__(self):
        self.feedback_history = []
        self.chat_history = []

    def analyze_exchange(self, exchange_history: List[dict], score: dict) -> dict:
        if not exchange_history:
            return {"error": "No exchange data to analyze"}

        fencer_actions = [h["fencer_action"] for h in exchange_history]
        referee_calls = [h["result"]["call"] for h in exchange_history]

        fencer_wins = referee_calls.count("fencer")
        opponent_wins = referee_calls.count("opponent")
        ties = referee_calls.count("both")

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
        self.chat_history = []

    def chat(
        self,
        question: str,
        retrieved_passages: list,
        exchange_history: list,
        score: dict,
    ) -> dict:
        """
        Answer an athlete's question using RAG context and match data.

        Returns a dict with:
        - answer: The coach's response text
        - sources: List of source references used
        """
        from src.knowledge.retriever import BookRetriever

        # Format retrieved book passages
        retriever = BookRetriever()
        passages_text = retriever.format_passages_for_prompt(retrieved_passages)

        # Summarize match context
        match_context = self._build_match_context(exchange_history, score)

        # Summarize any existing feedback
        feedback_summary = ""
        if self.feedback_history:
            latest = self.feedback_history[-1]
            feedback_summary = (
                f"Latest coach feedback summary: {latest.get('summary', 'N/A')}\n"
                f"Technical notes: {', '.join(latest.get('technical', []))}\n"
                f"Tactical notes: {', '.join(latest.get('tactical', []))}\n"
            )

        # Build the conversation history for multi-turn support
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert fencing coach with deep knowledge of foil fencing "
                    "technique, strategy, and rules. You are speaking with your athlete "
                    "after a training match.\n\n"
                    "Use the provided REFERENCE MATERIAL from fencing books to support "
                    "your answers. Cite the book name when referencing specific material.\n"
                    "Also use the MATCH CONTEXT to tie your advice to what actually "
                    "happened in the current match.\n\n"
                    "Be specific, encouraging, and instructive. Use fencing terminology "
                    "correctly. Keep answers focused and actionable.\n\n"
                    f"REFERENCE MATERIAL:\n{passages_text}\n\n"
                    f"MATCH CONTEXT:\n{match_context}\n\n"
                    f"{feedback_summary}"
                ),
            }
        ]

        # Include prior chat turns for conversational continuity
        for turn in self.chat_history[-6:]:  # Last 3 exchanges (6 messages)
            messages.append(turn)

        messages.append({"role": "user", "content": question})

        # Call LLM
        try:
            import litellm
            from src.utils.config import OLLAMA_MODEL, OLLAMA_BASE_URL

            response = litellm.completion(
                model=f"ollama/{OLLAMA_MODEL}",
                messages=messages,
                api_base=OLLAMA_BASE_URL,
                max_tokens=800,
            )
            answer = response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Coach chat LLM error: {e}")
            answer = (
                "I'm having trouble connecting right now. "
                "Please check that Ollama is running and try again."
            )

        # Extract source citations
        sources = []
        seen = set()
        for p in retrieved_passages:
            key = f"{p['source']}_p{p.get('page', 0)}"
            if key not in seen:
                sources.append({
                    "source": p["source"],
                    "page": p.get("page", 0),
                })
                seen.add(key)

        # Store in chat history for multi-turn
        self.chat_history.append({"role": "user", "content": question})
        self.chat_history.append({"role": "assistant", "content": answer})

        logger.info(f"Coach answered question: {question[:50]}...")
        return {"answer": answer, "sources": sources}

    def _build_match_context(self, exchange_history: list, score: dict) -> str:
        """Summarize match state for the LLM prompt."""
        if not exchange_history:
            return "No match data available yet."

        lines = [
            f"Current score: You {score.get('fencer', 0)} - "
            f"Opponent {score.get('opponent', 0)}",
            f"Total exchanges: {len(exchange_history)}",
            "",
            "Recent exchanges:",
        ]

        # Show last 5 exchanges
        for i, ex in enumerate(exchange_history[-5:], start=1):
            fa = ex.get("fencer_action", {})
            oa = ex.get("opponent_action", {})
            result = ex.get("result", {})
            call = result.get("call", "unknown")
            lines.append(
                f"  {i}. You: {fa.get('type', '?')} → {fa.get('target', '?')} | "
                f"Opponent: {oa.get('type', '?')} → {oa.get('target', '?')} | "
                f"Result: {call}"
            )

        return "\n".join(lines)