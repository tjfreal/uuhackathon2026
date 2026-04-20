"""
09_transcribe_regions.py — Region-Level Vision Transcription Experiment

Consumes a crop manifest produced from provisional layout-aware scaffolding and runs
targeted OpenAI vision calls on region crop images. Results are saved to a durable
region transcription manifest under data/ so they can be compared against the
existing page-level transcription pipeline.

This script is resume-safe at the region level:
  - completed regions are skipped on rerun
  - results are written immediately after each successful region call
  - the output records model, provenance, and the fact that region bounds are
    provisional unless a later stage proves otherwise
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

DATA_DIR = Path(os.getenv("TOPOLSKI_DATA_DIR", "data"))
REGION_CROP_MANIFEST_PATH = Path(
    os.getenv("REGION_CROP_MANIFEST_PATH", str(DATA_DIR / "region_crop_manifest.json"))
)
REGION_TRANSCRIPTION_MANIFEST_PATH = Path(
    os.getenv("REGION_TRANSCRIPTION_MANIFEST_PATH", str(DATA_DIR / "region_transcription_manifest.json"))
)
VISION_MODEL = os.getenv("OPENAI_REGION_VISION_MODEL") or os.getenv("OPENAI_VISION_MODEL", "gpt-4.1")
OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_REGION_VISION_MAX_TOKENS", os.getenv("OPENAI_VISION_MAX_TOKENS", "2500")))
API_DELAY_SECONDS = float(os.getenv("OPENAI_API_DELAY_SECONDS", "0.5"))
SCHEMA_VERSION = "2026-04-19-region-transcription-v1"

client = OpenAI()

SYSTEM_PROMPT = """You are analyzing a cropped region from a page of Topolski's Chronicle,
an illustrated broadsheet with mixed layout, typeset editorial text, handwritten
notes, captions, lists, and expressive sketches.

This is an experimental region-level read. Many regions come from provisional layout
guesses, so be careful about uncertainty and avoid inventing detail not visible in
the crop. The goal is retrieval-friendly structured understanding that can later be
compared against page-level analysis."""

REGION_PROMPTS = {
    "typeset_block": """This crop is expected to contain mostly printed or typeset text.
Prioritize accurate transcription of printed text. Mention sketches only if clearly present.""",
    "handwritten_block": """This crop is expected to contain handwritten notes or captions.
Prioritize best-effort handwriting transcription. Mark uncertain words with [?].""",
    "caption": """This crop is expected to contain a caption, inset, or small explanatory text.
Transcribe compact text carefully and describe any nearby visual cue briefly.""",
    "footer": """This crop is expected to contain footer material, numbering, references, or small print.
Prioritize small typeset text and reference-like content.""",
    "sidebar": """This crop may contain marginal notes, sidebars, or narrow column text.
Recover text carefully and note if the crop is too partial to read cleanly.""",
    "index_or_list": """This crop is expected to contain an index, list, or numbered references.
Preserve numbering structure where possible and capture list semantics in the summary.""",
    "sketch_region": """This crop is expected to be primarily visual. Focus on specific sketch
descriptions, figures, scene content, and any visible labels or captions.""",
    "mixed_region": """This crop may contain mixed text and drawing content. Recover both text
and scene description without overcommitting to uncertain boundaries.""",
}

USER_PROMPT_TEMPLATE = """Return a single JSON object with this exact structure:

{{
  "typeset_text": "Full transcription of printed/typeset text visible in this crop. Empty string if none.",
  "handwritten_text": "Best-effort transcription of handwritten text visible in this crop. Mark uncertain words with [?]. Empty string if none.",
  "sketch_descriptions": [
    "One concise but specific description per distinct drawing, figure group, or visual scene visible in this crop."
  ],
  "entities": {{
    "people": ["Named or strongly identifiable people shown or mentioned"],
    "places": ["Places, buildings, regions, or geographic references"],
    "events": ["Named events, conflicts, public occasions, or political moments"],
    "dates": ["Dates, years, eras, or time expressions"]
  }},
  "page_summary": "A concise 1-2 sentence summary of what this crop appears to capture."
}}

Rules:
- Return only valid JSON.
- Do not include markdown fences.
- If a field is absent, use an empty string or empty list.
- Do not claim complete page coverage; summarize only what seems visible in this crop.
- Remember that this region is provisional and may be partial.

