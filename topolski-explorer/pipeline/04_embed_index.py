"""
04_embed_index.py — Embed and Index

Reads transcription.json for each item, creates multiple retrieval documents per page,
embeds them with OpenAI text-embedding-3-small, and loads them into a persistent
local ChromaDB collection.

Chunk types per page:
  text     — typeset_text + handwritten_text
  sketch   — sketch descriptions
  entities — structured entity string
  summary  — page summary
  blended  — all available signals combined for broader semantic recall

Idempotent and resume-safe:
  - tracks a per-item content fingerprint in data/chroma/processed.json
  - skips items whose transcription payload has not changed
  - tolerates partial corpora while 03_transcribe.py is still running
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from openai import OpenAI
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

STAGED_DATA_DIR = Path(os.getenv("STAGED_DATA_DIR", "data/staged"))
CHROMA_DB_PATH = Path(os.getenv("CHROMA_DB_PATH", "data/chroma"))
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "topolski_explorer")
EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
EMBED_BATCH_SIZE = int(os.getenv("EMBED_BATCH_SIZE", "96"))
MAX_ITEMS = int(os.getenv("MAX_ITEMS", "0") or "0")
ITEM_ID_MIN = os.getenv("ITEM_ID_MIN", "").strip()
ITEM_ID_MAX = os.getenv("ITEM_ID_MAX", "").strip()
PROCESSED_REGISTRY = CHROMA_DB_PATH / "processed.json"
ITEM_DETAILS_BASE_URL = os.getenv("ITEM_DETAILS_BASE_URL", "")

CHROMA_DB_PATH.mkdir(parents=True, exist_ok=True)
client = OpenAI()
chroma = chromadb.PersistentClient(path=str(CHROMA_DB_PATH))
collection = chroma.get_or_create_collection(
    name=CHROMA_COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"},
)


def load_processed_registry() -> dict[str, str]:
    if PROCESSED_REGISTRY.exists():
        with PROCESSED_REGISTRY.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, list):
            return {item_id: "legacy" for item_id in data}
        if isinstance(data, dict):
            return {str(key): str(value) for key, value in data.items()}
    return {}


def save_processed_registry(processed: dict[str, str]) -> None:
    with PROCESSED_REGISTRY.open("w", encoding="utf-8") as handle:
        json.dump(dict(sorted(processed.items())), handle, indent=2)


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def normalize_string(value: object) -> str:
    if isinstance(value, str):
        return value.strip()
    return ""


def normalize_list(values: object) -> list[str]:
    if not isinstance(values, list):
        return []
    return [str(value).strip() for value in values if str(value).strip()]


def normalize_entities(entities: object) -> dict[str, list[str]]:
    if not isinstance(entities, dict):
        return {}
    return {
        key: normalize_list(value)
        for key, value in entities.items()
        if normalize_list(value)
    }


def fingerprint_transcription(transcription: dict) -> str:
    canonical = json.dumps(transcription, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_collection_url(item_id: str, item_metadata: dict) -> str:
    for key in ("Item URL", "item_url", "url"):
        candidate = normalize_string(item_metadata.get("metadata", {}).get(key))
        if candidate:
            return candidate
        candidate = normalize_string(item_metadata.get(key))
        if candidate:
            return candidate
    return f"{ITEM_DETAILS_BASE_URL}{item_id}" if ITEM_DETAILS_BASE_URL else ""


def resolve_image_path(path_value: str) -> str:
    if not path_value:
        return ""
    candidate = Path(path_value)
    if candidate.is_absolute():
        return str(candidate)
    return str((STAGED_DATA_DIR / candidate).resolve())


def format_entities(entities: dict[str, list[str]]) -> str:
    ordered_labels = {
        "people": "People",
        "places": "Places",
        "events": "Events",
        "dates": "Dates",
    }
    parts = []
    for key, label in ordered_labels.items():
        values = entities.get(key, [])
        if values:
            parts.append(f"{label}: {', '.join(values)}")
    for key, values in entities.items():
        if key not in ordered_labels and values:
            parts.append(f"{key.title()}: {', '.join(values)}")
    return ". ".join(parts)


def build_blended_text(
    item_title: str,
    item_date: str,
    page_num: int,
    text_combined: str,
    sketch_text: str,
    entity_text: str,
    summary: str,
) -> str:
    sections = [f"Item: {item_title or 'Untitled'}", f"Page: {page_num}"]
    if item_date:
        sections.append(f"Date: {item_date}")
    if summary:
        sections.append(f"Summary: {summary}")
    if text_combined:
        sections.append(f"Text: {text_combined}")
    if sketch_text:
        sections.append(f"Sketches: {sketch_text}")
    if entity_text:
        sections.append(f"Entities: {entity_text}")
    return "\n".join(sections)


def build_chunks(item_id: str, item_metadata: dict, page: dict) -> list[dict]:
    page_num = int(page.get("page_number", 0))
    item_title = normalize_string(item_metadata.get("metadata", {}).get("Title")) or normalize_string(
        item_metadata.get("Title")
    )
    item_date = normalize_string(item_metadata.get("metadata", {}).get("Date")) or normalize_string(
        item_metadata.get("Date")
    )
    image_path = resolve_image_path(normalize_string(page.get("image_path")))
    typeset = normalize_string(page.get("typeset_text"))
    handwritten = normalize_string(page.get("handwritten_text"))
    text_combined = "\n".join(part for part in (typeset, handwritten) if part)
    sketches = normalize_list(page.get("sketch_descriptions"))
    sketch_text = "\n".join(sketches)
    entities = normalize_entities(page.get("entities"))
    entity_text = format_entities(entities)
    summary = normalize_string(page.get("page_summary"))

    base_meta = {
        "item_id": item_id,
        "page_number": page_num,
        "item_title": item_title,
        "item_date": item_date,
        "collection_url": build_collection_url(item_id, item_metadata),
        "image_path": image_path,
        "has_text": bool(text_combined),
        "has_sketch": bool(sketch_text),
        "has_entities": bool(entity_text),
        "has_summary": bool(summary),
    }

    chunks: list[dict] = []

    def append_chunk(chunk_type: str, text: str, preview: str | None = None) -> None:
        cleaned = normalize_string(text)
        if not cleaned:
            return
        chunks.append(
            {
                "id": f"{item_id}_p{page_num}_{chunk_type}",
                "text": cleaned,
                "metadata": {
                    **base_meta,
                    "chunk_type": chunk_type,
                    "source_text": (preview or cleaned)[:1200],
                },
            }
        )

    append_chunk("text", text_combined)
    append_chunk("sketch", sketch_text)
    append_chunk("entities", entity_text)
    append_chunk("summary", summary)
    append_chunk(
        "blended",
        build_blended_text(item_title, item_date, page_num, text_combined, sketch_text, entity_text, summary),
        preview=summary or text_combined or sketch_text or entity_text,
    )

    return chunks


@retry(
    retry=retry_if_exception_type(Exception),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=4, max=30),
    reraise=True,
)
def embed_batch(texts: list[str]) -> list[list[float]]:
    response = client.embeddings.create(model=EMBED_MODEL, input=texts)
    return [item.embedding for item in sorted(response.data, key=lambda item: item.index)]


def delete_item_chunks(item_id: str) -> None:
    try:
        collection.delete(where={"item_id": item_id})
    except Exception as exc:
        log.warning("%s: failed to clear existing chunks before reindex: %s", item_id, exc)


def ingest_chunks(chunks: list[dict]) -> int:
    if not chunks:
        return 0

    indexed = 0
    for start in range(0, len(chunks), EMBED_BATCH_SIZE):
        batch = chunks[start:start + EMBED_BATCH_SIZE]
        texts = [chunk["text"] for chunk in batch]
        embeddings = embed_batch(texts)
        collection.upsert(
            ids=[chunk["id"] for chunk in batch],
            embeddings=embeddings,
            documents=texts,
            metadatas=[chunk["metadata"] for chunk in batch],
        )
        indexed += len(batch)
        log.info("Indexed %s chunks.", len(batch))
    return indexed


def main() -> None:
    processed = load_processed_registry()
    if not STAGED_DATA_DIR.exists():
        raise FileNotFoundError(f"STAGED_DATA_DIR does not exist: {STAGED_DATA_DIR}")

    item_dirs = sorted(path for path in STAGED_DATA_DIR.iterdir() if path.is_dir())
    if ITEM_ID_MIN:
        item_dirs = [path for path in item_dirs if path.name >= ITEM_ID_MIN]
    if ITEM_ID_MAX:
        item_dirs = [path for path in item_dirs if path.name <= ITEM_ID_MAX]
    if MAX_ITEMS > 0:
        item_dirs = item_dirs[:MAX_ITEMS]
    log.info("%s item directories found, %s already fingerprinted.", len(item_dirs), len(processed))

    for item_dir in item_dirs:
        item_id = item_dir.name
        transcription_path = item_dir / "transcription.json"
        metadata_path = STAGED_DATA_DIR / f"{item_id}.json"

        if not transcription_path.exists():
            log.debug("%s: no transcription yet, skipping.", item_id)
            continue

        transcription = load_json(transcription_path)
        pages = transcription.get("pages", [])
        if not pages:
            log.info("%s: transcription exists but has no pages yet, skipping.", item_id)
            continue

        fingerprint = fingerprint_transcription(transcription)
        if processed.get(item_id) == fingerprint:
            log.debug("%s: unchanged since last index.", item_id)
            continue

        item_metadata = load_json(metadata_path) if metadata_path.exists() else {}

        all_chunks: list[dict] = []
        for page in pages:
            try:
                all_chunks.extend(build_chunks(item_id, item_metadata, page))
            except Exception as exc:
                log.warning("%s p%s: failed to build chunks: %s", item_id, page.get("page_number"), exc)

        if not all_chunks:
            log.info("%s: no usable chunks produced, skipping.", item_id)
            continue

        delete_item_chunks(item_id)
        indexed_count = ingest_chunks(all_chunks)
        processed[item_id] = fingerprint
        save_processed_registry(processed)
        log.info("%s: %s chunks indexed.", item_id, indexed_count)

    log.info("Indexing complete. Collection has %s total chunks.", collection.count())


if __name__ == "__main__":
    main()
