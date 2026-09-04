# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

| Purpose | Command |
|---|---|
| Install dependencies | `pip install -r requirements.txt` |
| Set OpenRouter API key | `echo "OPENROUTER_API_KEY=sk-or-..." >> .env` (or paste in app sidebar) |
| Start the application | `streamlit run app.py` |
| Run tests | `pytest` |
| Lint code | `ruff check .` |
| Format code | `ruff format .` |
| Type-check (optional) | `mypy src/` |

## Architecture Overview

UFence is an AI‑powered fencing exchange simulation built with **CrewAI** and **OpenRouter**. The system coordinates four role‑based agents that interact through a Streamlit UI:

- **Fencer** – the user‑controlled agent that selects actions.
- **Opponent** – an adaptive AI opponent that learns from patterns.
- **Referee** – enforces right‑of‑way rules and decides touches.
- **Coach** – provides post‑match analysis and feedback.

Agents live in `src/agents/`, the crew orchestration is in `src/crew/fencing_crew.py`, and fencing rules are stored in `config/fencing_rules.json`. The top‑level `app.py` renders the Streamlit interface.

## Project Structure

```
ufence/
├── app.py                # Streamlit web interface (entry point)
├── config/
│   └── fencing_rules.json   # Fencing rules knowledge base
├── src/
│   ├── agents/
│   │   ├── fencer.py        # Fencer agent
│   │   ├── opponent.py      # Adaptive opponent AI
│   │   ├── referee.py      # Referee decision agent
│   │   └── coach.py        # Coach feedback agent
│   ├── crew/
│   │   └── fencing_crew.py # Crew orchestration
│   └── utils/
│       ├── config.py       # Configuration
│       └── logging.py      # Logging
├── tests/                # Test files (pytest)
├── pyproject.toml        # Project metadata & dependencies
├── requirements.txt      # Pinned Python dependencies
└── README.md             # User‑facing documentation
```

## Development

- **Run the test suite**: `pytest` — discover and run all tests in `tests/`.
- **Lint the codebase**: `ruff check .` — catch style and quality issues.
- **Format the code**: `ruff format .` — apply consistent formatting.
- **Install/upgrade dependencies**: `pip install -r requirements.txt` (dev extras include `black`, `ruff`, `mypy`).
- **Start the app**: `streamlit run app.py` — opens the UI at `http://localhost:8501`.
- **OpenRouter API key**: sign up at openrouter.ai/keys and set `OPENROUTER_API_KEY` in `.env` (or paste it in the app's sidebar). Needed for natural-language intent parsing and Coach Chat.

## Key Files to Know

- `app.py` — the Streamlit app; changing UI flow or pages goes here. The sidebar handles OpenRouter config (API key + model picker).
- `src/agents/*.py` — the four agents. Only `coach.py` calls the LLM (via litellm) for Coach Chat RAG answers.
- `src/crew/fencing_crew.py` — ties the agents together; `interpret_user_intent()` calls the LLM for natural-language move parsing.
- `src/utils/config.py` — holds `OPENROUTER_MODEL` and `OPENROUTER_MODELS` (the sidebar dropdown list).
- `config/fencing_rules.json` — the rule set the referee uses to score touches.
- `tests/` — pytest suite; adding a new test usually means adding a file or function here.