Region type: {region_type}
Region prompt: {region_prompt}
"""


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


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


def normalize_region_result(raw_result: dict[str, Any]) -> dict[str, Any]:
    return {
        "typeset_text": normalize_text(raw_result.get("typeset_text")),
        "handwritten_text": normalize_text(raw_result.get("handwritten_text")),
        "sketch_descriptions": normalize_string_list(raw_result.get("sketch_descriptions")),
        "entities": normalize_entities(raw_result.get("entities")),
        "page_summary": normalize_text(raw_result.get("page_summary")),
    }


def is_valid_completed_region(region: dict[str, Any]) -> bool:
    required_fields = {
        "region_id",
        "region_type",
        "crop_path",
        "typeset_text",
        "handwritten_text",
        "sketch_descriptions",
        "entities",
        "page_summary",
        "model",
        "transcribed_at",
        "provenance",
    }
    if not isinstance(region, dict) or not required_fields.issubset(region.keys()):
        return False
    if not isinstance(region.get("sketch_descriptions"), list):
        return False
    if not isinstance(region.get("entities"), dict):
        return False
    return True


def load_or_init_manifest(crop_manifest: dict[str, Any]) -> dict[str, Any]:
    if REGION_TRANSCRIPTION_MANIFEST_PATH.exists():
        existing = load_json(REGION_TRANSCRIPTION_MANIFEST_PATH)
        items = existing.get("items", {})
        normalized_items: dict[str, Any] = {}
        for item_id, item_record in items.items():
            pages = item_record.get("pages", {})
            normalized_pages: dict[str, Any] = {}
            for page_key, page_record in pages.items():
                regions = []
                for region in page_record.get("regions", []):
                    if not is_valid_completed_region(region):
                        continue
                    regions.append(region)
                normalized_pages[str(page_key)] = {
                    "page_number": int(page_record.get("page_number", page_key)),
                    "regions": sorted(regions, key=lambda entry: entry["region_id"]),
                }
            normalized_items[str(item_id)] = {
                "pages": normalized_pages,
            }
        return {
            "schema_version": SCHEMA_VERSION,
            "manifest_type": "region_transcription_experiment",
            "source_crop_manifest_path": normalize_text(existing.get("source_crop_manifest_path"))
            or REGION_CROP_MANIFEST_PATH.as_posix(),
            "source_crop_manifest_schema_version": normalize_text(existing.get("source_crop_manifest_schema_version"))
            or normalize_text(crop_manifest.get("schema_version")),
            "model": normalize_text(existing.get("model")) or VISION_MODEL,
            "generated_at": normalize_text(existing.get("generated_at")) or None,
            "notes": existing.get("notes") if isinstance(existing.get("notes"), list) else default_notes(),
            "items": normalized_items,
        }

    return {
        "schema_version": SCHEMA_VERSION,
        "manifest_type": "region_transcription_experiment",
        "source_crop_manifest_path": REGION_CROP_MANIFEST_PATH.as_posix(),
        "source_crop_manifest_schema_version": normalize_text(crop_manifest.get("schema_version")),
        "model": VISION_MODEL,
        "generated_at": None,
        "notes": default_notes(),
        "items": {},
    }


def default_notes() -> list[str]:
    return [
        "Region outputs are experimental and comparison-oriented.",
        "Crop provenance is provisional unless later stages attach measured geometry.",
        "This manifest mirrors page-level fields where practical so region-vs-page comparisons stay simple.",
    ]


def get_page_container(manifest: dict[str, Any], item_id: str, page_number: int) -> dict[str, Any]:
    item_record = manifest["items"].setdefault(str(item_id), {"pages": {}})
    pages = item_record["pages"]
    page_key = str(page_number)
    if page_key not in pages:
        pages[page_key] = {"page_number": page_number, "regions": []}
    return pages[page_key]


def upsert_region(manifest: dict[str, Any], item_id: str, page_number: int, region_payload: dict[str, Any]) -> None:
    page_record = get_page_container(manifest, item_id, page_number)
    for index, existing in enumerate(page_record["regions"]):
        if existing["region_id"] == region_payload["region_id"]:
            page_record["regions"][index] = region_payload
            break
    else:
        page_record["regions"].append(region_payload)
    page_record["regions"].sort(key=lambda entry: entry["region_id"])
    manifest["model"] = VISION_MODEL
    manifest["generated_at"] = datetime.now(timezone.utc).isoformat()


def iter_crop_regions(crop_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    items = crop_manifest.get("items")
    if isinstance(items, dict):
        for item_id, item_record in items.items():
            pages = item_record.get("pages", [])
            if isinstance(pages, dict):
                page_iterable = pages.values()
            else:
                page_iterable = pages if isinstance(pages, list) else []
            for page_record in page_iterable:
                page_number = int(page_record.get("page_number", 0))
                for index, region in enumerate(page_record.get("regions", []), start=1):
                    normalized_region = normalize_crop_region(item_id, page_number, region, index)
                    if normalized_region:
                        normalized.append(normalized_region)

    top_level_regions = crop_manifest.get("regions", [])
    if isinstance(top_level_regions, list):
        for index, region in enumerate(top_level_regions, start=1):
            item_id = normalize_text(region.get("item_id"))
            page_number = int(region.get("page_number", 0))
            normalized_region = normalize_crop_region(item_id, page_number, region, index)
            if normalized_region:
                normalized.append(normalized_region)

    normalized.sort(key=lambda entry: (entry["item_id"], entry["page_number"], entry["region_id"]))
    return normalized


def normalize_crop_region(item_id: str, page_number: int, region: dict[str, Any], ordinal: int) -> dict[str, Any] | None:
    if not item_id or not page_number or not isinstance(region, dict):
        return None

    region_type = normalize_text(region.get("region_type")) or "mixed_region"
    crop_path_value = (
        region.get("crop_path")
        or region.get("image_path")
        or region.get("filepath")
        or region.get("path")
    )
    crop_path = Path(str(crop_path_value)).expanduser() if crop_path_value else None
    if not crop_path:
        return None
    if not crop_path.is_absolute():
        crop_path = (Path.cwd() / crop_path).resolve()

    region_id = normalize_text(region.get("region_id"))
    if not region_id:
        region_id = "%s-p%03d-r%03d-%s" % (item_id, page_number, ordinal, region_type)

    bounds = region.get("bounds") if isinstance(region.get("bounds"), dict) else {}
    provenance = {
        "provisional": bool(bounds.get("provisional", region.get("provisional", True))),
        "basis": normalize_text(region.get("basis")) or normalize_text(bounds.get("mode")) or "provisional_layout_scaffold",
        "source_manifest_path": REGION_CROP_MANIFEST_PATH.as_posix(),
        "source_manifest_schema_version": None,
        "source_region_type": region_type,
        "source_region_notes": region.get("notes") if isinstance(region.get("notes"), list) else [],
    }

    return {
        "item_id": item_id,
        "page_number": page_number,
        "region_id": region_id,
        "region_type": region_type,
        "crop_path": crop_path,
        "bounds": bounds,
        "provenance": provenance,
    }


def build_completed_region_ids(manifest: dict[str, Any]) -> set[tuple[str, int, str]]:
    completed: set[tuple[str, int, str]] = set()
    for item_id, item_record in manifest.get("items", {}).items():
        pages = item_record.get("pages", {})
        if not isinstance(pages, dict):
            continue
        for page_record in pages.values():
            page_number = int(page_record.get("page_number", 0))
            for region in page_record.get("regions", []):
                if is_valid_completed_region(region):
                    completed.add((str(item_id), page_number, str(region["region_id"])))
    return completed


def prompt_for_region_type(region_type: str) -> str:
    return REGION_PROMPTS.get(region_type, REGION_PROMPTS["mixed_region"])


@retry(
    retry=retry_if_exception_type(Exception),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=4, max=30),
    reraise=True,
)
def transcribe_region(crop_path: Path, region_type: str) -> dict[str, Any]:
    b64 = encode_image(crop_path)
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
                            "url": "data:image/jpeg;base64,%s" % b64,
                            "detail": "high",
                        },
                    },
                    {
                        "type": "text",
                        "text": USER_PROMPT_TEMPLATE.format(
                            region_type=region_type,
                            region_prompt=prompt_for_region_type(region_type),
                        ),
                    },
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
    return normalize_region_result(parsed)


def main() -> None:
    if not REGION_CROP_MANIFEST_PATH.exists():
        raise FileNotFoundError("Missing crop manifest at %s" % REGION_CROP_MANIFEST_PATH)

    crop_manifest = load_json(REGION_CROP_MANIFEST_PATH)
    manifest = load_or_init_manifest(crop_manifest)
    regions = iter_crop_regions(crop_manifest)
    completed_region_ids = build_completed_region_ids(manifest)

    log.info("Found %s crop regions in %s.", len(regions), REGION_CROP_MANIFEST_PATH)
    for index, region in enumerate(regions, start=1):
        item_id = region["item_id"]
        page_number = region["page_number"]
        region_id = region["region_id"]
        crop_path = region["crop_path"]

        region["provenance"]["source_manifest_schema_version"] = normalize_text(crop_manifest.get("schema_version"))

        if (item_id, page_number, region_id) in completed_region_ids:
            log.info("[%s/%s] %s p%s %s: already complete, skipping.", index, len(regions), item_id, page_number, region_id)
            continue

        if not crop_path.exists():
            log.warning("[%s/%s] %s p%s %s: missing crop file at %s, skipping.", index, len(regions), item_id, page_number, region_id, crop_path)
            continue

        try:
            result = transcribe_region(crop_path, region["region_type"])
            region_payload = {
                "region_id": region_id,
                "region_type": region["region_type"],
                "crop_path": str(crop_path),
                "bounds": region["bounds"],
                "provenance": region["provenance"],
                "typeset_text": result["typeset_text"],
                "handwritten_text": result["handwritten_text"],
                "sketch_descriptions": result["sketch_descriptions"],
                "entities": result["entities"],
                "page_summary": result["page_summary"],
                "model": VISION_MODEL,
                "transcribed_at": datetime.now(timezone.utc).isoformat(),
            }
            upsert_region(manifest, item_id, page_number, region_payload)
            write_json(REGION_TRANSCRIPTION_MANIFEST_PATH, manifest)
            completed_region_ids.add((item_id, page_number, region_id))
            log.info("[%s/%s] %s p%s %s: transcribed.", index, len(regions), item_id, page_number, region_id)
        except Exception as exc:
            log.error("[%s/%s] %s p%s %s: transcription failed: %s", index, len(regions), item_id, page_number, region_id, exc)

        time.sleep(API_DELAY_SECONDS)

    log.info("Region transcription pass complete. Output: %s", REGION_TRANSCRIPTION_MANIFEST_PATH)


if __name__ == "__main__":
    main()
