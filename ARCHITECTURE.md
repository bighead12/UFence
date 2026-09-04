# UFence — Architecture Documentation

## 1. Project Overview

UFence is an AI-powered fencing exchange simulator that orchestrates four role-based agents through a Streamlit web interface. The system simulates foil fencing matches where a human-controlled fencer faces an adaptive AI opponent, with an automated referee enforcing right-of-way rules and a coach providing post-match analysis and interactive Q&A.

The system uses **LiteLLM** to call **Google Gemini 2.5 Flash** (previously Ollama llama3.2) for the referee interpretation and coach feedback/chat functions. The opponent agent uses a deterministic pattern-learning algorithm rather than an LLM.

---

## 2. Top-Level Project Structure

```
ufence/
├── app.py                          # Streamlit UI — single-page application entry point
├── pyproject.toml                  # Project metadata, dependencies, tool config
├── requirements.txt                # Pinned Python dependencies
├── README.md                       # User-facing documentation
├── .env / .env.example             # Environment variables (Gemini API key)
├── .github/workflows/ci.yml        # GitHub Actions CI (test + lint)
├── config/
│   └── fencing_rules.json          # Complete foil fencing rules knowledge base
├── data/
│   ├── books/                      # PDF/TXT source books for RAG (e.g., foil1.txt)
│   └── vectorstore/                # Persistent ChromaDB storage (binary files + SQLite)
├── scripts/
│   └── transcribe_books.py         # Multimodal Gemini OCR transcription pipeline
├── src/
│   ├── __init__.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── fencer.py               # FencerAgent
│   │   ├── opponent.py             # OpponentAgent
│   │   ├── referee.py              # RefereeAgent
│   │   └── coach.py                # CoachAgent
│   ├── crew/
│   │   ├── __init__.py
│   │   └── fencing_crew.py         # FencingCrew orchestrator
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── config.py               # Configuration constants and helpers
│   │   └── logging.py              # Logger factory
│   ├── knowledge/
│   │   ├── __init__.py
│   │   ├── ingest.py               # PDF/TXT ingestion → ChromaDB pipeline
│   │   └── retriever.py            # ChromaDB vector retriever
│   └── visualization/
│       ├── __init__.py
│       ├── animator.py             # CSS-keyframe animation HTML generators
│       ├── fencer_svg.py           # Arena rendering (distance, actions, score)
│       └── history.py              # Exchange history panel + matplotlib charts
└── tests/
    ├── test_agents.py              # Unit tests for individual agents
    ├── test_coach_chat.py          # Tests for RAG ingestion, retrieval, chat
    ├── test_fencing_crew.py        # Integration tests for FencingCrew
    └── test_score_bug.py           # Regression test for score consistency bug
```

---

## 3. Configuration and Rules System

### 3.1 `src/utils/config.py` — Central Configuration

**Purpose**: Singleton configuration module loaded at import time. Reads from environment variables (via `python-dotenv`) and defines all runtime constants.

**Key constants**:
| Constant | Default | Purpose |
|---|---|---|
| `GEMINI_MODEL` | `"gemini/gemini-2.5-flash"` | LLM model identifier for LiteLLM calls |
| `WINNING_SCORE` | `5` | Score required to win a match |
| `LOG_LEVEL` | `"INFO"` | Python logging level |
| `BOOKS_DIR` | `data/books` | Directory for source PDFs/TXTs |
| `VECTORSTORE_DIR` | `data/vectorstore` | Persistent ChromaDB storage path |
| `EMBEDDING_MODEL` | `"all-MiniLM-L6-v2"` | Sentence-transformer model for embeddings |
| `CHUNK_SIZE` | `500` | Word count per text chunk |
| `CHUNK_OVERLAP` | `50` | Overlapping words between chunks |
| `RAG_TOP_K` | `5` | Number of retrieval results |

