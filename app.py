import os
import traceback

import streamlit as st
import streamlit.components.v1 as components

from src.crew.fencing_crew import FencingCrew
from src.knowledge.ingest import get_ingestion_status, ingest_books
from src.knowledge.retriever import BookRetriever
from src.utils.config import WINNING_SCORE
from src.visualization.animator import render_complete_animation
from src.visualization.fencer_svg import render_fencer_arena
from src.visualization.history import render_history_panel


# ------------------------------------------------------------------
# Helper functions for exchange execution
# ------------------------------------------------------------------
def _execute_move(crew: FencingCrew, action: str, target: str) -> None:
    """Execute a fencing move with the given action and target."""
    if st.session_state.get("_processing_message"):
        return
    st.session_state._processing_message = True

    try:
        result = crew.execute_exchange(action, target)

        fencer_action = result.get("fencer_action", {}).get("type", "direct_attack")
        opponent_action = result.get("opponent_action", {}).get("type", "direct_attack")
        referee_call = result.get("referee_call", {})
        call = referee_call.get("call", "simultaneous")
        reason = referee_call.get("reason", "")

        _action_labels = {
            "direct_attack": "Direct Attack",
            "compound_attack": "Compound Attack",
            "fleche": "Fleche",
            "parry_and_riposte": "Parry & Riposte",
            "counter_attack": "Counter-Attack",
            "remise": "Remise",
            "prise_de_fer": "Prise de Fer",
        }
        opp_label = _action_labels.get(opponent_action, opponent_action)
        call_icons = {"fencer": "✅", "opponent": "❌", "simultaneous": "🤝"}
        call_text = {
            "fencer": "You scored!",
            "opponent": "Opponent scored.",
            "simultaneous": "Simultaneous",
        }

        assistant_msg = (
            f"**You:** {_action_labels.get(action, action)} → *{target}*\n\n"
            f"**Opponent:** {opp_label}\n\n"
            f"{call_icons.get(call, '⚔️')} "
            f"**{call_text.get(call, '')}** — {reason}\n\n"
            f"🔵 {result['score']['fencer']} — 🔴 {result['score']['opponent']}"
        )

        with st.chat_message("assistant"):
            st.markdown(assistant_msg)
            with st.expander("🎬 Show animation"):
                animation_html = render_complete_animation(
                    fencer_action,
                    opponent_action,
                    call,
                    result.get("score", {}).get("fencer", 0),
                    result.get("score", {}).get("opponent", 0),
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
            "opponent_score": result.get("score", {}).get("opponent", 0),
        })
        st.session_state.exchange_results.append(result)
        st.session_state.last_result = referee_call

    except (ValueError, RuntimeError) as e:
        st.error(f"Error: {e}")
        with st.expander("Debug"):
            st.code(traceback.format_exc())
    finally:
        st.session_state._processing_message = False


def _execute_natural_language_move(crew: FencingCrew, prompt: str) -> None:
    """Interpret a natural language fencing move and execute it."""
    if st.session_state.get("_processing_message"):
        return
    st.session_state._processing_message = True

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        with st.spinner("Interpreting and executing..."):
            action, target = crew.interpret_user_intent(prompt)
            _execute_move(crew, action, target)

    except (ValueError, RuntimeError) as e:
        st.error(f"Error: {e}")
        with st.expander("Debug"):
            st.code(traceback.format_exc())
    finally:
        st.session_state._processing_message = False


st.set_page_config(
    page_title="UFence - Fencing Exchange Simulator",
    page_icon="🤺",
    layout="wide"
)

# Sidebar for Gemini Configuration
st.sidebar.title("🤺 UFence Control Panel")
st.sidebar.markdown("---")

# Retrieve API Key from env if present
env_key = os.getenv("GEMINI_API_KEY", "")

# Key input (hides character by default)
api_key = st.sidebar.text_input(
    "🔑 Google Gemini API Key",
    value=env_key,
    type="password",
    help="Get a free key from Google AI Studio (aistudio.google.com)"
)

