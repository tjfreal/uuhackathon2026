"""
03_transcribe.py — Vision Transcription Per Page

Reads normalized item metadata from data/staged/{item_id}.json, uses the declared
page_images entries as input, and writes durable per-item transcription outputs to
data/staged/{item_id}/transcription.json.

The script is resume-safe at the page level:
  - successful pages are saved immediately
  - reruns skip pages that already have a valid transcription entry
  - failed or missing pages are retried on later runs
"""

from __future__ import annotations

import base64
import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

STAGED_DATA_DIR = Path(os.getenv("STAGED_DATA_DIR", "data/staged"))
VISION_MODEL = os.getenv("OPENAI_VISION_MODEL", "gpt-4.1")
OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_VISION_MAX_TOKENS", "2500"))
API_DELAY_SECONDS = float(os.getenv("OPENAI_API_DELAY_SECONDS", "0.5"))
MAX_ITEMS = int(os.getenv("MAX_ITEMS", "0") or "0")
ITEM_ID_MIN = os.getenv("ITEM_ID_MIN", "").strip()
ITEM_ID_MAX = os.getenv("ITEM_ID_MAX", "").strip()
SCHEMA_VERSION = "2026-04-19"

client = OpenAI()

SYSTEM_PROMPT = """You are analyzing a page from Topolski's Chronicle, a biweekly illustrated
broadsheet published by artist Felix Topolski between the 1950s and 1980s.

Each page may contain:
- typeset editorial text
- Topolski's handwritten cursive notes or captions
- expressive sketches, portraits, crowds, architecture, and scene fragments

Your job is to extract durable, retrieval-friendly structured information from the page.
Be careful, concrete, and conservative where uncertain."""

USER_PROMPT = """Return a single JSON object with this exact structure:

{
  "typeset_text": "Full transcription of printed/typeset text. Empty string if none.",
  "handwritten_text": "Best-effort transcription of handwritten text. Mark uncertain words with [?]. Empty string if none.",
  "sketch_descriptions": [
    "One concise but specific description per distinct drawing, figure group, or visual scene."
  ],
  "entities": {
    "people": ["Named or strongly identifiable people shown or mentioned"],
    "places": ["Places, buildings, regions, or geographic references"],
    "events": ["Named events, conflicts, public occasions, or political moments"],
    "dates": ["Dates, years, eras, or time expressions"]
  },
  "page_summary": "A concise 1-2 sentence summary of what this page captures."
}

Rules:
- Return only valid JSON.
- Do not include markdown fences.
- If a field is absent, use an empty string or empty list.
- Keep sketch descriptions semantically rich enough for later retrieval.
- Include entities only when they are explicit or strongly supported by the page."""


def encode_image(image_path: Path) -> str:
    with image_path.open("rb") as handle:
        return base64.b64encode(handle.read()).decode("utf-8")


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return "\n".join(str(part).strip() for part in value if str(part).strip()).strip()
    return str(value).strip()


def normalize_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        cleaned = value.strip()
        return [cleaned] if cleaned else []
    if isinstance(value, list):
        normalized = []
        for item in value:
            cleaned = normalize_text(item)
            if cleaned:
                normalized.append(cleaned)
        return normalized
    cleaned = normalize_text(value)
    return [cleaned] if cleaned else []


def normalize_entities(value: Any) -> dict[str, list[str]]:
    entity_keys = ("people", "places", "events", "dates")
    raw = value if isinstance(value, dict) else {}
    normalized: dict[str, list[str]] = {}
    for key in entity_keys:
        normalized[key] = normalize_string_list(raw.get(key))
    return normalized


def normalize_page_result(raw_result: dict[str, Any]) -> dict[str, Any]:
    return {
        "typeset_text": normalize_text(raw_result.get("typeset_text")),
        "handwritten_text": normalize_text(raw_result.get("handwritten_text")),
        "sketch_descriptions": normalize_string_list(raw_result.get("sketch_descriptions")),
        "entities": normalize_entities(raw_result.get("entities")),
        "page_summary": normalize_text(raw_result.get("page_summary")),
    }


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def valid_completed_page(page: dict[str, Any]) -> bool:
    required_fields = {
        "page_number",
        "image_path",
        "typeset_text",
        "handwritten_text",
        "sketch_descriptions",
        "entities",
        "page_summary",
    }
    if not isinstance(page, dict) or not required_fields.issubset(page.keys()):
        return False
    if not isinstance(page.get("page_number"), int):
        return False
    if not isinstance(page.get("sketch_descriptions"), list):
        return False
    if not isinstance(page.get("entities"), dict):
        return False
    return True


def load_or_init_transcription(item_id: str, item_dir: Path) -> dict[str, Any]:
    path = item_dir / "transcription.json"
    if path.exists():
        existing = load_json(path)
        pages = existing.get("pages", [])
        normalized_pages = []
        for page in pages:
            if not valid_completed_page(page):
                continue
            normalized_page = {
                "page_number": page["page_number"],
                "image_path": normalize_text(page.get("image_path")),
                "typeset_text": normalize_text(page.get("typeset_text")),
                "handwritten_text": normalize_text(page.get("handwritten_text")),
                "sketch_descriptions": normalize_string_list(page.get("sketch_descriptions")),
                "entities": normalize_entities(page.get("entities")),
                "page_summary": normalize_text(page.get("page_summary")),
                "model": normalize_text(page.get("model")) or VISION_MODEL,
                "transcribed_at": normalize_text(page.get("transcribed_at")),
            }
            normalized_pages.append(normalized_page)

        return {
            "schema_version": SCHEMA_VERSION,
            "item_id": item_id,
            "model": normalize_text(existing.get("model")) or VISION_MODEL,
            "processed_at": normalize_text(existing.get("processed_at")) or None,
            "pages": sorted(normalized_pages, key=lambda page: page["page_number"]),
        }

    return {
        "schema_version": SCHEMA_VERSION,
        "item_id": item_id,
        "model": VISION_MODEL,
        "processed_at": None,
        "pages": [],
    }


