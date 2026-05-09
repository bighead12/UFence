import streamlit as st
from src.crew.fencing_crew import FencingCrew
from src.utils.config import WINNING_SCORE

st.set_page_config(page_title="UFence - Fencing Exchange Simulator", page_icon="🤺", layout="wide")

if "crew" not in st.session_state:
    st.session_state.crew = FencingCrew()
    st.session_state.match_started = False
    st.session_state.exchange_results = []

st.title("🤺 UFence - Fencing Exchange Simulator")

if not st.session_state.match_started:
    st.markdown("### Welcome to UFence!")
    st.markdown("Experience a fencing match with AI-powered agents:")
    st.markdown("- **You (Fencer)** - Execute fencing actions")
    st.markdown("- **Opponent** - Adaptive AI opponent")
    st.markdown("- **Referee** - Official decisions with right-of-way")
    st.markdown("- **Coach** - Post-match analysis and feedback")

    col1, col2 = st.columns([2, 1])
    with col1:
        st.info(f"🏆 First to {WINNING_SCORE} touches wins!")

    if st.button("Start New Match", type="primary"):
        result = st.session_state.crew.start_new_match()
        st.session_state.match_started = True
        st.session_state.exchange_results = []
        st.rerun()

else:
    crew = st.session_state.crew

    score = crew.referee.score
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("You", score["fencer"])
    with col2:
        st.metric("Opponent", score["opponent"])
    with col3:
        st.metric("Exchanges", st.session_state.crew.exchange_number)

    if score["fencer"] >= WINNING_SCORE or score["opponent"] >= WINNING_SCORE:
        st.divider()
        st.markdown("### 🏆 Match Complete!")

        winner = "You" if score["fencer"] > score["opponent"] else "Opponent"
        st.success(f"**{winner} won the match!**")

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

        if st.button("Start New Match"):
            result = crew.start_new_match()
            st.session_state.exchange_results = []
            st.rerun()

    else:
        st.divider()
        st.markdown("### Your Action")

        valid_actions = crew.get_valid_actions()
        action_labels = {
            "direct_attack": "Direct Attack",
            "compound_attack": "Compound Attack",
            "fleche": "Fleche (Running Attack)",
            "parry_and_riposte": "Parry & Riposte",
            "counter_attack": "Counter-Attack",
            "remise": "Remise",
            "prise_de_fer": "Prise de Fer"
        }

        action_options = [action_labels[a] for a in valid_actions]
        selected_action = st.selectbox("Select your action:", action_options)

        selected_action_key = valid_actions[action_options.index(selected_action)]

        if st.button("Execute Action", type="primary"):
            result = crew.execute_exchange(selected_action_key)
            st.session_state.exchange_results.append(result)

            st.success(f"Action executed: {selected_action}")
            st.rerun()

    st.divider()
    st.markdown("### 📜 Exchange History")

    if st.session_state.exchange_results:
        for i, result in enumerate(st.session_state.exchange_results, 1):
            with st.expander(f"Exchange #{i}", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Your Action:** {result['fencer_action']['type']}")
                    st.markdown(f"**Target:** {result['fencer_action']['target']}")

                with col2:
                    st.markdown(f"**Opponent Action:** {result['opponent_action']['type']}")
                    st.markdown(f"**Target:** {result['opponent_action']['target']}")

                call = result['referee_call']
                st.markdown(f"**Referee Call:** {call['call']}")
                st.markdown(f"**Reason:** {call['reason']}")

                if call['fencer_score']:
                    st.success("You scored! +1")
                if call['opponent_score']:
                    st.error("Opponent scored! +1")

    else:
        st.info("No exchanges yet. Start your first exchange!")

st.markdown("---")
st.markdown("UFence - AI-Powered Fencing Exchange Simulator")