**Key function**: `get_rules()` — reads and returns the parsed `config/fencing_rules.json` dictionary. Called each time a `RefereeAgent` is instantiated.

**Dependencies**: `dotenv`, `pathlib`, standard `os` and `json`.

---

### 3.2 `config/fencing_rules.json` — Fencing Rules Knowledge Base

**Purpose**: Authoritative JSON rule set for foil fencing. Used by the referee for right-of-way determination and target validation, and by the knowledge base fallback ingestion.

**Top-level structure**:
```json
{
  "weapon": "foil",
  "valid_target_areas": ["torso", "back", "shoulders", "groin"],
  "invalid_target_areas": ["head", "arms", "legs", "hands"],
  "right_of_way_rules": { ... },
  "infractions": { ... },
  "actions": { ... },
  "referee_commands": { "halts": ["Halt!", "En garde!", "Allez!", "Ecart!"] },
  "scoring": { "touch_value": 1, "winning_score": 5, ... }
}
```

**Right-of-way logic** (`right_of_way_rules`):
- **`priority_attacks`** (ordered list): `direct-attack`, `compound-attack`, `fleche`, `counter-attack`, `remise`, `prise-de-fer`, `parry-and-riposte` — these have highest priority.
- **`secondary_actions`**: `parry`, `riposte`, `counter-parry` — beat non-priority actions.
- When both fencers use priority actions, winner is determined by list index order (lower index wins). Same index = simultaneous.

**Actions taxonomy** (`actions`): Three categories — `attacks` (direct_attack, compound_attack, fleche), `defenses` (parry, evasion), `counter_actions` (riposte, counter_attack), and `advanced` (remise, prise_de_fer). Each action has a `priority` field (`high`, `medium`, `secondary`).

---

## 4. Agent Components

### 4.1 `src/agents/fencer.py` — FencerAgent

**Purpose**: Represents the user-controlled fencer. Executes validated fencing actions and tracks action history for side-alternation logic.

**Key class**: `FencerAgent`

**State**:
- `action_history: list[dict]` — each entry is `{"type": str, "target": str, "side": str}`

**Key methods**:
| Method | Parameters | Returns | Description |
|---|---|---|---|
| `execute_action(action_type, target)` | `action_type: str`, `target: str \| None` | `dict` | Creates action dict with alternating `"side"` (right/left), appends to history |
| `_get_opposite_side()` | — | `str` | Alternates between `"right"` and `"left"` based on last action |
| `get_valid_actions()` | — | `list[str]` | 7 valid actions |
| `get_valid_targets()` | — | `list[str]` | `["torso", "back", "shoulders"]` |
| `reset()` | — | `None` | Clears `action_history` |

**Valid actions**: `direct_attack`, `compound_attack`, `fleche`, `parry_and_riposte`, `counter_attack`, `remise`, `prise_de_fer`

**Dependencies**: `src/utils.logging`

**Integration points**: Called by `FencingCrew.execute_exchange()` with user-supplied action/target. The `side` field alternates to simulate left/right line changes.

---

### 4.2 `src/agents/opponent.py` — OpponentAgent

**Purpose**: Adaptive AI opponent that learns the human fencer's patterns and exploits predictable behavior. Uses a deterministic state machine with two phases rather than an LLM.

**Key class**: `OpponentAgent`

**State**:
| Field | Type | Description |
|---|---|---|
| `action_history` | `list[dict]` | All actions taken this match |
| `fencer_patterns` | `list[str]` | Types of fencer actions observed |
| `phase` | `str` | `"learning"` (first 2 exchanges) or `"adapting"` |
| `exchange_count` | `int` | Number of exchanges processed |
| `pattern_counts` | `dict[str, int]` | Frequency count of fencer action types |

