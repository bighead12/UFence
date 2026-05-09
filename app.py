import streamlit as st
from src.crew.fencing_crew import FencingCrew
from src.utils.config import WINNING_SCORE
from src.visualization.fencer_svg import render_fencer_arena
from src.visualization.animator import create_action_icon
from src.visualization.history import render_history_panel
import traceback

st.set_page_config(page_title="UFence - Fencing Exchange Simulator", page_icon="🤺", layout="wide")

st.markdown("""
<style>
@keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.05); }
    100% { transform: scale(1); }
}
</style>
""", unsafe_allow_html=True)

if "crew" not in st.session_state:
    try:
        st.session_state.crew = FencingCrew()
    except Exception as e:
        st.error(f"Error initializing crew: {e}")
        st.session_state.crew = None
    st.session_state.match_started = False
    st.session_state.exchange_results = []
    st.session_state.last_result = None

if st.session_state.crew is None:
    try:
        st.session_state.crew = FencingCrew()
    except Exception as e:
        st.error(f"Error recreating crew: {e}")
        st.button("Retry", on_click=lambda: st.rerun())

st.title("🤺 UFence - Fencing Arena")

if not st.session_state.match_started:
    st.markdown("### Welcome to UFence!")
    st.markdown("Experience a fencing match with AI-powered agents:")
    st.markdown("- **You (Blue Fencer)** - Execute fencing actions")
    st.markdown("- **Opponent (Red Fencer)** - Adaptive AI opponent")
    st.markdown("- **Referee** - Official decisions with right-of-way")
    st.markdown("- **Coach** - Post-match analysis and feedback")

    col1, col2 = st.columns([2, 1])
    with col1:
        st.info(f"🏆 First to {WINNING_SCORE} touches wins!")

    if st.button("Start New Match", type="primary"):
        result = st.session_state.crew.start_new_match()
        st.session_state.match_started = True
        st.session_state.exchange_results = []
        st.session_state.last_result = None
        st.rerun()

else:
    crew = st.session_state.crew
    if crew is None:
        st.error("Crew not initialized. Please refresh the page.")
        st.button("Refresh", on_click=lambda: st.rerun())

    score = crew.referee.score

    tab1, tab2, tab3 = st.tabs(["🎯 Arena", "📜 History", "🏅 Coach"])

    with tab1:
        if score["fencer"] >= WINNING_SCORE or score["opponent"] >= WINNING_SCORE:
            st.divider()
            st.markdown("### 🏆 Match Complete!")

            winner = "You" if score["fencer"] > score["opponent"] else "Opponent"
            winner_color = "#3B82F6" if score["fencer"] > score["opponent"] else "#EF4444"
            st.markdown(f"<h2 style='color: {winner_color}; text-align: center;'>{winner} won the match {score['fencer']}-{score['opponent']}!</h2>", unsafe_allow_html=True)

            if crew.referee.exchange_history:
                feedback = crew.coach.analyze_exchange(
                    crew.referee.exchange_history,
                    score
                )

                st.markdown("### 📋 Coach's Analysis")
                st.info(f"**Summary:** {feedback['summary']}")

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("#### 🔧 Technical Feedback")
                    for item in feedback['technical']:
                        st.markdown(f"- {item}")

                with col2:
                    st.markdown("#### 🎯 Tactical Feedback")
                    for item in feedback['tactical']:
                        st.markdown(f"- {item}")

                st.markdown("#### 📈 Strategic Insights")
                for item in feedback['strategic']:
                    st.markdown(f"- {item}")

                st.markdown("#### 💡 Recommendations")
                for rec in feedback['recommendations']:
                    st.markdown(f"- {rec}")

            if st.button("Play Again", type="primary"):
                result = crew.start_new_match()
                st.session_state.exchange_results = []
                st.session_state.last_result = None
                st.rerun()

        else:
            st.markdown("---")
            st.markdown("### 🎯 Fencing Arena")

            opponent_intent = crew.get_opponent_intent()
            distance = opponent_intent.get("distance", "medium")

            render_fencer_arena(
                distance=distance,
                opponent_action=opponent_intent.get("action"),
                score=score,
                last_result=st.session_state.get("last_result")
            )

            st.markdown("---")
            st.markdown("### ⚔️ Your Action")

            col1, col2 = st.columns([3, 1])

            with col1:
                valid_actions = crew.get_valid_actions()
                action_labels = {
                    "direct_attack": "🗡️ Direct Attack",
                    "compound_attack": "🔱 Compound Attack",
                    "fleche": "🏃 Fleche (Running)",
                    "parry_and_riposte": "🛡️ Parry & Riposte",
                    "counter_attack": "⚡ Counter-Attack",
                    "remise": "↩️ Remise",
                    "prise_de_fer": "✋ Prise de Fer"
                }

                action_options = [action_labels[a] for a in valid_actions]
                selected_action = st.selectbox("Select your action:", action_options, key="action_select")

                selected_action_key = valid_actions[action_options.index(selected_action)]

            with col2:
                st.markdown("### Target Areas")
                st.info("🎯 Torso (main)")

            if st.button("⚔️ Execute Action", type="primary", use_container_width=True):
                try:
                    result = crew.execute_exchange(selected_action_key)
                    st.session_state.exchange_results.append(result)
                    st.session_state.last_result = result["referee_call"]

                    with st.spinner("⚔️ Fencing..."):
                        pass
                    st.rerun()
                except Exception as e:
                    st.error(f"Error executing action: {e}")
                    with st.expander("Debug details"):
                        st.code(traceback.format_exc())

            st.markdown("---")
            st.markdown("### 📊 Quick Stats")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🔵 You", score["fencer"])
            with col2:
                st.metric("🔴 Opponent", score["opponent"])
            with col3:
                st.metric("⚔️ Exchanges", crew.exchange_number)

    with tab2:
        render_history_panel(st.session_state.exchange_results)

    with tab3:
        if crew.referee.exchange_history:
            feedback = crew.coach.analyze_exchange(
                crew.referee.exchange_history,
                crew.referee.score
            )

            st.markdown("### 📋 Coach's Analysis")
            st.info(f"**Summary:** {feedback['summary']}")

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### 🔧 Technical")
                for item in feedback['technical']:
                    st.markdown(f"- {item}")

                st.markdown("#### 📈 Strategic")
                for item in feedback['strategic']:
                    st.markdown(f"- {item}")

            with col2:
                st.markdown("#### 🎯 Tactical")
                for item in feedback['tactical']:
                    st.markdown(f"- {item}")

                st.markdown("#### 💡 Recommendations")
                for rec in feedback['recommendations']:
                    st.markdown(f"- {rec}")

            if feedback.get('score_analysis'):
                st.markdown("### 📊 Performance")
                sa = feedback['score_analysis']
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Your Points", sa.get('fencer_points', 0))
                with col2:
                    st.metric("Opp Points", sa.get('opponent_points', 0))
                with col3:
                    st.metric("Ties", sa.get('ties', 0))
        else:
            st.info("Complete some exchanges to get coach feedback!")

st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'>UFence - AI-Powered Fencing Exchange Simulator</p>", unsafe_allow_html=True)