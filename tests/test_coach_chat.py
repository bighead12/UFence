"""
Tests for the Coach Chat RAG pipeline.

Covers: PDF text extraction, chunking, ingestion, retrieval,
coach chat prompt building, and fallback behavior.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.knowledge.ingest import (
    extract_text_from_pdf,
    chunk_text,
    ingest_books,
    get_ingestion_status,
)
from src.knowledge.retriever import BookRetriever
from src.agents.coach import CoachAgent


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_text():
    """A block of sample fencing text for testing chunking."""
    return (
        "[Page 1]\n"
        "Fencing is a group of three related combat sports. "
        "The three disciplines in modern fencing are the foil, the épée, "
        "and the sabre. Each discipline uses a different kind of blade "
        "and has different rules. " * 20
        + "\n[Page 2]\n"
        + "The right of way rule is fundamental in foil fencing. "
        "It determines which fencer scores a touch when both fencers "
        "hit each other within the allowed time frame. " * 20
    )


@pytest.fixture
def coach():
    """A fresh CoachAgent instance."""
    return CoachAgent()


@pytest.fixture
def mock_exchange_history():
    """Sample exchange history for testing."""
    return [
        {
            "fencer_action": {"type": "direct_attack", "target": "torso", "side": "right"},
            "opponent_action": {"type": "parry_and_riposte", "target": "torso"},
            "result": {
                "call": "opponent",
                "fencer_hit": False,
                "opponent_hit": True,
                "score": {"fencer": 0, "opponent": 1},
            },
        },
        {
            "fencer_action": {"type": "fleche", "target": "shoulders", "side": "left"},
            "opponent_action": {"type": "counter_attack", "target": "torso"},
            "result": {
                "call": "fencer",
                "fencer_hit": True,
                "opponent_hit": False,
                "score": {"fencer": 1, "opponent": 1},
            },
        },
    ]


# ---------------------------------------------------------------------------
# Task 2 tests: Ingestion
# ---------------------------------------------------------------------------

class TestChunkText:
    def test_basic_chunking(self, sample_text):
        chunks = chunk_text(sample_text, "test_book.pdf", chunk_size=100, overlap=10)
        assert len(chunks) > 0
        assert all(c["metadata"]["source"] == "test_book.pdf" for c in chunks)

    def test_chunk_indices_are_sequential(self, sample_text):
        chunks = chunk_text(sample_text, "test.pdf", chunk_size=50, overlap=5)
        indices = [c["metadata"]["chunk_index"] for c in chunks]
        assert indices == list(range(len(chunks)))

    def test_chunk_overlap(self, sample_text):
        """Chunks should share some words due to overlap."""
        chunks = chunk_text(sample_text, "test.pdf", chunk_size=50, overlap=10)
        if len(chunks) >= 2:
            words_0 = set(chunks[0]["text"].split()[-10:])
            words_1 = set(chunks[1]["text"].split()[:10])
            # At least some overlap words should be shared
            assert len(words_0 & words_1) > 0

    def test_empty_text(self):
        chunks = chunk_text("", "empty.pdf")
        assert chunks == []

    def test_page_number_extraction(self, sample_text):
        chunks = chunk_text(sample_text, "test.pdf", chunk_size=100, overlap=10)
        # At least one chunk should have a page number > 0
        pages = [c["metadata"]["page"] for c in chunks]
        assert any(p > 0 for p in pages)


class TestIngestionStatus:
    def test_empty_directory(self, tmp_path):
        books_dir = tmp_path / "books"
        books_dir.mkdir()
        vs_dir = tmp_path / "vectorstore"

        status = get_ingestion_status(books_dir, vs_dir)
        assert status["pdf_files"] == []
        assert status["total_chunks"] == 0


# ---------------------------------------------------------------------------
# Task 3 tests: Retriever
# ---------------------------------------------------------------------------

class TestBookRetriever:
    def test_not_ready_when_no_vectorstore(self, tmp_path):
        retriever = BookRetriever(
            vectorstore_dir=tmp_path / "nonexistent",
            embedding_model="all-MiniLM-L6-v2",
        )
        assert retriever.is_ready is False

    def test_retrieve_returns_empty_when_not_ready(self, tmp_path):
        retriever = BookRetriever(
            vectorstore_dir=tmp_path / "nonexistent",
            embedding_model="all-MiniLM-L6-v2",
        )
        results = retriever.retrieve("test query")
        assert results == []

    def test_format_passages_empty(self):
        retriever = BookRetriever()
        formatted = retriever.format_passages_for_prompt([])
        assert "No reference material" in formatted

    def test_format_passages_with_data(self):
        retriever = BookRetriever()
        passages = [
            {"text": "Sample passage text", "source": "book.pdf", "page": 42, "chunk_index": 0, "distance": 0.5},
        ]
        formatted = retriever.format_passages_for_prompt(passages)
        assert "book.pdf" in formatted
        assert "p. 42" in formatted
        assert "Sample passage text" in formatted


# ---------------------------------------------------------------------------
# Task 4 tests: Coach Chat
# ---------------------------------------------------------------------------

class TestCoachChat:
    def test_build_match_context_no_history(self, coach):
        ctx = coach._build_match_context([], {"fencer": 0, "opponent": 0})
        assert "No match data" in ctx

    def test_build_match_context_with_history(self, coach, mock_exchange_history):
        ctx = coach._build_match_context(
            mock_exchange_history,
            {"fencer": 1, "opponent": 1},
        )
        assert "1 - Opponent 1" in ctx
        assert "direct_attack" in ctx
        assert "fleche" in ctx

    @patch("src.agents.coach.litellm")
    def test_chat_calls_llm(self, mock_litellm, coach, mock_exchange_history):
        """Verify the chat method calls litellm with proper message structure."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Great question! Let me explain..."
        mock_litellm.completion.return_value = mock_response

        passages = [
            {"text": "Parry technique info", "source": "foil_guide.pdf", "page": 10, "chunk_index": 3, "distance": 0.2},
        ]

        result = coach.chat(
            question="Why did my parry fail?",
            retrieved_passages=passages,
            exchange_history=mock_exchange_history,
            score={"fencer": 1, "opponent": 1},
        )

        assert "answer" in result
        assert "sources" in result
        assert result["answer"] == "Great question! Let me explain..."
        assert len(result["sources"]) == 1
        assert result["sources"][0]["source"] == "foil_guide.pdf"

    @patch("src.agents.coach.litellm")
    def test_chat_stores_history(self, mock_litellm, coach, mock_exchange_history):
        """Verify chat history is stored for multi-turn support."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Here's my advice..."
        mock_litellm.completion.return_value = mock_response

        coach.chat(
            question="How to improve?",
            retrieved_passages=[],
            exchange_history=mock_exchange_history,
            score={"fencer": 1, "opponent": 1},
        )

        assert len(coach.chat_history) == 2
        assert coach.chat_history[0]["role"] == "user"
        assert coach.chat_history[1]["role"] == "assistant"

    @patch("src.agents.coach.litellm")
    def test_chat_fallback_on_error(self, mock_litellm, coach, mock_exchange_history):
        """Verify graceful fallback when LLM is unavailable."""
        mock_litellm.completion.side_effect = Exception("Connection refused")

        result = coach.chat(
            question="Help me",
            retrieved_passages=[],
            exchange_history=mock_exchange_history,
            score={"fencer": 0, "opponent": 0},
        )

        assert "trouble connecting" in result["answer"]

    def test_reset_clears_chat_history(self, coach):
        coach.chat_history = [{"role": "user", "content": "test"}]
        coach.feedback_history = [{"summary": "test"}]
        coach.reset()
        assert coach.chat_history == []
        assert coach.feedback_history == []