**Key methods**:
| Method | Parameters | Returns | Description |
|---|---|---|---|
| `init_exchange()` | — | `None` | Resets `action_history`, increments counter, transitions phase after 2 exchanges |
| `execute_action(fencer_action)` | `fencer_action: dict \| None` | `dict` | If fencer_action provided, learns pattern. Then selects action based on phase |
| `_random_action()` | — | `dict` | Weighted random choice from 5 action types |
| `_learn_pattern(fencer_action)` | `fencer_action: dict` | `None` | Appends to `fencer_patterns`, increments `pattern_counts` |
| `_adaptive_action()` | — | `dict` | If a pattern is predictable (>threshold), exploits it; otherwise strategic random |
| `_exploit_weakness(common_action)` | `common_action: str` | `dict` | Counter-mapping: direct_attack→counter_attack, fleche→parry_and_riposte, etc. |
| `_strategic_action()` | — | `dict` | Random from 5 actions with varied targets |
| `get_valid_actions()` | — | `list[str]` | 6 valid actions (no `prise_de_fer`) |
| `reset()` | — | `None` | Clears all state to initial values |

**Adaptive algorithm**: After 2 exchanges, the opponent calculates the predictability ratio of the fencer's most common action. If `random() < min(predictability, 0.7)`, it exploits that action using a hardcoded counter-map. Otherwise, it makes a strategic random choice.

**Dependencies**: `src/utils.logging`

**Integration points**: Called by `FencingCrew.execute_exchange()` after the fencer's action is known. This ordering allows the opponent to observe the fencer's move before selecting its counter.

---

### 4.3 `src/agents/referee.py` — RefereeAgent

**Purpose**: Enforces foil fencing rules — determines right-of-way, validates targets, scores touches, and maintains match state.

**Key class**: `RefereeAgent`

**State**:
| Field | Type | Description |
|---|---|---|
| `rules` | `dict` | Parsed `fencing_rules.json` |
| `score` | `dict[str, int]` | `{"fencer": 0, "opponent": 0}` |
| `penalty_stack` | `list[str]` | Penalty card history |
| `current_call` | `dict \| None` | Result of last judge_action |
| `exchange_history` | `list[dict]` | Complete record of all exchanges |

**Key methods**:
| Method | Parameters | Returns | Description |
|---|---|---|---|
| `judge_action(fencer_action, opponent_action)` | Two `dict`s | `dict` | Core scoring logic — returns full result dict with call, scores, validity, match-over flag |
| `_determine_winner(fencer_type, opponent_type)` | Two `str` | `str` | Right-of-way resolution: `"fencer"`, `"opponent"`, or `"simultaneous"` |
| `_normalize_action(action)` | `str` | `str` | Converts `"direct_attack"` → `"direct-attack"` to match JSON keys |
| `_is_valid_target(target)` | `str` | `bool` | Checks against `valid_target_areas` from rules |
| `_get_call_reason(call, fencer_type, opponent_type)` | Three `str` | `str` | Human-readable reason for the call |
| `_is_match_over()` | — | `bool` | Score >= WINNING_SCORE |
| `get_match_result()` | — | `dict` | Returns `{"winner": str, "final_score": dict}` |
| `get_halt_command()` | — | `str` | Returns first referee command |
| `reset()` | — | `None` | Clears all state |

**Right-of-way algorithm** (`_determine_winner`):
1. Normalize action names (underscore → hyphen) to match `fencing_rules.json` keys
2. Check if each action is in `priority_attacks` or `secondary_actions`
3. Priority beats everything; secondary beats non-priority non-secondary
4. Both priority: lower index in `priority_attacks` wins; same index = simultaneous
5. Both secondary: same logic using `secondary_actions` index
6. Neither priority/secondary = simultaneous (no score in foil)

**Foil-specific rule**: Simultaneous hits award no points (unlike sabre/épée). Invalid targets also result in no score even if the attacker had priority.

