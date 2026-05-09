import streamlit as st


CSS_KEYFRAMES = """
<style>
@keyframes thrust-right {
    0% { transform: translateX(0); }
    25% { transform: translateX(30px); }
    50% { transform: translateX(50px); }
    75% { transform: translateX(30px); }
    100% { transform: translateX(0); }
}
@keyframes thrust-left {
    0% { transform: translateX(0) scaleX(-1); }
    25% { transform: translateX(-30px) scaleX(-1); }
    50% { transform: translateX(-50px) scaleX(-1); }
    75% { transform: translateX(-30px) scaleX(-1); }
    100% { transform: translateX(0) scaleX(-1); }
}
@keyframes fleche-run {
    0% { transform: translateX(0); }
    30% { transform: translateX(60px); }
    60% { transform: translateX(100px); }
    80% { transform: translateX(80px); }
    100% { transform: translateX(0); }
}
@keyframes parry-deflect {
    0%, 100% { transform: translateX(0); }
    25% { transform: translateX(-15px) rotate(-20deg); }
    75% { transform: translateX(15px) rotate(20deg); }
}
@keyframes counter-quick {
    0% { transform: translateX(0); }
    20% { transform: translateX(40px); }
    40% { transform: translateX(0); }
    60% { transform: translateX(0); }
    80% { transform: translateX(-40px); }
    100% { transform: translateX(0); }
}
@keyframes remise-push {
    0% { transform: translateX(0); }
    50% { transform: translateX(25px); }
    100% { transform: translateX(0); }
}
@keyframes prise-grab {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.2); }
}
@keyframes score-flash-green {
    0%, 100% { background-color: #10B981; opacity: 1; }
    50% { background-color: #34D399; opacity: 0.7; }
}
@keyframes score-flash-red {
    0%, 100% { background-color: #EF4444; opacity: 1; }
    50% { background-color: #F87171; opacity: 0.7; }
}
@keyframes score-flash-yellow {
    0%, 100% { background-color: #FBBF24; opacity: 1; }
    50% { background-color: #FCD34D; opacity: 0.7; }
}
@keyframes pulse-glow {
    0%, 100% { transform: scale(1); filter: brightness(1); }
    50% { transform: scale(1.1); filter: brightness(1.2); }
}
@keyframes shake {
    0%, 100% { transform: translateX(0); }
    25% { transform: translateX(-5px); }
    75% { transform: translateX(5px); }
}
@keyframes bounce {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-10px); }
}
.fencer-left {
    animation: thrust-right 1s ease-in-out;
}
.fencer-right {
    animation: thrust-left 1s ease-in-out;
}
.action-emoji {
    animation: pulse-glow 0.5s ease-in-out infinite;
}
</style>
"""


ACTION_ANIMATIONS = {
    "direct_attack": {
        "emoji": "🗡️",
        "your_animation": "fencer-left",
        "opp_animation": "fencer-right",
        "name": "Direct Attack"
    },
    "compound_attack": {
        "emoji": "🔱",
        "your_animation": "fencer-left",
        "opp_animation": "fencer-right",
        "name": "Compound Attack"
    },
    "fleche": {
        "emoji": "🏃",
        "your_animation": "fleche-run",
        "opp_animation": "parry-deflect",
        "name": "Fleche"
    },
    "parry_and_riposte": {
        "emoji": "🛡️",
        "your_animation": "parry-deflect",
        "opp_animation": "fencer-left",
        "name": "Parry & Riposte"
    },
    "counter_attack": {
        "emoji": "⚡",
        "your_animation": "counter-quick",
        "opp_animation": "counter-quick",
        "name": "Counter-Attack"
    },
    "remise": {
        "emoji": "↩️",
        "your_animation": "remise-push",
        "opp_animation": "fencer-left",
        "name": "Remise"
    },
    "prise_de_fer": {
        "emoji": "✋",
        "your_animation": "prise-grab",
        "opp_animation": "prise-grab",
        "name": "Prise de Fer"
    }
}


def get_action_animation(action_type: str) -> dict:
    return ACTION_ANIMATIONS.get(action_type, {
        "emoji": "⚔️",
        "your_animation": "fencer-left",
        "opp_animation": "fencer-right",
        "name": "Unknown"
    })


