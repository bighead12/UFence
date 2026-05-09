import streamlit as st
import random
from typing import Optional


class FencerVisualizer:
    FENCER_COLOR = "#3B82F6"
    OPPONENT_COLOR = "#EF4444"
    PISTE_COLOR = "#1E3A5F"
    LINE_COLOR = "#FFFFFF"

    def __init__(self):
        self.animation_state = "idle"
        self.last_result = None
        self.score = {"fencer": 0, "opponent": 0}

    def set_score(self, score: dict):
        self.score = score

    def set_animation_state(self, state: str, result: Optional[dict] = None):
        self.animation_state = state
        self.last_result = result

    def render_piste(self, distance: str = "medium", opponent_action: dict = None) -> str:
        distance_map = {"far": 70, "medium": 50, "close": 30}

        fencer_x = 20
        opponent_x = 100 - distance_map.get(distance, 50)
        fencer_y = 80
        opponent_y = 80

        fencer_svg = self._render_stick_fencer(fencer_x, fencer_y, self.FENCER_COLOR, "left")
        opponent_svg = self._render_stick_fencer(opponent_x, opponent_y, self.OPPONENT_COLOR, "right")

        distance_line = f'<line x1="{fencer_x + 30}" y1="140" x2="{opponent_x - 10}" y2="140" stroke="white" stroke-width="2" stroke-dasharray="5,5"/>'
        distance_label = f'<text x="50" y="155" fill="white" font-size="12" text-anchor="middle">Distance: {distance.title()}</text>'

        action_icons = ""
        if opponent_action:
            action_type = opponent_action.get("type", "unknown").replace("_", " ").title()
            action_icons = f'''
            <text x="{opponent_x}" y="40" fill="{self.OPPONENT_COLOR}" font-size="11" text-anchor="middle" font-weight="bold">
                ⚔️ {action_type}
            </text>
            '''

        svg = f'''
        <svg viewBox="0 0 200 180" xmlns="http://www.w3.org/2000/svg">
            <rect x="0" y="0" width="200" height="180" fill="{self.PISTE_COLOR}"/>
            <line x1="100" y1="0" x2="100" y2="180" stroke="{self.LINE_COLOR}" stroke-width="2" opacity="0.5"/>
            <line x1="10" y1="0" x2="10" y2="180" stroke="{self.LINE_COLOR}" stroke-width="3"/>
            <line x1="190" y1="0" x2="190" y2="180" stroke="{self.LINE_COLOR}" stroke-width="3"/>
            {distance_line}
            {distance_label}
            {fencer_svg}
            {opponent_svg}
            {action_icons}
            <text x="30" y="20" fill="{self.FENCER_COLOR}" font-size="14" font-weight="bold">YOU</text>
            <text x="170" y="20" fill="{self.OPPONENT_COLOR}" font-size="14" font-weight="bold">OPP</text>
        </svg>
        '''
        return svg

    def _render_stick_fencer(self, x: int, y: int, color: str, facing: str) -> str:
        direction = 1 if facing == "right" else -1

        body = f'''
        <circle cx="{x}" cy="{y-50}" r="8" fill="{color}"/>
        <line x1="{x}" y1="{y-42}" x2="{x}" y2="{y-10}" stroke="{color}" stroke-width="3"/>
        <line x1="{x}" y1="{y-35}" x2="{x + 15 * direction}" y2="{y-30}" stroke="{color}" stroke-width="2"/>
        <line x1="{x}" y1="{y-35}" x2="{x - 10 * direction}" y2="{y-20}" stroke="{color}" stroke-width="2"/>
        <line x1="{x}" y1="{y-10}" x2="{x - 8}" y2="{y+20}" stroke="{color}" stroke-width="3"/>
        <line x1="{x}" y1="{y-10}" x2="{x + 8}" y2="{y+20}" stroke="{color}" stroke-width="3"/>
        <line x1="{x + 5 * direction}" y1="{y-30}" x2="{x + 20 * direction}" y2="{y-45}" stroke="{color}" stroke-width="2"/>
        <line x1="{x + 5 * direction}" y1="{y-30}" x2="{x + 18 * direction}" y2="{y-15}" stroke="{color}" stroke-width="2"/>
        '''
        return body

    def render_score(self) -> str:
        return f'''
        <svg viewBox="0 0 120 40" xmlns="http://www.w3.org/2000/svg">
            <rect x="0" y="0" width="120" height="40" rx="5" fill="#1F2937"/>
            <text x="30" y="25" fill="{self.FENCER_COLOR}" font-size="18" font-weight="bold" text-anchor="middle">
                {self.score["fencer"]}
            </text>
            <text x="60" y="25" fill="white" font-size="14" text-anchor="middle">-</text>
            <text x="90" y="25" fill="{self.OPPONENT_COLOR}" font-size="18" font-weight="bold" text-anchor="middle">
                {self.score["opponent"]}
            </text>
        </svg>
        '''

    def render_target_zones(self) -> str:
        zones = ""
        targets = [
            ("torso", 50, 60, "#3B82F6"),
            ("back", 150, 60, "#EF4444"),
            ("shoulders", 100, 45, "#10B981"),
        ]
        for name, x, y, color in targets:
            zones += f'<circle cx="{x}" cy="{y}" r="8" fill="{color}" opacity="0.3"/><text x="{x}" y="{y+20}" fill="white" font-size="8" text-anchor="middle">{name}</text>'
        return zones

    def render_exchange_result(self, result: dict) -> str:
        call = result.get("call", "simultaneous")
        fencer_score = result.get("fencer_score", 0)
        opponent_score = result.get("opponent_score", 0)

        if call == "fencer":
            color = self.FENCER_COLOR
            text = f"✓ You scored!"
        elif call == "opponent":
            color = self.OPPONENT_COLOR
            text = "✗ Opponent scored!"
        else:
            color = "#FBBF24"
            text = "○ Simultaneous - no score"

        return f'''
        <svg viewBox="0 0 150 30" xmlns="http://www.w3.org/2000/svg">
            <rect x="0" y="0" width="150" height="30" rx="5" fill="{color}"/>
            <text x="75" y="20" fill="white" font-size="12" font-weight="bold" text-anchor="middle">{text}</text>
        </svg>
        '''


def render_fencer_arena(distance: str, opponent_action: dict, score: dict, last_result: dict = None):
    visualizer = FencerVisualizer()
    visualizer.set_score(score)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        st.markdown("### 🔵 You", unsafe_allow_html=True)
        st.markdown(f"**Score: {score['fencer']}**")

    with col2:
        piste_svg = visualizer.render_piste(distance, opponent_action)
        st.markdown(f'<div style="text-align: center;">{piste_svg}</div>', unsafe_allow_html=True)

        if last_result:
            result_svg = visualizer.render_exchange_result(last_result)
            st.markdown(f'<div style="text-align: center; margin-top: 10px;">{result_svg}</div>', unsafe_allow_html=True)

    with col3:
        st.markdown("### 🔴 Opponent", unsafe_allow_html=True)
        st.markdown(f"**Score: {score['opponent']}**")

    return visualizer