**Result dict structure**:
```python
{
    "call": "fencer" | "opponent" | "simultaneous",
    "fencer_hit": bool,
    "opponent_hit": bool,
    "fencer_valid": bool,
    "opponent_valid": bool,
    "fencer_score": 0 | 1,
    "opponent_score": 0 | 1,
    "score": {"fencer": int, "opponent": int},
    "reason": str,
    "is_match_over": bool,
}
```

**Dependencies**: `src.utils.config` (for `get_rules()`), `src.utils.logging`

**Integration points**: The central decision node. Called by `FencingCrew.execute_exchange()`. Its `score` and `exchange_history` are read by the Coach and displayed by the UI.

---

### 4.4 `src/agents/coach.py` — CoachAgent

**Purpose**: Provides post-match analysis and interactive Q&A. Has two distinct modes: (1) **rule-based analysis** of exchange history, and (2) **LLM-powered chat** with RAG retrieval from fencing books.

**Key class**: `CoachAgent`

**State**:
| Field | Type | Description |
|---|---|---|
| `feedback_history` | `list[dict]` | Accumulated analysis results from matches |
| `chat_history` | `list[dict]` | Chat turn history for multi-turn conversation |

**Key methods**:

**Mode 1 — `analyze_exchange(exchange_history, score)`**:
| Aspect | Details |
|---|---|
| Returns | `dict` with keys: `summary`, `technical`, `strategic`, `tactical`, `recommendations`, `score_analysis` |
| Technical analysis | Detects fleche overuse (>30%), direct attack predictability (>50%), missing parry-riposte, counter-attack frequency |
| Strategic analysis | Detects limited target selection (>70% torso), no lateral movement (no side changes) |
| Tactical analysis | Win rate (<40% triggers warning), simultaneous hits (>30%), priority action frequency |
| Recommendations | Context-dependent: advice for winning vs losing, suggests fleche if unused |

**Mode 2 — `chat(question, retrieved_passages, exchange_history, score)`**:
| Aspect | Details |
|---|---|
| LLM call | `litellm.completion(model=GEMINI_MODEL, messages=..., max_tokens=800)` |
| System prompt | Expert fencing coach persona + RAG passages + match context + latest feedback |
| Context window | Last 6 chat messages (3 exchanges) for conversational continuity |
| Error handling | Catches `KeyError, ValueError, ConnectionError, TypeError` — returns friendly error message |
| Returns | `{"answer": str, "sources": list[dict]}` with source citations |

**Helper methods**:
- `_build_match_context(exchange_history, score)` — Formats last 5 exchanges for the LLM prompt
- `format_passages_for_prompt(passages)` — (in Retriever, called here) — formats retrieved chunks for the prompt

**Dependencies**: `litellm`, `src.utils.config` (for `GEMINI_MODEL`), `src.utils.logging`, `src.knowledge.retriever.BookRetriever` (lazy import)

**Integration points**: Called by `FencingCrew.execute_exchange()` when match ends. Called by `FencingCrew.coach_chat()` for the Chat interface. The chat uses the `BookRetriever` passed from the Streamlit app.

---

## 5. FencingCrew — Orchestration Layer

**File**: `src/crew/fencing_crew.py`

**Purpose**: Central orchestrator that coordinates all four agents, manages match lifecycle, and exposes the interface used by the Streamlit UI.

**Key class**: `FencingCrew`

**State**:
| Field | Type | Description |
|---|---|---|
| `fencer` | `FencerAgent` | User-controlled fencer |
| `opponent` | `OpponentAgent` | Adaptive AI opponent |
| `referee` | `RefereeAgent` | Rule enforcement and scoring |
| `coach` | `CoachAgent` | Analysis and chat |
| `exchange_number` | `int` | Current exchange counter |
| `current_opponent_action` | `dict \| None` | Cached opponent intent for UI display |
| `current_distance` | `str \| None` | `"close"`, `"medium"`, or `"far"` |

