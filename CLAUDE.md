# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

| Purpose | Command |
|---|---|
| Install dependencies | `pip install -r requirements.txt` |
| Install Ollama and pull model | `ollama pull llama3.2` |
| Start the application | `streamlit run app.py` |
| Run tests | `pytest` |
| Lint code | `ruff check .` |
| Format code | `ruff format .` |
| Type-check (optional) | `mypy src/` |

## Architecture Overview

UFence is an AI‑powered fencing exchange simulation built with **CrewAI** and **Ollama**. The system coordinates four role‑based agents that interact through a Streamlit UI:

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
- **Pull the required Ollama model**: `ollama pull llama3.2` — needed for the LLM‑backed agents.

## Key Files to Know

- `app.py` — the Streamlit app; changing UI flow or pages goes here.
- `src/agents/*.py` — the four AI agents; each implements a `crewai` agent definition.
- `src/crew/fencing_crew.py` — ties the agents together into a crew and defines the task flow.
- `config/fencing_rules.json` — the rule set the referee uses to score touches.
- `tests/` — pytest suite; adding a new test usually means adding a file or function here.