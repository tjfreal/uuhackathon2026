"""
06_build_feature_manifest.py — Build Feature Manifest v1

Derives a corpus-level feature manifest from saved transcription outputs plus the
local Chroma index. The goal is not perfect classification; it is a durable and
inspectable summary of what the current pipeline believes exists on each page.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

import chromadb
from dotenv import load_dotenv

load_dotenv()

STAGED_DATA_DIR = Path(os.getenv("STAGED_DATA_DIR", "data/staged"))
CHROMA_DB_PATH = Path(os.getenv("CHROMA_DB_PATH", "data/chroma"))
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "topolski_explorer")
FEATURE_MANIFEST_PATH = Path(os.getenv("FEATURE_MANIFEST_PATH", "data/feature_manifest.json"))


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def normalize_text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def normalize_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def normalize_entities(value: Any) -> dict[str, list[str]]:
    if not isinstance(value, dict):
        return {}
    normalized: dict[str, list[str]] = {}
    for key, raw in value.items():
        values = normalize_list(raw)
        if values:
            normalized[key] = values
    return normalized


def count_words(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def infer_page_flags(page: dict[str, Any]) -> dict[str, Any]:
    typeset_text = normalize_text(page.get("typeset_text"))
    handwritten_text = normalize_text(page.get("handwritten_text"))
    sketch_descriptions = normalize_list(page.get("sketch_descriptions"))
    entities = normalize_entities(page.get("entities"))
    page_summary = normalize_text(page.get("page_summary"))

    combined_text = "\n".join(part for part in (typeset_text, handwritten_text, page_summary) if part)
    lower_typeset = typeset_text.lower()
    lower_summary = page_summary.lower()
    lower_sketch = " ".join(sketch_descriptions).lower()

    typeset_words = count_words(typeset_text)
    handwritten_words = count_words(handwritten_text)
    summary_words = count_words(page_summary)
    sketch_count = len(sketch_descriptions)
    entity_count = sum(len(values) for values in entities.values())
    newline_count = typeset_text.count("\n")
    numbered_refs = len(re.findall(r"\(\d+\)|\bno\.\s*\d+\b|\bpages?\b", lower_typeset))

    is_index_like = any(
        token in lower_typeset or token in lower_summary
        for token in ("index", "list of drawings", "numbers refer to drawings", "list of")
    )
    is_list_like = newline_count >= 6 or numbered_refs >= 4
    is_text_heavy = typeset_words >= 180 or (typeset_words >= 100 and sketch_count <= 1)
    is_image_heavy = sketch_count >= 4 and typeset_words <= 80

    return {
        "has_typeset_text": bool(typeset_text),
        "has_handwritten_text": bool(handwritten_text),
        "has_sketches": bool(sketch_descriptions),
        "has_entities": bool(entities),
        "has_summary": bool(page_summary),
        "is_index_like": is_index_like,
        "is_list_like": is_list_like,
        "is_text_heavy": is_text_heavy,
        "is_image_heavy": is_image_heavy,
        "has_portrait": any(token in lower_sketch for token in ("portrait", "head in profile", "profile view")),
        "has_crowd_scene": any(token in lower_sketch for token in ("crowd", "group of figures", "gathered", "mass scene")),
        "has_architecture": any(token in combined_text.lower() + " " + lower_sketch for token in ("cathedral", "abbey", "bridge", "architecture", "building", "church")),
        "word_counts": {
            "typeset": typeset_words,
            "handwritten": handwritten_words,
            "summary": summary_words,
        },
        "sketch_count": sketch_count,
        "entity_count": entity_count,
    }


def load_indexed_chunk_types() -> dict[tuple[str, int], list[str]]:
    if not CHROMA_DB_PATH.exists():
        return {}

    chroma = chromadb.PersistentClient(path=str(CHROMA_DB_PATH))
    collection = chroma.get_or_create_collection(
        name=CHROMA_COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    if collection.count() == 0:
        return {}

    snapshot = collection.get(include=["metadatas"])
    indexed: dict[tuple[str, int], set[str]] = {}
    for metadata in snapshot.get("metadatas", []):
        if not metadata:
            continue
        item_id = metadata.get("item_id")
        page_number = metadata.get("page_number")
        chunk_type = metadata.get("chunk_type")
        if item_id is None or page_number is None or not chunk_type:
            continue
        key = (str(item_id), int(page_number))
        indexed.setdefault(key, set()).add(str(chunk_type))

    return {key: sorted(value) for key, value in indexed.items()}


def build_manifest() -> dict[str, Any]:
    indexed_chunk_types = load_indexed_chunk_types()

    item_dirs = sorted(path for path in STAGED_DATA_DIR.iterdir() if path.is_dir()) if STAGED_DATA_DIR.exists() else []
    items: dict[str, Any] = {}
    corpus_feature_counts: dict[str, int] = {}
    total_pages = 0
    transcribed_pages = 0
    indexed_pages = 0

    for item_dir in item_dirs:
        item_id = item_dir.name
        metadata_path = STAGED_DATA_DIR / f"{item_id}.json"
        transcription_path = item_dir / "transcription.json"
        metadata = load_json(metadata_path) if metadata_path.exists() else {}
        title = normalize_text(metadata.get("metadata", {}).get("Title")) or normalize_text(metadata.get("Title"))

        item_record: dict[str, Any] = {
            "item_id": item_id,
            "title": title,
            "page_count": len(metadata.get("page_images", [])) if isinstance(metadata.get("page_images"), list) else 0,
            "transcribed_page_count": 0,
            "indexed_page_count": 0,
            "feature_counts": {},
            "indexed_chunk_types_present": [],
            "weakly_characterized_pages": [],
            "pages": [],
        }
        total_pages += item_record["page_count"]

        if transcription_path.exists():
            transcription = load_json(transcription_path)
            for page in transcription.get("pages", []):
                page_number = int(page.get("page_number", 0))
                flags = infer_page_flags(page)
                chunk_types = indexed_chunk_types.get((item_id, page_number), [])
                page_entry = {
                    "page_number": page_number,
                    "indexed_chunk_types": chunk_types,
                    **flags,
                }
                item_record["pages"].append(page_entry)
                item_record["transcribed_page_count"] += 1
                transcribed_pages += 1
                if chunk_types:
                    item_record["indexed_page_count"] += 1
                    indexed_pages += 1

                for key, value in flags.items():
                    if isinstance(value, bool) and value:
                        item_record["feature_counts"][key] = item_record["feature_counts"].get(key, 0) + 1
                        corpus_feature_counts[key] = corpus_feature_counts.get(key, 0) + 1

                if len(chunk_types) <= 1 or (not flags["has_typeset_text"] and not flags["has_sketches"]):
                    item_record["weakly_characterized_pages"].append(page_number)

        present_chunk_types = sorted(
            {
                chunk_type
                for page in item_record["pages"]
                for chunk_type in page.get("indexed_chunk_types", [])
            }
        )
        item_record["indexed_chunk_types_present"] = present_chunk_types
        items[item_id] = item_record

    return {
        "schema_version": "2026-04-19-feature-manifest-v1",
        "manifest_path": FEATURE_MANIFEST_PATH.as_posix(),
        "corpus_summary": {
            "staged_item_count": len(item_dirs),
            "staged_page_count": total_pages,
            "transcribed_item_count": sum(1 for item in items.values() if item["transcribed_page_count"] > 0),
            "transcribed_page_count": transcribed_pages,
            "indexed_item_count": sum(1 for item in items.values() if item["indexed_page_count"] > 0),
            "indexed_page_count": indexed_pages,
            "feature_counts": dict(sorted(corpus_feature_counts.items())),
        },
        "items": items,
    }


def main() -> None:
    manifest = build_manifest()
    write_json(FEATURE_MANIFEST_PATH, manifest)
    print(f"Wrote feature manifest to {FEATURE_MANIFEST_PATH}")
    print(
        f"Items: {manifest['corpus_summary']['staged_item_count']} "
        f"Transcribed pages: {manifest['corpus_summary']['transcribed_page_count']} "
        f"Indexed pages: {manifest['corpus_summary']['indexed_page_count']}"
    )


if __name__ == "__main__":
    main()