**Key methods**:
| Method | Parameters | Returns | Description |
|---|---|---|---|
| `start_new_match()` | — | `dict` | Resets all agents, generates initial opponent intent, returns match metadata |
| `_generate_opponent_intent()` | — | `None` | Initializes opponent exchange and picks random distance |
| `get_opponent_intent()` | — | `dict` | Returns `{"action": dict, "distance": str}` for UI rendering |
| `execute_exchange(fencer_action, target)` | `str`, `str` | `dict` | Core loop: init opponent → execute fencer → opponent responds → referee judges → coach feedback if match over |
| `interpret_user_intent(user_message)` | `str` | `tuple[str, str]` | Calls LiteLLM to parse natural language into `{action, target}` JSON |
| `coach_chat(question, retriever)` | `str`, `BookRetriever` | `dict` | Retrieves passages, delegates to `CoachAgent.chat()` |
| `get_current_state()` | — | `dict` | Returns score, exchange count, history, match-over flag |
| `get_coach_feedback()` | — | `dict` | Delegates to `CoachAgent.analyze_exchange()` |

**Exchange execution flow** (`execute_exchange`):
```
1. increment exchange_number
2. opponent.init_exchange()  — reset action_history for this exchange
3. fencer.execute_action(fencer_action_type, target)  — user's action
4. opponent.execute_action(fencer_action_dict)  — opponent sees fencer's move, then responds
5. referee.judge_action(fencer_action_dict, opponent_action)  — determine winner
6. Build response dict with exchange_number, actions, referee_call, score, match_over
7. If match_over: get match_result, run coach.analyze_exchange(), attach feedback
8. Else: call _generate_opponent_intent() for next exchange display
```

**Natural language interpretation** (`interpret_user_intent`):
- Builds a prompt constraining the LLM to output ONLY `{"action": "...", "target": "..."}` JSON
- Calls `litellm.completion` with `max_tokens=50`
- Parses JSON from the response (handles markdown code blocks)
- Validates against `fencer.get_valid_actions()` and `fencer.get_valid_targets()`
- Falls back to `{"direct_attack", "torso"}` on any parse error

**Dependencies**: All four agent classes, `src.utils.config` (for `WINNING_SCORE`), `src.utils.logging`

---

## 6. Data Flow Between Components

```
┌─────────────┐     user message     ┌──────────────────────┐
│  Streamlit   │ ────────────────────▶│     FencingCrew       │
│   UI/app.py │ ◀─────────────────── │  (orchestrator)       │
└─────────────┘     action/score     └──────────┬───────────┘
                                                 │
              ┌──────────────────────────────────┼──────────────────┐
              │                                  │                  │
              ▼                                  ▼                  ▼
     ┌──────────────┐                 ┌──────────────┐   ┌──────────────┐
     │ FencerAgent  │                 │ OpponentAgent│   │ RefereeAgent │
     │  (user)      │ ◀── action ─────│  (AI)        │──▶│  (rules)     │
     │              │  target ──────▶ │  learns      │   │  scores      │
     │ valid_actions│                 │  patterns    │   │  history     │
     │ valid_targets│                 │  adapts      │   │  score       │
     └──────────────┘                 └──────────────┘   └──────┬───────┘
                                                                │
                                                                ▼
     ┌──────────────┐         ┌──────────────┐         ┌──────────────┐
     │  visualization│◀───────│  exchange    │◀───────│   CoachAgent │
     │  fencer_svg   │  state │  results     │  feedback│ (analysis)  │
     │  animator     │        │  dict        │        │ (RAG chat)  │
     │  history      │        └──────────────┘        └──────────────┘
     └──────────────┘
                │
                ▼
     ┌──────────────────┐       ┌──────────────┐
     │  knowledge/      │◀──────│  BookRetriever│
     │  ingest.py       │  PDFs │  (ChromaDB)   │
     │  retriever.py    │──────▶│  (vector store)│
     └──────────────────┘       └──────────────┘
```

**Data flow summary**:

