# UFence - Fencing Exchange Simulator

AI-powered fencing exchange simulation with role-based agents using CrewAI and Ollama.

## Overview

UFence simulates a complete fencing match with three distinct AI agents:
- **Fencer** - You control the fencer through actions
- **Opponent** - Adaptive AI opponent that learns from your patterns
- **Referee** - Makes official decisions based on right-of-way rules
- **Coach** - Provides post-match analysis and feedback

## Requirements

- Python 3.10+
- Ollama installed with llama3.2 model
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

# Install Ollama and pull the model
# (Follow instructions at https://ollama.ai)
ollama pull llama3.2
```

## Running the Application

```bash
streamlit run app.py
```

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
