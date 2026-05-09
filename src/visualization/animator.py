import streamlit as st
import time


class Animator:
    def __init__(self):
        self.animation_duration = 1.5
        self.last_animation_time = None

    def animate_exchange(self, fencer_action: str, opponent_action: str, result: dict):
        placeholder = st.empty()

        steps = [
            ("⚔️", "Fencers engage...", 0.3),
            ("💥", f"Your {fencer_action.replace('_', ' ').title()} vs {opponent_action.replace('_', ' ').title()}", 0.5),
            (self._get_result_emoji(result["call"]), self._get_result_text(result), 0.7),
        ]

        for emoji, text, delay in steps:
            with placeholder.container():
                st.markdown(f"""
                <div style="text-align: center; padding: 20px; animation: pulse 1s infinite;">
                    <h1 style="font-size: 48px;">{emoji}</h1>
                    <p style="font-size: 18px; color: white;">{text}</p>
                </div>
                """, unsafe_allow_html=True)
            time.sleep(delay)

        placeholder.empty()

    def _get_result_emoji(self, call: str) -> str:
        emojis = {
            "fencer": "✅",
            "opponent": "❌",
            "simultaneous": "⭕",
            "both": "🔄"
        }
        return emojis.get(call, "❓")

    def _get_result_text(self, result: dict) -> str:
        if result.get("fencer_score"):
            return f"You scored! Score: {result['score']['fencer']}-{result['score']['opponent']}"
        elif result.get("opponent_score"):
            return f"Opponent scored! Score: {result['score']['fencer']}-{result['score']['opponent']}"
        else:
            return f"Simultaneous! No score. Score: {result['score']['fencer']}-{result['score']['opponent']}"


def render_animation_step(phase: str, data: dict):
    animations = {
        "engaging": {
            "emoji": "⚔️",
            "text": "Fencers engaging...",
            "color": "#3B82F6"
        },
        "action": {
            "emoji": "💥",
            "text": f"{data.get('fencer_action', 'Attack')} vs {data.get('opponent_action', 'Attack')}",
            "color": "#EF4444"
        },
        "result": {
            "emoji": data.get("result_emoji", "🏆"),
            "text": data.get("result_text", "Exchange complete"),
            "color": "#10B981"
        }
    }

    anim = animations.get(phase, animations["engaging"])

    st.markdown(f"""
    <div style="
        text-align: center;
        padding: 30px;
        background: linear-gradient(135deg, {anim['color']}22, {anim['color']}44);
        border-radius: 15px;
        border: 2px solid {anim['color']};
        animation: pulse 1s infinite;
    ">
        <h1 style="font-size: 64px; margin: 0;">{anim['emoji']}</h1>
        <p style="font-size: 20px; color: white; margin: 10px 0 0 0;">{anim['text']}</p>
    </div>
    """, unsafe_allow_html=True)


def create_action_icon(action_type: str) -> str:
    icons = {
        "direct_attack": "🗡️",
        "compound_attack": "🔱",
        "fleche": "🏃",
        "parry_and_riposte": "🛡️",
        "counter_attack": "⚡",
        "remise": "↩️",
        "prise_de_fer": "✋"
    }
    return icons.get(action_type, "❓")