1. **User input** → Streamlit UI → `FencingCrew.interpret_user_intent()` → returns `(action, target)` tuple → `FencingCrew.execute_exchange(action, target)`
2. **Execute exchange**: Creates `fencer_action` dict → `opponent.execute_action(fencer_action)` learns pattern → `referee.judge_action()` returns result → score accumulates
3. **Display**: `FencingCrew.get_opponent_intent()` provides opponent action + distance to `render_fencer_arena()` → UI renders arena with score
4. **Match end**: When `score >= WINNING_SCORE`, `coach.analyze_exchange()` produces feedback with `technical`, `strategic`, `tactical`, `recommendations` arrays
5. **Coach chat**: User question → `FencingCrew.coach_chat()` → `BookRetriever.retrieve()` → `CoachAgent.chat()` → LLM call with RAG context → answer + sources
6. **History**: Each `execute_exchange` result is appended to `st.session_state.exchange_results` → `render_history_panel()` renders timeline, stats, and matplotlib score chart

---

## 7. Knowledge Base (RAG System)

### 7.1 `src/knowledge/ingest.py` — Ingestion Pipeline

**Purpose**: Extracts text from PDFs and TXT files, chunks it, embeds it, and stores it in a persistent ChromaDB collection. Falls back to rules-based content when no PDFs are available.

**Key functions**:
| Function | Parameters | Returns | Description |
|---|---|---|---|
| `extract_text_from_pdf(pdf_path)` | `Path` | `str` | Uses PyMuPDF (`fitz`) to extract text with `[Page N]` markers |
| `chunk_text(text, source_name, chunk_size, overlap)` | `str`, `str`, `int`, `int` | `list[dict]` | Word-level chunking with metadata (source, chunk_index, page) |
| `_extract_page_number(text)` | `str` | `int` | Regex to find `[Page N]` markers |
| `ingest_books(books_dir, vectorstore_dir)` | `Path`, `Path` | `chromadb.Collection` | Main ingestion entry point — handles TXT/PDF, idempotent, batch adds (500/batch) |
| `_ingest_rules_fallback(collection)` | `chromadb.Collection` | `int` | Ingest `fencing_rules.json` content when PDFs are scanned/empty |
| `get_ingestion_status(books_dir, vectorstore_dir)` | `Path`, `Path` | `dict` | Returns `{pdf_files, ingested_sources, pending, total_chunks}` |

**Chunking algorithm**: Word-level sliding window. `start=0`, `end=start+chunk_size`, slide by `end-overlap`. Each chunk gets metadata: `source`, `chunk_index`, `page` (extracted from `[Page N]` markers).

**Idempotency**: Checks `existing_sources` in the collection before ingesting; skips already-ingested files. Prefers `.txt` over `.pdf` if both exist for the same stem.

---

### 7.2 `src/knowledge/retriever.py` — Vector Retriever

**Purpose**: Lazy-loaded wrapper around ChromaDB for semantic retrieval of fencing knowledge.

**Key class**: `BookRetriever`

**Key attributes**:
- `_collection: chromadb.Collection | None` — the ChromaDB collection
- `_ready: bool` — whether the collection was successfully loaded
- `_vectorstore_dir: Path` — path to persistent ChromaDB

**Key methods**:
| Method | Parameters | Returns | Description |
|---|---|---|---|
| `_ensure_loaded()` | — | `None` | Lazy-initializes ChromaDB client + collection with SentenceTransformerEmbeddingFunction |
| `is_ready` | — | `bool` | Property that calls `_ensure_loaded()` |
| `document_count` | — | `int` | Property returning collection count |
| `retrieve(query, top_k)` | `str`, `int` | `list[dict]` | ChromaDB `collection.query()` returning passages with text, source, page, chunk_index, distance |
| `format_passages_for_prompt(passages)` | `list[dict]` | `str` | Formats passages into `--- Reference N (from: source, p. N) ---\ntext` blocks |

