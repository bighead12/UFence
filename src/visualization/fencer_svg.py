import streamlit as st
from typing import Optional


class FencerVisualizer:
    def __init__(self):
        self.animation_state = "idle"
        self.last_result = None
        self.score = {"fencer": 0, "opponent": 0}

    def set_score(self, score: dict):
        self.score = score

    def set_animation_state(self, state: str, result: Optional[dict] = None):
        self.animation_state = state
        self.last_result = result


def render_fencer_arena(distance: str, opponent_action: dict, score: dict, last_result: dict = None):
    distance_symbols = {
        "far": "━━━━━━━",
        "medium": "━━━━━",
        "close": "━━━"
    }

    action_icons = {
        "direct_attack": "🗡️",
        "compound_attack": "🔱",
        "fleche": "🏃",
        "parry_and_riposte": "🛡️",
        "counter_attack": "⚡",
        "remise": "↩️",
        "prise_de_fer": "✋"
    }

    action_name = "unknown"
    if opponent_action:
        action_name = opponent_action.get("type", "unknown")
        action_icon = action_icons.get(action_name, "⚔️")
    else:
        action_icon = "⚔️"

    col1, col2, col3 = st.columns([1, 3, 1])

    with col1:
        st.markdown("### 🔵 **YOU**")
        st.metric("Score", score['fencer'])

    with col2:
        with st.container(border=True):
            st.markdown("### ⚔️ FENCING ARENA")

            st.markdown(f"""
            <div style="background:#1a1a2e; padding:20px; border-radius:15px; text-align:center; margin:10px 0;">
                <div style="font-size:60px; color:#3B82F6; display:inline-block; transform: scaleX(-1);">🤺</div>
                <span style="font-size:30px; color:white; margin:0 15px;">{distance_symbols.get(distance, '━━━━━')}</span>
                <div style="font-size:60px; color:#EF4444; display:inline-block;">🤺</div>
                <div style="margin-top:15px; font-size:14px; color:#888;">
                    📏 Distance: {distance.title()} | {action_icon} Opponent: {action_name.replace('_', ' ').title()}
                </div>
            </div>
            """, unsafe_allow_html=True)

            if last_result:
                call = last_result.get("call", "simultaneous")
                if call == "fencer":
                    st.success("✅ You scored!")
                elif call == "opponent":
                    st.error("❌ Opponent scored!")
                else:
                    st.warning("⭕ Simultaneous - no score")

    with col3:
        st.markdown("### 🔴 **OPPONENT**")
        st.metric("Score", score['opponent'])

    return FencerVisualizer()