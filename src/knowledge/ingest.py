"""
PDF ingestion pipeline for the fencing knowledge base.

Extracts text from PDF files, chunks it, embeds it, and stores
in a persistent ChromaDB collection for RAG retrieval.
"""

from pathlib import Path

import chromadb
import fitz  # PyMuPDF
from chromadb.utils import embedding_functions

from src.utils.config import (
    BOOKS_DIR,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    EMBEDDING_MODEL,
    VECTORSTORE_DIR,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)

COLLECTION_NAME = "fencing_books"


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract all text from a PDF file using PyMuPDF."""
    logger.info(f"Extracting text from: {pdf_path.name}")
    doc = fitz.open(str(pdf_path))
    pages = []
    for page_num, page in enumerate(doc, start=1):
        text = page.get_text("text")
        if text.strip():
            pages.append(f"[Page {page_num}]\n{text}")
    doc.close()

    full_text = "\n\n".join(pages)
    logger.info(f"Extracted {len(pages)} pages from {pdf_path.name}")
    return full_text


def chunk_text(
    text: str,
    source_name: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[dict]:
    """
    Split text into overlapping chunks with metadata.

    Each chunk is roughly `chunk_size` characters with `overlap`
    characters shared between consecutive chunks.
    """
    chunks = []
    words = text.split()
    if not words:
        return chunks

    # Approximate characters-per-word to convert token-ish sizes
    # We use word-level splitting for cleaner boundaries
    start = 0
    chunk_index = 0

    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        chunk_text = " ".join(chunk_words)

        # Try to detect the nearest page marker for metadata
        page_num = _extract_page_number(chunk_text)

        chunks.append({
            "text": chunk_text,
            "metadata": {
                "source": source_name,
                "chunk_index": chunk_index,
                "page": page_num,
            },
        })

        chunk_index += 1
        start = end - overlap  # slide window with overlap

    logger.info(f"Created {len(chunks)} chunks from {source_name}")
    return chunks


def _extract_page_number(text: str) -> int:
    """Extract the last [Page N] marker found in a chunk."""
    import re

    matches = re.findall(r"\[Page (\d+)\]", text)
    if matches:
        return int(matches[-1])
    return 0


def ingest_books(
    books_dir: Path = BOOKS_DIR,
    vectorstore_dir: Path = VECTORSTORE_DIR,
) -> chromadb.Collection:
    """
    Ingest all books (PDF or pre-transcribed TXT) into a persistent ChromaDB collection.

    Skips files that have already been ingested (idempotent).
    Returns the ChromaDB collection.
    """
    books_dir = Path(books_dir)
    vectorstore_dir = Path(vectorstore_dir)
    vectorstore_dir.mkdir(parents=True, exist_ok=True)

    # Gather PDF and TXT files
    pdf_files = {f.stem: f for f in books_dir.glob("*.pdf")}
    txt_files = {f.stem: f for f in books_dir.glob("*.txt")}

    # Prefer TXT files over PDFs if both exist
    files_to_ingest = []
    for stem in sorted(set(pdf_files.keys()) | set(txt_files.keys())):
        if stem in txt_files:
            files_to_ingest.append(txt_files[stem])
        else:
            files_to_ingest.append(pdf_files[stem])

    # Initialize ChromaDB with persistent storage
    client = chromadb.PersistentClient(path=str(vectorstore_dir))

    # Use sentence-transformers for embedding
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=ef,
    )

    if not files_to_ingest:
        logger.warning(f"No PDF or TXT files found in {books_dir}. Initializing knowledge base with fallback rules.")
        _ingest_rules_fallback(collection)
        return collection

    logger.info(f"Found {len(files_to_ingest)} books/transcriptions to ingest")

    # Check which sources are already ingested
    existing_sources = set()
    if collection.count() > 0:
        existing_meta = collection.get(include=["metadatas"])
        existing_sources = {
            m.get("source", "") for m in existing_meta["metadatas"]
        }
        logger.info(f"Already ingested sources: {existing_sources}")

    for file_path in files_to_ingest:
        source_name = file_path.name
        
        # If ingesting a TXT file, check if either the TXT or original PDF source is already present
        pdf_source = file_path.with_suffix(".pdf").name
        if source_name in existing_sources or pdf_source in existing_sources:
            logger.info(f"Skipping already-ingested: {source_name}")
            continue

        logger.info(f"Ingesting: {source_name}")
        
        # Load text
        if file_path.suffix == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        else:
            text = extract_text_from_pdf(file_path)
            
        chunks = chunk_text(text, source_name)

        if not chunks:
            logger.warning(f"No text extracted from {source_name}")
            continue

        # Batch add to ChromaDB
        ids = [f"{source_name}_chunk_{c['metadata']['chunk_index']}" for c in chunks]
        documents = [c["text"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]

        # ChromaDB has a batch limit; add in batches of 500
        batch_size = 500
        for i in range(0, len(ids), batch_size):
            collection.add(
                ids=ids[i : i + batch_size],
                documents=documents[i : i + batch_size],
                metadatas=metadatas[i : i + batch_size],
            )

        logger.info(f"Ingested {len(chunks)} chunks from {source_name}")

    if collection.count() == 0:
        logger.warning("No PDF chunks were ingested (PDFs may be scanned or empty). Falling back to rules ingestion.")
        _ingest_rules_fallback(collection)

    logger.info(f"Total documents in collection: {collection.count()}")
    return collection


def _ingest_rules_fallback(collection) -> int:
    """Ingest rules from fencing_rules.json as a fallback when PDFs are scanned or empty."""
    from src.utils.config import get_rules
    try:
        rules = get_rules()
        documents = []
        metadatas = []
        ids = []

        # 1. Target areas
        target_text = (
            f"Foil fencing valid target areas include: {', '.join(rules['valid_target_areas'])}. "
            f"Invalid target areas include: {', '.join(rules['invalid_target_areas'])}."
        )
        documents.append(target_text)
        metadatas.append({"source": "fencing_rules.json", "chunk_index": 0, "page": 1})
        ids.append("rules_fallback_targets")

        # 2. Right of way rules
        row = rules.get("right_of_way_rules", {})
        row_text = (
            f"Right of way (priority) rules in foil fencing: "
            f"Priority attacks include: {', '.join(row.get('priority_attacks', []))}. "
            f"Secondary actions include: {', '.join(row.get('secondary_actions', []))}. "
            f"Simultaneous hit condition: {row.get('simultaneous_hit', {}).get('condition', '')}."
        )
        documents.append(row_text)
        metadatas.append({"source": "fencing_rules.json", "chunk_index": 1, "page": 1})
        ids.append("rules_fallback_right_of_way")

        # 3. Actions detail
        chunk_idx = 2
        for category, cat_data in rules.get("actions", {}).items():
            for action_key, action_data in cat_data.items():
                name = action_data.get("name", action_key)
                desc = action_data.get("description", "")
                priority = action_data.get("priority", "N/A")
                note = action_data.get("note", "")
                action_text = (
                    f"Fencing action: {name} (Category: {category}). "
                    f"Description: {desc}. Priority: {priority}."
                )
                if note:
                    action_text += f" Note: {note}"
                documents.append(action_text)
                metadatas.append({"source": "fencing_rules.json", "chunk_index": chunk_idx, "page": 1})
                ids.append(f"rules_fallback_action_{action_key}")
                chunk_idx += 1

        # Add to collection
        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        logger.info(f"Ingested {len(ids)} fallback rule chunks into ChromaDB.")
        return len(ids)
    except (chromadb.errors.ChromaError, OSError, ValueError) as e:
        logger.error(f"Failed to ingest fallback rules: {e}")
        return 0


def get_ingestion_status(
    books_dir: Path = BOOKS_DIR,
    vectorstore_dir: Path = VECTORSTORE_DIR,
) -> dict:
    """Check the current ingestion status."""
    books_dir = Path(books_dir)
    vectorstore_dir = Path(vectorstore_dir)

    pdf_files = {f.stem: f.name for f in books_dir.glob("*.pdf")}
    txt_files = {f.stem: f.name for f in books_dir.glob("*.txt")}
    
    # Combined set of stems
    all_stems = sorted(set(pdf_files.keys()) | set(txt_files.keys()))
    pdf_names = [pdf_files.get(stem, f"{stem}.pdf") for stem in all_stems]

    ingested_sources = set()
    total_chunks = 0

    if vectorstore_dir.exists():
        try:
            client = chromadb.PersistentClient(path=str(vectorstore_dir))
            ef = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=EMBEDDING_MODEL
            )
            collection = client.get_or_create_collection(
                name=COLLECTION_NAME,
                embedding_function=ef,
            )
            total_chunks = collection.count()
            if total_chunks > 0:
                meta = collection.get(include=["metadatas"])
                ingested_sources = {
                    m.get("source", "") for m in meta["metadatas"]
                }
        except (chromadb.errors.ChromaError, OSError, ValueError) as e:
            logger.error(f"Error checking ingestion status: {e}")

    # A source is pending if neither its PDF nor its TXT file version is ingested
    pending = []
    for stem in all_stems:
        pdf_name = pdf_files.get(stem, f"{stem}.pdf")
        txt_name = txt_files.get(stem, f"{stem}.txt")
        if pdf_name not in ingested_sources and txt_name not in ingested_sources:
            pending.append(pdf_name)

    return {
        "pdf_files": pdf_names,
        "ingested_sources": list(ingested_sources),
        "pending": pending,
        "total_chunks": total_chunks,
    }


# CLI entry point: python -m src.knowledge.ingest
if __name__ == "__main__":
    import sys

    print("=" * 50)
    print("Fencing Book Ingestion Pipeline")
    print("=" * 50)

    status = get_ingestion_status()
    print(f"\nPDF files found: {status['pdf_files']}")
    print(f"Already ingested: {status['ingested_sources']}")
    print(f"Pending: {status['pending']}")

    if not status["pdf_files"]:
        print(f"\nNo PDF files found in {BOOKS_DIR}")
        print("Please place your fencing PDF books there and re-run.")
        sys.exit(1)

    if not status["pending"]:
        print(f"\nAll books already ingested ({status['total_chunks']} chunks).")
        sys.exit(0)

    print("\nStarting ingestion...")
    collection = ingest_books()
    if collection:
        print(f"\nDone! Total chunks in knowledge base: {collection.count()}")
    else:
        print("\nIngestion failed. Check logs for details.")
