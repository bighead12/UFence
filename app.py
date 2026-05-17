import streamlit as st
from src.crew.fencing_crew import FencingCrew
from src.utils.config import WINNING_SCORE
from src.visualization.fencer_svg import render_fencer_arena
from src.visualization.animator import render_complete_animation
from src.visualization.history import render_history_panel
import streamlit.components.v1 as components
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
    st.session_state.messages = []

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
        st.session_state.messages = []
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
                st.session_state.messages = []
                st.rerun()

        else:
            st.markdown("### 🎯 Fencing Arena")

            opponent_intent = crew.get_opponent_intent()
            distance = opponent_intent.get("distance", "medium")

            render_fencer_arena(
                distance=distance,
                opponent_action=opponent_intent.get("action"),
                score=score,
                last_result=st.session_state.get("last_result")
            )

            st.caption(f"🔵 {score['fencer']} — 🔴 {score['opponent']}  |  Exchange {crew.exchange_number}")

            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

            if prompt := st.chat_input("Describe your fencing move..."):
                if not st.session_state.get("_processing_message"):
                    st.session_state._processing_message = True
                    st.session_state.messages.append({"role": "user", "content": prompt})

                    with st.chat_message("user"):
                        st.markdown(prompt)

                    with st.spinner("Interpreting and executing..."):
                        try:
                            action, target = crew.interpret_user_intent(prompt)
                            result = crew.execute_exchange(action, target)
                            score = crew.referee.score

                            fencer_action = result.get("fencer_action", {}).get("type", "direct_attack")
                            opponent_action = result.get("opponent_action", {}).get("type", "direct_attack")
                            referee_call = result.get("referee_call", {})
                            call = referee_call.get("call", "simultaneous")
                            reason = referee_call.get("reason", "")

                            action_labels = {
                                "direct_attack": "Direct Attack", "compound_attack": "Compound Attack",
                                "fleche": "Fleche", "parry_and_riposte": "Parry & Riposte",
                                "counter_attack": "Counter-Attack", "remise": "Remise", "prise_de_fer": "Prise de Fer",
                            }
                            action_label = action_labels.get(action, action)
                            opp_label = action_labels.get(opponent_action, opponent_action)

                            call_icons = {"fencer": "✅", "opponent": "❌", "simultaneous": "🤝"}
                            call_text = {"fencer": "You scored!", "opponent": "Opponent scored.", "simultaneous": "Simultaneous"}

                            assistant_msg = (
                                f"**You:** {action_label} → *{target}*\n\n"
                                f"**Opponent:** {opp_label}\n\n"
                                f"{call_icons.get(call, '⚔️')} **{call_text.get(call, '')}** — {reason}\n\n"
                                f"🔵 {result['score']['fencer']} — 🔴 {result['score']['opponent']}"
                            )

                            with st.chat_message("assistant"):
                                st.markdown(assistant_msg)
                                with st.expander("🎬 Show animation"):
                                    animation_html = render_complete_animation(
                                        fencer_action, opponent_action, call,
                                        result.get("score", {}).get("fencer", 0),
                                        result.get("score", {}).get("opponent", 0)
                                    )
                                    components.html(animation_html, height=400)

                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": assistant_msg,
                                "animation_html": animation_html,
                                "fencer_action": fencer_action,
                                "opponent_action": opponent_action,
                                "call": call,
                                "fencer_score": result.get("score", {}).get("fencer", 0),
                                "opponent_score": result.get("score", {}).get("opponent", 0)
                            })
                            st.session_state.exchange_results.append(result)
                            st.session_state.last_result = referee_call

                            st.rerun()

                        except Exception as e:
                            st.error(f"Error: {e}")
                            with st.expander("Debug"):
                                st.code(traceback.format_exc())
                        finally:
                            st.session_state._processing_message = False
                else:
                    st.session_state._processing_message = False

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