import streamlit as st
import matplotlib.pyplot as plt
from typing import List, Dict


class HistoryPanel:
    def __init__(self):
        self.exchanges = []

    def add_exchange(self, exchange_num: int, fencer_action: str, opponent_action: str, result: dict):
        self.exchanges.append({
            "exchange": exchange_num,
            "your_action": fencer_action.replace("_", " ").title(),
            "opponent_action": opponent_action.replace("_", " ").title(),
            "call": result.get("call", "unknown"),
            "you_scored": result.get("fencer_score", 0),
            "opp_scored": result.get("opponent_score", 0)
        })

    def get_timeline(self) -> List[Dict]:
        return self.exchanges

    def get_score_history(self) -> Dict:
        you_scores = []
        opp_scores = []
        cumulative_you = 0
        cumulative_opp = 0

        for ex in self.exchanges:
            cumulative_you += ex["you_scored"]
            cumulative_opp += ex["opp_scored"]
            you_scores.append(cumulative_you)
            opp_scores.append(cumulative_opp)

        return {"you": you_scores, "opponent": opp_scores}

    def render_timeline(self):
        if not self.exchanges:
            st.info("No exchanges yet!")
            return

        st.markdown("### 📜 Exchange History")

        for ex in self.exchanges[-5:]:
            with st.expander(f"Exchange #{ex['exchange']}", expanded=False):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.markdown(f"**🔵 You:** {ex['your_action']}")
                    if ex['you_scored']:
                        st.success("✓ Scored!")

                with col2:
                    call_emoji = "✅" if ex['call'] == 'fencer' else "❌" if ex['call'] == 'opponent' else "⭕"
                    st.markdown(f"**Call:** {call_emoji} {ex['call'].title()}")

                with col3:
                    st.markdown(f"**🔴 Opp:** {ex['opponent_action']}")
                    if ex['opp_scored']:
                        st.error("✗ Scored!")

    def render_score_chart(self):
        if not self.exchanges:
            return

        score_data = self.get_score_history()

        if not score_data["you"]:
            return

        fig, ax = plt.subplots(figsize=(8, 4))

        exchanges = list(range(1, len(score_data["you"]) + 1))

        ax.plot(exchanges, score_data["you"], 'b-o', label='You', linewidth=2, markersize=8)
        ax.plot(exchanges, score_data["opponent"], 'r-s', label='Opponent', linewidth=2, markersize=8)

        ax.set_xlabel('Exchange Number')
        ax.set_ylabel('Score')
        ax.set_title('Score Progression')
        ax.legend()
        ax.grid(True, alpha=0.3)

        ax.set_ylim(0, max(max(score_data["you"]), max(score_data["opponent"]), 5) + 1)

        st.pyplot(fig)

    def render_stats(self):
        if not self.exchanges:
            return

        total = len(self.exchanges)
        your_wins = sum(1 for ex in self.exchanges if ex["you_scored"])
        opp_wins = sum(1 for ex in self.exchanges if ex["opp_scored"])
        total - your_wins - opp_wins

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Exchanges", total)
        with col2:
            st.metric("Your Wins", your_wins)
        with col3:
            st.metric("Opponent Wins", opp_wins)
        with col4:
            win_rate = (your_wins / total * 100) if total > 0 else 0
            st.metric("Win Rate", f"{win_rate:.0f}%")

    def clear(self):
        self.exchanges = []


def render_history_panel(exchange_results: List[dict]):
    panel = HistoryPanel()

    for result in exchange_results:
        panel.add_exchange(
            result.get("exchange_number", 0),
            result.get("fencer_action", {}).get("type", ""),
            result.get("opponent_action", {}).get("type", ""),
            result.get("referee_call", {})
        )

    col1, col2 = st.columns([2, 1])

    with col1:
        panel.render_timeline()

    with col2:
        panel.render_stats()

    st.markdown("### 📈 Score Progression")
    panel.render_score_chart()

    return panel