**Embedding**: Uses `SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")` via ChromaDB's `embedding_functions` module.

**Retrieval**: Uses `collection.query(query_texts=[query], n_results=min(top_k, count), include=["documents", "metadatas", "distances"])`.

---

## 8. Visualization Layer

### 8.1 `src/visualization/fencer_svg.py` — Arena Renderer

**Function**: `render_fencer_arena(distance, opponent_action, score, last_result)`

**Purpose**: Renders the main arena view showing both fencers, the distance indicator, opponent action, score metrics, and last-result feedback. Uses `st.columns` layout with a dark-themed HTML container.

**Distance symbols**: `"far"` → `"━━━━━━━"`, `"medium"` → `"━━━━━"`, `"close"` → `"━━━"`

**Action icons**: Maps action types to emoji (🗡️, 🔱, 🏃, 🛡️, ⚡, ↩️, ✋)

**Returns**: `FencerVisualizer` instance (a stateful object storing `animation_state`, `last_result`, `score`)

---

### 8.2 `src/visualization/animator.py` — CSS Animation Generator

**Purpose**: Generates standalone HTML+CSS strings for exchange animations using CSS `@keyframes`. All animations are self-contained with no external dependencies.

**Key data**:
- `CSS_KEYFRAMES`: Global `<style>` block with 12 animation keyframes
- `ACTION_ANIMATIONS`: Maps each action type to emoji + CSS animation class + display name
- 7 CSS keyframe animations: `thrust-right`, `thrust-left`, `fleche-run`, `parry-deflect`, `counter-quick`, `remise-push`, `prise-grab`, plus score flash animations (`score-flash-green/red/yellow`) and effects (`pulse-glow`, `shake`, `bounce`)

**Key functions**:
| Function | Returns | Description |
|---|---|---|
| `render_complete_animation(fencer_action, opponent_action, call_result, your_score, opp_score)` | `str` | Full animation: fencers approaching, action emojis, result banner |
| `render_engaging_animation()` | `str` | Pulsing ⚔️ "FENCERS ENGAGE!" screen |
| `render_action_animation(your_action, opp_action)` | `str` | Side-by-side action animation |
| `render_result_animation(call_result, your_score, opp_score)` | `str` | Result-only animation with score |
| `get_action_animation(action_type)` | `dict` | Helper to get emoji + animation class + name |

---

### 8.3 `src/visualization/history.py` — History Panel

**Key class**: `HistoryPanel`

| Method | Description |
|---|---|
| `add_exchange(exchange_num, fencer_action, opponent_action, result)` | Appends to internal exchanges list |
| `render_timeline()` | Shows last 5 exchanges in expandable containers |
| `render_score_chart()` | Matplotlib line chart of cumulative score progression |
| `render_stats()` | Metrics: total exchanges, wins, opponent wins, win rate |
| `get_score_history()` | Returns cumulative scores for charting |
| `clear()` | Resets exchanges list |

**Standalone function**: `render_history_panel(exchange_results)` — constructs a `HistoryPanel`, populates it from `exchange_results` dicts, renders in a 2-column Streamlit layout with timeline, stats, and score chart.

---

## 9. Utility Infrastructure

### 9.1 `src/utils/logging.py` — Logger Factory

**Function**: `get_logger(name)` — returns a configured `logging.Logger`. Uses a module-level handler cache to prevent duplicate handlers. Format: `"%(asctime)s - %(name)s - %(levelname)s - %(message)s"`. Level controlled by `LOG_LEVEL` from config.

---

### 9.2 Environment Configuration

**`.env.example`** and **`.env`**: Store `GEMINI_API_KEY`. The Streamlit sidebar also provides a runtime input for the API key, which is set into `os.environ["GEMINI_API_KEY"]` if provided.

---

## 10. Key Architectural Patterns