# If key is provided in UI, set it in environment for LiteLLM to use
if api_key:
    os.environ["GEMINI_API_KEY"] = api_key
    st.sidebar.success("🟢 API Key Active")
else:
    st.sidebar.warning(
        "🔴 Missing API Key. Enter a key to enable Coach Chat & "
        "Natural Language interpretation!"
    )

st.sidebar.markdown("---")
st.sidebar.info(
    "💡 **Google Gemini Mode Active**\n\n"
    "This app now uses **Gemini 2.5 Flash** (Free Tier) to power the fencing "
    "referee interpretation and Coach feedback agents! "
    "This allows for fast, cloud-hosted intelligence without running local "
    "GPU/Ollama servers."
)


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
    except (ConnectionError, RuntimeError, ValueError) as e:
        st.error(f"Error initializing crew: {e}")
        st.session_state.crew = None
    st.session_state.match_started = False
    st.session_state.exchange_results = []
    st.session_state.last_result = None
    st.session_state.messages = []
    st.session_state.coach_messages = []
    st.session_state.book_retriever = None

if st.session_state.crew is None:
    try:
        st.session_state.crew = FencingCrew()
    except (ConnectionError, RuntimeError, ValueError) as e:
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
        st.session_state.coach_messages = []
        st.rerun()

