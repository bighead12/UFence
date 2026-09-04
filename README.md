# UFence - Fencing Exchange Simulator

AI-powered fencing exchange simulation with role-based agents using CrewAI and OpenRouter.

## Overview

UFence simulates a complete fencing match with three distinct AI agents:
- **Fencer** - You control the fencer through actions
- **Opponent** - Adaptive AI opponent that learns from your patterns
- **Referee** - Makes official decisions based on right-of-way rules
- **Coach** - Provides post-match analysis and feedback

## Requirements

- Python 3.10+
- An [OpenRouter](https://openrouter.ai) API key (sign up free at openrouter.ai/keys)
- See `requirements.txt` for Python dependencies

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd ufence

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# Unix/MacOS
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## API Key Setup

Sign up at [openrouter.ai/keys](https://openrouter.ai/keys), then either:

```bash
# Option A: put it in your environment / .env file
echo "OPENROUTER_API_KEY=sk-or-..." > .env
```

or paste the key into the **🔑 OpenRouter API Key** field in the app's
sidebar. You can also pick a different model from the sidebar dropdown —
OpenRouter gives you one key for Anthropic, Google, OpenAI, Meta, and many
more. Free models (e.g. `meta-llama/llama-3.1-8b-instruct:free`) are
available with no billing required.

## Running the Application

```bash
streamlit run app.py
```

> ℹ️ The Arena, action buttons, scoring, history, and post-match analysis all
> work **without** an API key — only natural-language intent parsing and the
> RAG-backed Coach Chat need OpenRouter.

## How to Play

1. Click "Start New Match"
2. The match is first to 5 touches
3. Select your fencing action from the dropdown
4. Click "Execute Action" to fence
5. The opponent will respond with an action
6. The referee will judge who scores
7. After the match, the coach provides analysis

## Action Types

| Action | Description |
|--------|-------------|
| Direct Attack | Simple thrust to target |
| Compound Attack | Multiple feints followed by final thrust |
| Fleche | Running attack |
| Parry & Riposte | Defensive parry followed by counter-attack |
| Counter-Attack | Attack into opponent's attack |
| Remise | Immediate follow-up |
| Prise de Fer | Taking opponent's blade |

## Project Structure

```
ufence/
├── app.py                    # Streamlit web interface
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
├── tests/                   # Test files
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Development

### Running Tests

```bash
pytest
```

### Linting

```bash
ruff check .
```

## License

MIT

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/bighead12/UFence)
