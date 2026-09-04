import os
import sys
import time
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv

# Setup environment
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("[ERROR] GEMINI_API_KEY is not set in .env!")
    sys.exit(1)

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.0-flash")

books_dir = PROJECT_ROOT / "data" / "books"
pdf_files = sorted(books_dir.glob("*.pdf"))

if not pdf_files:
    print("[ERROR] No PDF files found in data/books/!")
    sys.exit(1)

print("=" * 60)
print("=== Multimodal Gemini PDF OCR Transcribing Engine starting ===")
print("=" * 60)

for pdf_path in pdf_files:
    txt_path = pdf_path.with_suffix(".txt")
    if txt_path.exists():
        print(f"[INFO] Skipping already transcribed book: {txt_path.name}")
        continue

    print(f"\n[1/4] Uploading {pdf_path.name} to Google GenAI API...")
    try:
        uploaded_file = genai.upload_file(path=str(pdf_path))
        print(f"Uploaded successfully. Remote Name: {uploaded_file.name}")

        # Wait for file processing in Gemini Cloud
        while uploaded_file.state.name == "PROCESSING":
            print(".", end="", flush=True)
            time.sleep(2)
            uploaded_file = genai.get_file(uploaded_file.name)

        if uploaded_file.state.name == "FAILED":
            raise ValueError(f"File processing failed: {uploaded_file.error.message}")

        print(
            f"\n[2/4] File is ready for processing. State: {uploaded_file.state.name}"
        )

        # Get total page count
        import fitz

        doc = fitz.open(str(pdf_path))
        page_count = doc.page_count
        doc.close()
        print(f"Total Pages to transcribe: {page_count}")

        # Transcribe in page ranges of 10 pages to prevent 8192-token output truncation
        transcriptions = []
        page_ranges = []

        step = 10
        for i in range(1, page_count + 1, step):
            end = min(i + step - 1, page_count)
            page_ranges.append((i, end))

        print(
            f"[3/4] Transcribing book in {len(page_ranges)} chunks to guarantee full coverage..."
        )

        for idx, (start, end) in enumerate(page_ranges, 1):
            print(
                f" -> Processing pages {start} to {end} (Chunk {idx}/{len(page_ranges)})..."
            )
            prompt = (
                f"You are a professional book transcriber. Transcribe pages {start} through {end} "
                "of this scanned fencing guidebook in full detail. Do not summarize or skip anything. "
                "Output the exact textual contents of the pages in clean markdown. Format each page "
                f"with a clear marker like '[Page N]' before its text starts."
            )

            # Robust retry loop with rate limit backoff for Free Tier
            max_retries = 6
            for retry in range(max_retries):
                try:
                    response = model.generate_content([uploaded_file, prompt])
                    text = response.text.strip()
                    if text:
                        transcriptions.append(text)
                        break
                    print("Received empty text, retrying...")
                except (ValueError, RuntimeError, OSError) as ex:
                    print(
                        f"Error during chunk generation (retry {retry + 1}/{max_retries}): {ex}"
                    )
                    # If it's a rate limit error (429), wait longer
                    if (
                        "429" in str(ex)
                        or "Quota exceeded" in str(ex)
                        or "ResourceExhausted" in str(ex)
                    ):
                        print("Rate limit hit! Sleeping 60 seconds before retrying...")
                        time.sleep(60)
                    else:
                        time.sleep(5)
            else:
                raise RuntimeError(
                    f"Failed to transcribe page range {start}-{end} after multiple retries."
                )

            # Generous sleep to stay well within Google AI Studio's free tier limits (15 RPM / 10 RPM)
            time.sleep(8)

        # Save transcription
        full_transcription = "\n\n".join(transcriptions)
        print(f"\n[4/4] Writing transcription to: {txt_path.name}...")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(full_transcription)
        print(
            f"SUCCESS! {txt_path.name} created successfully ({len(full_transcription)} characters)."
        )

    except (ValueError, RuntimeError, OSError) as e:
        print(f"\n[ERROR] Failed to transcribe {pdf_path.name}: {e}")
    finally:
        try:
            genai.delete_file(uploaded_file.name)
            print(f"Cleaned up remote file {uploaded_file.name} from Gemini API.")
        except (ValueError, RuntimeError, OSError):
            pass  # Best-effort cleanup; ignore failures

print("\n" + "=" * 60)
print("=== Transcribe engine tasks completed successfully! ===")
print("=" * 60)