def render_animation_sequence(fencer_action: str, opponent_action: str, call_result: str) -> str:
    fencer_anim = get_action_animation(fencer_action)
    opponent_anim = get_action_animation(opponent_action)

    result_colors = {
        "fencer": ("score-flash-green", "✅ YOU SCORED!"),
        "opponent": ("score-flash-red", "❌ OPPONENT SCORED!"),
        "simultaneous": ("score-flash-yellow", "⭕ SIMULTANEOUS")
    }

    flash_class, result_text = result_colors.get(call_result, ("score-flash-yellow", "❓"))

    html = f"""
    {CSS_KEYFRAMES}
    <div style="text-align: center; padding: 20px;">
        <div style="margin-bottom: 20px;">
            <span style="font-size: 50px; display: inline-block; animation: thrust-right 1s ease-in-out;">
                🤺
            </span>
            <span style="font-size: 40px; margin: 0 20px; color: #888;">
                ⚔️
            </span>
            <span style="font-size: 50px; display: inline-block; animation: thrust-left 1s ease-in-out;">
                🤺
            </span>
        </div>
        <div style="background: linear-gradient(135deg, #1a1a2e, #2d2d4a); padding: 20px; border-radius: 15px; border: 2px solid #3B82F6;">
            <div style="font-size: 60px; margin-bottom: 10px;">
                {fencer_anim['emoji']} ⚔️ {opponent_anim['emoji']}
            </div>
            <div style="color: #ccc; font-size: 16px;">
                {fencer_anim['name']} vs {opponent_anim['name']}
            </div>
        </div>
        <div class="{flash_class}" style="margin-top: 20px; padding: 15px 30px; border-radius: 10px; font-size: 24px; font-weight: bold; color: white;">
            {result_text}
        </div>
    </div>
    """
    return html


def render_engaging_animation() -> str:
    return f"""
    {CSS_KEYFRAMES}
    <div style="text-align: center; padding: 40px;">
        <div style="font-size: 80px; animation: pulse-glow 1s ease-in-out infinite;">
            ⚔️
        </div>
        <div style="font-size: 24px; color: #3B82F6; margin-top: 20px; font-weight: bold;">
            FENCERS ENGAGE!
        </div>
    </div>
    """


def render_action_animation(your_action: str, opp_action: str) -> str:
    your_anim = get_action_animation(your_action)
    opp_anim = get_action_animation(opp_action)

    return f"""
    {CSS_KEYFRAMES}
    <div style="text-align: center; padding: 30px; background: linear-gradient(135deg, #1a1a2e, #2d2d4a); border-radius: 20px; margin: 10px 0;">
        <div style="margin-bottom: 15px;">
            <span style="font-size: 60px; animation: thrust-right 0.8s ease-in-out; display: inline-block;">
                🤺
            </span>
            <span style="font-size: 20px; color: #888; margin: 0 15px;">
                → ⚔️ ←
            </span>
            <span style="font-size: 60px; animation: thrust-left 0.8s ease-in-out; display: inline-block;">
                🤺
            </span>
        </div>
        <div style="display: flex; justify-content: center; gap: 40px; font-size: 50px;">
            <div style="animation: pulse-glow 0.5s infinite;">
                {your_anim['emoji']}
            </div>
            <div style="color: #666;">vs</div>
            <div style="animation: pulse-glow 0.5s infinite;">
                {opp_anim['emoji']}
            </div>
        </div>
        <div style="color: #888; font-size: 14px; margin-top: 15px;">
            {your_anim['name']} ⚔️ {opp_anim['name']}
        </div>
    </div>
    """


def render_result_animation(call_result: str, your_score: int, opp_score: int) -> str:
    result_data = {
        "fencer": {
            "emoji": "✅",
            "class": "score-flash-green",
            "text": f"YOU SCORED! {your_score}-{opp_score}"
        },
        "opponent": {
            "emoji": "❌",
            "class": "score-flash-red",
            "text": f"OPPONENT SCORED! {your_score}-{opp_score}"
        },
        "simultaneous": {
            "emoji": "⭕",
            "class": "score-flash-yellow",
            "text": f"SIMULTANEOUS! {your_score}-{opp_score}"
        }
    }

    result = result_data.get(call_result, result_data["simultaneous"])

    return f"""
    {CSS_KEYFRAMES}
    <div style="text-align: center; padding: 30px;">
        <div style="font-size: 80px; animation: bounce 0.5s ease-in-out; margin-bottom: 15px;">
            {result['emoji']}
        </div>
        <div class="{result['class']}" style="padding: 20px 40px; border-radius: 15px; font-size: 28px; font-weight: bold; color: white;">
            {result['text']}
        </div>
    </div>
    """


def render_complete_animation(fencer_action: str, opponent_action: str, call_result: str, your_score: int, opp_score: int) -> str:
    return f"""
    {CSS_KEYFRAMES}
    <div style="text-align: center; padding: 20px;">
        <div style="margin-bottom: 20px;">
            <span style="font-size: 60px; animation: thrust-right 1s ease-in-out; display: inline-block;">
                🤺
            </span>
            <span style="font-size: 40px; margin: 0 20px;">⚔️</span>
            <span style="font-size: 60px; animation: thrust-left 1s ease-in-out; display: inline-block;">
                🤺
            </span>
        </div>
        <div style="background: linear-gradient(135deg, #1a1a2e, #2d2d4a); padding: 25px; border-radius: 15px; margin-bottom: 15px;">
            <div style="font-size: 40px; margin-bottom: 10px;">
                {get_action_animation(fencer_action)['emoji']} vs {get_action_animation(opponent_action)['emoji']}
            </div>
            <div style="color: #aaa; font-size: 14px;">
                {get_action_animation(fencer_action)['name']} vs {get_action_animation(opponent_action)['name']}
            </div>
        </div>
    </div>
    """