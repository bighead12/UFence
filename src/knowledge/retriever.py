"""
Vector retriever for the fencing knowledge base.

Queries the ChromaDB collection to find the most relevant
book passages for a given question.
"""

from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

from src.utils.config import (
    EMBEDDING_MODEL,
    RAG_TOP_K,
    VECTORSTORE_DIR,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)

COLLECTION_NAME = "fencing_books"


class BookRetriever:
    """Retrieves relevant passages from the fencing book knowledge base."""

    def __init__(
        self,
        vectorstore_dir: Path = VECTORSTORE_DIR,
        embedding_model: str = EMBEDDING_MODEL,
    ):
        self._vectorstore_dir = Path(vectorstore_dir)
        self._embedding_model = embedding_model
        self._collection: chromadb.Collection | None = None
        self._ready = False

    def _ensure_loaded(self):
        """Lazy-load the ChromaDB collection and embedding model."""
        if self._ready:
            return

        if not self._vectorstore_dir.exists():
            logger.warning(f"Vectorstore not found at {self._vectorstore_dir}")
            return

        try:
            client = chromadb.PersistentClient(path=str(self._vectorstore_dir))
            ef = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=self._embedding_model
            )
            self._collection = client.get_or_create_collection(
                name=COLLECTION_NAME,
                embedding_function=ef,
            )

            count = self._collection.count()
            if count == 0:
                logger.warning("Vectorstore collection is empty")
                return

            self._ready = True
            logger.info(
                f"BookRetriever ready with {count} documents"
            )
        except (chromadb.errors.ChromaError, OSError, ValueError) as e:
            logger.error(f"Failed to load vectorstore: {e}")

    @property
    def is_ready(self) -> bool:
        """Check if the retriever is ready to serve queries."""
        self._ensure_loaded()
        return self._ready

    @property
    def document_count(self) -> int:
        """Number of documents in the collection."""
        self._ensure_loaded()
        if self._collection:
            return self._collection.count()
        return 0

    def retrieve(
        self, query: str, top_k: int = RAG_TOP_K
    ) -> list[dict]:
        """
        Retrieve the top-k most relevant passages for a query.

        Returns a list of dicts with keys:
        - text: The passage text
        - source: The source PDF filename
        - page: The approximate page number
        - chunk_index: The chunk index within the source
        - distance: The similarity distance (lower = more relevant)
        """
        self._ensure_loaded()

        if not self._ready or self._collection is None:
            logger.warning("Retriever not ready, returning empty results")
            return []

        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=min(top_k, self._collection.count()),
                include=["documents", "metadatas", "distances"],
            )

            passages = []
            if results and results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    meta = results["metadatas"][0][i] if results["metadatas"] else {}
                    distance = (
                        results["distances"][0][i] if results["distances"] else 0.0
                    )

                    passages.append({
                        "text": doc,
                        "source": meta.get("source", "Unknown"),
                        "page": meta.get("page", 0),
                        "chunk_index": meta.get("chunk_index", 0),
                        "distance": distance,
                    })

            logger.info(
                f"Retrieved {len(passages)} passages for query: "
                f"{query[:50]}..."
            )
            return passages

        except (chromadb.errors.ChromaError, ValueError) as e:
            logger.error(f"Retrieval error: {e}")
            return []

    def format_passages_for_prompt(
        self, passages: list[dict]
    ) -> str:
        """Format retrieved passages into a string for the LLM prompt."""
        if not passages:
            return "No reference material available."

        formatted = []
        for i, p in enumerate(passages, start=1):
            source_info = f'{p["source"]}'
            if p.get("page"):
                source_info += f", p. {p['page']}"

            formatted.append(
                f"--- Reference {i} (from: {source_info}) ---\n"
                f"{p['text'][:1500]}\n"  # Truncate very long passages
            )

        return "\n".join(formatted)