### 10.1 Stateless Agents, Stateful Crew
Each agent class is a simple Python object with no framework dependencies. The `FencingCrew` class owns all agent instances and manages their lifecycle. Agents are created in `FencingCrew.__init__()` and reset via `start_new_match()`.

### 10.2 Streamlit Session State Pattern
The entire application state lives in `st.session_state`:
- `st.session_state.crew` — the `FencingCrew` instance
- `st.session_state.exchange_results` — list of exchange result dicts
- `st.session_state.messages` — chat messages for the arena tab
- `st.session_state.coach_messages` — chat messages for the coach tab
- `st.session_state.last_result` — last referee call for animation
- `st.session_state.book_retriever` — lazy `BookRetriever` instance
- `st.session_state.match_started` — boolean flag

### 10.3 Lazy Initialization
- `BookRetriever._ensure_loaded()` — loaded on first `retrieve()` or `is_ready` access
- `st.session_state.book_retriever` — initialized on first chat access
- ChromaDB collection — created on first ingestion or retrieval

### 10.4 Fallback Chain for Coach Knowledge
1. Try to ingest user-provided PDFs/TXTs into ChromaDB
2. If no files found, ingest `fencing_rules.json` as fallback
3. If PDFs are scanned/image-only (PyMuPDF returns empty text), fall back to rules ingestion
4. If LLM call fails, return a friendly error message (no crash)

### 10.5 Deterministic Opponent AI
The opponent does not use an LLM. It uses a 2-phase state machine:
- **Phase 1 (learning)**: Random actions for the first 2 exchanges
- **Phase 2 (adapting)**: Analyzes fencer patterns and exploits the most common action with a probability capped at 70% predictability

### 10.6 Configuration Over Code
- `WINNING_SCORE` is configurable via env var `WINNING_SCORE` (default 5)
- `GEMINI_MODEL` is configurable via env var (default `"gemini/gemini-2.5-flash"`)
- RAG parameters (`CHUNK_SIZE`, `CHUNK_OVERLAP`, `RAG_TOP_K`, `EMBEDDING_MODEL`) are all env-configurable

---

## 11. Testing Architecture

**Test framework**: `pytest` with `pytest-asyncio`

**Test files**:
| File | Coverage |
|---|---|
| `tests/test_agents.py` | Unit tests for all four agents — action execution, valid lists, basic scoring |
| `tests/test_fencing_crew.py` | Integration tests — match lifecycle, score consistency, right-of-way rules, end-to-end match play, multiple matches |
| `tests/test_coach_chat.py` | RAG pipeline tests — chunking, ingestion status, retriever behavior, coach chat with mocked LLM, fallback on error |
| `tests/test_score_bug.py` | Regression tests — score consistency between `referee.score` and `result['score']` |

**Notable test class**: `TestRightOfWayRules` and `TestEndToEndMatch` in `test_fencing_crew.py` — these directly verify the fencing rule implementation and full match completion.

---

## 12. Dependencies Overview

| Dependency | Used by | Purpose |
|---|---|---|
| `litellm` | `CoachAgent`, `FencingCrew.interpret_user_intent()` | Unified LLM API (Google Gemini 2.5 Flash) |
| `streamlit` | `app.py`, `fencer_svg.py`, `history.py` | Web UI framework |
| `chromadb` | `retriever.py`, `ingest.py` | Vector database for RAG |
| `sentence-transformers` | `ingest.py`, `retriever.py` | Embedding model (`all-MiniLM-L6-v2`) |
| `PyMuPDF` | `ingest.py`, `transcribe_books.py` | PDF text extraction |
| `python-dotenv` | `config.py`, `transcribe_books.py` | Environment variable loading |
| `matplotlib` | `history.py` | Score progression chart |
| `pytest` | `tests/` | Test framework |
| `crewai` | `pyproject.toml` (declared, not heavily used in current code) | Agent framework (mentioned in README) |
| `google-generativeai` | `transcribe_books.py` | Multimodal PDF transcription |