def upsert_page(transcription: dict[str, Any], page_payload: dict[str, Any]) -> None:
    for index, existing_page in enumerate(transcription["pages"]):
        if existing_page["page_number"] == page_payload["page_number"]:
            transcription["pages"][index] = page_payload
            break
    else:
        transcription["pages"].append(page_payload)

    transcription["pages"].sort(key=lambda page: page["page_number"])
    transcription["model"] = VISION_MODEL
    transcription["processed_at"] = datetime.now(timezone.utc).isoformat()


@retry(
    retry=retry_if_exception_type(Exception),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=4, max=30),
    reraise=True,
)
def transcribe_page(image_path: Path) -> dict[str, Any]:
    b64 = encode_image(image_path)
    response = client.chat.completions.create(
        model=VISION_MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{b64}",
                            "detail": "high",
                        },
                    },
                    {"type": "text", "text": USER_PROMPT},
                ],
            },
        ],
        max_tokens=OPENAI_MAX_TOKENS,
    )

    raw_content = response.choices[0].message.content
    if not raw_content:
        raise ValueError("Model returned empty content")

    parsed = json.loads(raw_content)
    if not isinstance(parsed, dict):
        raise ValueError("Model response was not a JSON object")
    return normalize_page_result(parsed)


def metadata_path_for_item(item_id: str) -> Path:
    return STAGED_DATA_DIR / f"{item_id}.json"


def iter_item_ids() -> list[str]:
    item_ids = sorted(path.stem for path in STAGED_DATA_DIR.glob("*.json"))
    if ITEM_ID_MIN:
        item_ids = [item_id for item_id in item_ids if item_id >= ITEM_ID_MIN]
    if ITEM_ID_MAX:
        item_ids = [item_id for item_id in item_ids if item_id <= ITEM_ID_MAX]
    if MAX_ITEMS > 0:
        item_ids = item_ids[:MAX_ITEMS]
    return item_ids


def main() -> None:
    item_ids = iter_item_ids()
    total_items = len(item_ids)
    log.info("Found %s metadata files to transcribe.", total_items)

    for item_index, item_id in enumerate(item_ids, start=1):
        metadata_path = metadata_path_for_item(item_id)
        item_dir = STAGED_DATA_DIR / item_id
        item_dir.mkdir(parents=True, exist_ok=True)

        try:
            metadata = load_json(metadata_path)
        except Exception as exc:
            log.error("[%s/%s] %s: failed to read metadata: %s", item_index, total_items, item_id, exc)
            continue

        page_images = metadata.get("page_images")
        if not isinstance(page_images, list) or not page_images:
            log.warning("[%s/%s] %s: missing page_images metadata, skipping.", item_index, total_items, item_id)
            continue

        transcription = load_or_init_transcription(item_id, item_dir)
        completed_pages = {
            page["page_number"]
            for page in transcription["pages"]
            if valid_completed_page(page)
        }
        pending_pages = [
            page_info for page_info in page_images
            if isinstance(page_info, dict) and page_info.get("page_number") not in completed_pages
        ]

        if not pending_pages:
            log.info("[%s/%s] %s: all %s pages already transcribed.", item_index, total_items, item_id, len(page_images))
            continue

        log.info(
            "[%s/%s] %s: transcribing %s pending pages (%s already complete).",
            item_index,
            total_items,
            item_id,
            len(pending_pages),
            len(completed_pages),
        )

        transcription_path = item_dir / "transcription.json"
        for page_info in pending_pages:
            page_number = page_info.get("page_number")
            raw_image_path = page_info.get("filepath")
            if not isinstance(page_number, int) or not raw_image_path:
                log.warning("%s: invalid page_images entry %s, skipping.", item_id, page_info)
                continue

            image_path = Path(raw_image_path)
            if not image_path.is_absolute():
                image_path = (Path.cwd() / image_path).resolve()

            if not image_path.exists():
                log.warning("%s p%s: missing image file at %s, skipping.", item_id, page_number, image_path)
                continue

            try:
                result = transcribe_page(image_path)
                page_payload = {
                    "page_number": page_number,
                    "image_path": str(image_path),
                    "typeset_text": result["typeset_text"],
                    "handwritten_text": result["handwritten_text"],
                    "sketch_descriptions": result["sketch_descriptions"],
                    "entities": result["entities"],
                    "page_summary": result["page_summary"],
                    "model": VISION_MODEL,
                    "transcribed_at": datetime.now(timezone.utc).isoformat(),
                }
                upsert_page(transcription, page_payload)
                write_json(transcription_path, transcription)
                log.info("%s p%s: transcribed.", item_id, page_number)
            except Exception as exc:
                log.error("%s p%s: transcription failed: %s", item_id, page_number, exc)

            time.sleep(API_DELAY_SECONDS)

    log.info("Transcription pass complete.")


if __name__ == "__main__":
    main()