else:
    crew = st.session_state.crew
    if crew is None:
        st.error("Crew not initialized. Please refresh the page.")
        st.button("Refresh", on_click=lambda: st.rerun())

    score = crew.referee.score

    tab1, tab2, tab3 = st.tabs(["🎯 Arena", "📜 History", "🏅 Coach"])

    with tab1:
        if (
            score["fencer"] >= WINNING_SCORE
            or score["opponent"] >= WINNING_SCORE
        ):
            st.divider()
            st.markdown("### 🏆 Match Complete!")

            winner = (
                "You"
                if score["fencer"] > score["opponent"]
                else "Opponent"
            )
            winner_color = (
                "#3B82F6"
                if score["fencer"] > score["opponent"]
                else "#EF4444"
            )
            st.markdown(
                f"<h2 style='color: {winner_color}; text-align: center;'>"
                f"{winner} won the match {score['fencer']}-"
                f"{score['opponent']}!</h2>",
                unsafe_allow_html=True
            )

            st.info(
                "📋 Switch to the **🏅 Coach** tab to view detailed post-match analysis."
            )

            if st.button("Play Again", type="primary"):
                result = crew.start_new_match()
                st.session_state.exchange_results = []
                st.session_state.last_result = None
                st.session_state.messages = []
                st.session_state.coach_messages = []
                st.session_state.selected_action = None
                st.session_state.selected_target = "torso"
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

            st.caption(
                f"🔵 {score['fencer']} — 🔴 {score['opponent']}  |  "
                f"Exchange {crew.exchange_number}"
            )

            # Initialize selection state
            if "selected_action" not in st.session_state:
                st.session_state.selected_action = None
            if "selected_target" not in st.session_state:
                st.session_state.selected_target = "torso"

            # Action button labels
            action_labels = {
                "direct_attack": "⚡ Direct",
                "compound_attack": "🔗 Compound",
                "fleche": "💨 Fleche",
                "parry_and_riposte": "🛡️ Parry-Riposte",
                "counter_attack": "⚡ Counter",
                "remise": "↗️ Remise",
                "prise_de_fer": "🤝 Prise de Fer",
            }
            valid_actions = crew.get_valid_actions()
            valid_targets = crew.get_valid_targets()

            st.markdown("#### Choose Your Action")

            # 4-column grid for action buttons
            cols = st.columns(4)
            for i, action in enumerate(valid_actions):
                col_idx = i % 4
                label = action_labels.get(action, action.replace("_", " ").title())
                is_selected = st.session_state.selected_action == action
                button_type = "primary" if is_selected else "secondary"
                with cols[col_idx]:
                    if st.button(label, key=f"action_{action}", type=button_type, use_container_width=True):
                        st.session_state.selected_action = action
                        st.rerun()

            # Target selection
            st.markdown("**Target:**")
            target_cols = st.columns(len(valid_targets))
            for i, target in enumerate(valid_targets):
                is_selected = st.session_state.selected_target == target
                button_type = "primary" if is_selected else "secondary"
                label = target.title()
                with target_cols[i]:
                    if st.button(label, key=f"target_{target}", type=button_type, use_container_width=True):
                        st.session_state.selected_target = target
                        st.rerun()

            # Execute / Clear buttons
            col_exec, col_clear = st.columns([1, 1])
            with col_exec:
                if st.button("🎯 Execute Move", type="primary", disabled=st.session_state.selected_action is None, use_container_width=True):
                    _execute_move(crew, st.session_state.selected_action, st.session_state.selected_target)
                    st.rerun()

            with col_clear:
                if st.button("🔄 Clear Selection", use_container_width=True):
                    st.session_state.selected_action = None
                    st.session_state.selected_target = "torso"
                    st.rerun()

            # Advanced: Natural language input
            with st.expander("✨ Advanced: Describe your move in plain text"):
                st.caption("For custom moves or power users")
                if prompt := st.chat_input("Describe your fencing move..."):
                    _execute_natural_language_move(crew, prompt)
                    st.rerun()

            # Display recent exchange messages
            if st.session_state.messages:
                for msg in st.session_state.messages:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])

    with tab2:
        render_history_panel(st.session_state.exchange_results)

    with tab3:
        # Match-complete winner banner
        if (
            score["fencer"] >= WINNING_SCORE
            or score["opponent"] >= WINNING_SCORE
        ):
            winner = (
                "You" if score["fencer"] > score["opponent"] else "Opponent"
            )
            winner_color = (
                "#3B82F6"
                if score["fencer"] > score["opponent"]
                else "#EF4444"
            )
            st.markdown(
                f"<h2 style='color: {winner_color}; text-align: center;'>"
                f"🏆 {winner} won the match {score['fencer']}-"
                f"{score['opponent']}!</h2>",
                unsafe_allow_html=True
            )

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

        # --- Coach Chat Section ---
        st.divider()
        st.markdown("### 💬 Ask Your Coach")
        st.caption(
            "Ask questions about your performance, technique, or fencing "
            "strategy. The coach uses knowledge from fencing reference books."
        )

        # Check book ingestion status
        status = get_ingestion_status()
        has_pdfs = len(status["pdf_files"]) > 0
        has_vectorstore = status["total_chunks"] > 0

        # Show persistence success message if present in state
        if st.session_state.get("show_ingestion_success"):
            st.success("✅ Knowledge base successfully populated and ready!")

        if not has_pdfs and not has_vectorstore:
            st.warning(
                "📚 No fencing PDF books found. "
                "You can place your PDF files in `data/books` to build a "
                "custom knowledge base."
            )
            st.info(
                "💡 You can initialize the Coach's knowledge base using the "
                "built-in Fencing Rules Handbook!"
            )
            if st.button(
                "📥 Initialize Rules Knowledge Base", type="primary"
            ):
                with st.spinner("Initializing rules knowledge base..."):
                    try:
                        collection = ingest_books()
                        if collection:
                            st.session_state.show_ingestion_success = True
                            st.session_state.book_retriever = None
                            st.rerun()
                        else:
                            st.error("Failed to initialize database.")
                    except (ValueError, RuntimeError) as e:
                        st.error(f"Error: {e}")
        elif not has_vectorstore:
            st.info(
                f"📚 Found {len(status['pdf_files'])} PDF(s) ready to "
                f"ingest: {', '.join(status['pdf_files'])}"
            )
            st.markdown(
                "*(Note: Scanned/image-only PDFs will automatically trigger "
                "a rules-fallback ingestion to ensure a working coach "
                "experience)*"
            )
            if st.button(
                "📥 Ingest Books & Rules into Knowledge Base",
                type="primary"
            ):
                with st.spinner(
                    "Ingesting knowledge base... This may take a minute on "
                    "first run."
                ):
                    try:
                        collection = ingest_books()
                        if collection:
                            st.session_state.show_ingestion_success = True
                            st.session_state.book_retriever = None
                            st.rerun()
                        else:
                            st.error("Ingestion failed. Check the logs.")
                    except (ValueError, RuntimeError) as e:
                        st.error(f"Ingestion error: {e}")
        else:
            # Retriever is available — show chat
            with st.expander(
                f"📚 Knowledge Base: {status['total_chunks']} chunks from "
                f"{len(status['ingested_sources'])} source(s)",
                expanded=False
            ):
                for src in status["ingested_sources"]:
                    st.markdown(f"- ✅ {src}")
                if status["pending"]:
                    st.markdown("**Pending:**")
                    for src in status["pending"]:
                        st.markdown(f"- ⏳ {src}")
                    if st.button("📥 Ingest New Books"):
                        with st.spinner("Ingesting..."):
                            ingest_books()
                            st.session_state.book_retriever = None
                            st.rerun()

            # Lazy-initialize the retriever
            if st.session_state.book_retriever is None:
                st.session_state.book_retriever = BookRetriever()

            retriever = st.session_state.book_retriever

            if not retriever.is_ready:
                st.warning(
                    "Knowledge base is not ready. Try re-ingesting the books."
                )
            else:
                # Display chat history
                for msg in st.session_state.coach_messages:
                    with st.chat_message(
                        msg["role"],
                        avatar="🏋️" if msg["role"] == "user" else "🧑‍🏫"
                    ):
                        st.markdown(msg["content"])
                        if msg.get("sources"):
                            with st.expander("📚 Sources"):
                                for s in msg["sources"]:
                                    page_info = (
                                        f", p. {s['page']}"
                                        if s.get('page')
                                        else ""
                                    )
                                    st.markdown(
                                        f"- *{s['source']}*{page_info}"
                                    )

                # If the last message is from user, generate assistant
                # response
                if (
                    st.session_state.coach_messages
                    and st.session_state.coach_messages[-1]["role"] == "user"
                ):
                    user_msg = (
                        st.session_state.coach_messages[-1]["content"]
                    )
                    with st.chat_message("assistant", avatar="🧑‍🏫"), st.spinner("Coach is thinking..."):
                            try:
                                result = crew.coach_chat(
                                    user_msg, retriever
                                )
                                answer = result["answer"]
                                sources = result["sources"]

                                st.markdown(answer)
                                if sources:
                                    with st.expander("📚 Sources"):
                                        for s in sources:
                                            page_info = (
                                                f", p. {s['page']}"
                                                if s.get('page')
                                                else ""
                                            )
                                            st.markdown(
                                                f"- *{s['source']}*"
                                                f"{page_info}"
                                            )

                                st.session_state.coach_messages.append({
                                    "role": "assistant",
                                    "content": answer,
                                    "sources": sources,
                                })
                                # Clear success banner on first question
                                if (
                                    "show_ingestion_success"
                                    in st.session_state
                                ):
                                    del (
                                        st.session_state
                                        .show_ingestion_success
                                    )
                                st.rerun()
                            except (ValueError, RuntimeError) as e:
                                st.error(f"Error: {e}")
                                with st.expander("Debug"):
                                    st.code(traceback.format_exc())

                # Chat input using form to bypass Streamlit single
                # st.chat_input restriction
                with st.form(key="coach_chat_form", clear_on_submit=True):
                    col_input, col_btn = st.columns([5, 1])
                    with col_input:
                        coach_question = st.text_input(
                            "Ask your coach a question:",
                            placeholder=(
                                "e.g. How can I defend better "
                                "against fleche?"
                            ),
                            label_visibility="collapsed"
                        )
                    with col_btn:
                        submit_button = st.form_submit_button(
                            label="Send", use_container_width=True
                        )

                if submit_button and coach_question:
                    st.session_state.coach_messages.append({
                        "role": "user",
                        "content": coach_question,
                    })
                    st.rerun()

st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: gray;'>"
    "UFence - AI-Powered Fencing Exchange Simulator</p>",
    unsafe_allow_html=True
)
