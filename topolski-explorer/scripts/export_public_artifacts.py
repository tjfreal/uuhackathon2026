#!/usr/bin/env python3
"""
export_public_artifacts.py

Copies selected derived artifacts from the ignored live data directory into a tracked
publish-safe directory and builds a sanitized per-item assessment library.

This is deliberately conservative. It avoids raw scans, rendered page images, crop images,
and the live vector store.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "published_artifacts"
STAGED_DATA_DIR = DATA_DIR / "staged"
ARTIFACT_LIBRARY_DIR = OUTPUT_DIR / "artifact_library"

FILES_TO_COPY = [
    "feature_manifest.json",
    "layout_manifest.json",
    "region_eval_sample.json",
    "region_crop_manifest_sample.json",
    "region_transcription_manifest_sample.json",
]


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=True)
        handle.write("\n")


def sanitize_pathish_string(value: object) -> str:
    text = normalize_string(value)
    if not text:
        return ""
    filename = Path(text).name
    return filename or text


def sanitize_region_crop_manifest(manifest: dict) -> dict:
    sanitized = dict(manifest)
    sanitized["source_layout_manifest"] = "published_artifacts/layout_manifest.json"
    sanitized["output_root"] = "omitted_from_public_artifacts"

    items = {}
    for item_id, item in (manifest.get("items") or {}).items():
        pages_out = []
        for page in item.get("pages", []):
            regions_out = []
            for region in page.get("regions", []):
                region_out = dict(region)
                region_out.pop("source_image_path", None)
                region_out["crop_path"] = sanitize_pathish_string(region.get("crop_path"))
                regions_out.append(region_out)
            page_out = dict(page)
            page_out["regions"] = regions_out
            pages_out.append(page_out)
        items[str(item_id)] = {"page_count": item.get("page_count", len(pages_out)), "pages": pages_out}
    sanitized["items"] = items
    return sanitized


def sanitize_region_transcription_manifest(manifest: dict) -> dict:
    sanitized = dict(manifest)
    sanitized["source_crop_manifest_path"] = "published_artifacts/region_crop_manifest_sample.json"
    items = {}
    for item_id, item in (manifest.get("items") or {}).items():
        pages_out = {}
        for page_key, page in (item.get("pages") or {}).items():
            regions_out = []
            for region in page.get("regions", []):
                region_out = dict(region)
                region_out["crop_path"] = sanitize_pathish_string(region.get("crop_path"))
                provenance = dict(region.get("provenance", {}))
                if provenance.get("source_manifest_path"):
                    provenance["source_manifest_path"] = "published_artifacts/region_crop_manifest_sample.json"
                region_out["provenance"] = provenance
                regions_out.append(region_out)
            page_out = dict(page)
            page_out["regions"] = regions_out
            pages_out[str(page_key)] = page_out
        items[str(item_id)] = {"pages": pages_out}
    sanitized["items"] = items
    return sanitized


def sanitize_processing_matrix(manifest: dict) -> dict:
    sanitized = dict(manifest)
    generated = dict(manifest.get("generated_artifacts", {}))
    generated["json"] = "published_artifacts/processing_matrix.json"
    generated["markdown"] = "published_artifacts/processing_matrix.md"
    sanitized["generated_artifacts"] = generated

    artifact_state = dict(manifest.get("artifact_state", {}))
    index_state = dict(artifact_state.get("index_state", {}))
    if "path" in index_state:
        index_state["path"] = "omitted_from_public_artifacts"
    artifact_state["index_state"] = index_state
    sanitized["artifact_state"] = artifact_state

    approaches_out = []
    for approach in manifest.get("approaches", []):
        approach_out = dict(approach)
        paths = []
        for path in approach.get("artifact_paths", []):
            text = normalize_string(path)
            if not text:
                continue
            if "data/staged" in text:
                paths.append("published_artifacts/artifact_library/")
            elif "data/chroma" in text:
                paths.append("rebuild_locally")
            elif "data/region_crop_manifest_sample.json" in text:
                paths.append("published_artifacts/region_crop_manifest_sample.json")
            elif "data/region_transcription_manifest_sample.json" in text:
                paths.append("published_artifacts/region_transcription_manifest_sample.json")
            else:
                paths.append(text)
        approach_out["artifact_paths"] = paths
        approaches_out.append(approach_out)
    sanitized["approaches"] = approaches_out
    return scrub_public_strings(sanitized)


def scrub_public_strings(value: object) -> object:
    if isinstance(value, dict):
        return {key: scrub_public_strings(subvalue) for key, subvalue in value.items()}
    if isinstance(value, list):
        return [scrub_public_strings(subvalue) for subvalue in value]
    if isinstance(value, str):
        return (
            value.replace("data/staged/{item_id}/pages/", "published artifact library page assessments")
            .replace("data/staged", "published_artifacts/artifact_library")
            .replace("data/chroma/chroma.sqlite3", "local rebuilt index")
            .replace("data/chroma", "local rebuilt index")
            .replace("data/region_crop_manifest_sample.json", "published_artifacts/region_crop_manifest_sample.json")
            .replace("data/region_transcription_manifest_sample.json", "published_artifacts/region_transcription_manifest_sample.json")
        )
    return value


def sanitize_copied_payload(name: str, payload: dict) -> dict:
    if name == "region_crop_manifest_sample.json":
        return sanitize_region_crop_manifest(payload)
    if name == "region_transcription_manifest_sample.json":
        return sanitize_region_transcription_manifest(payload)
    if name == "processing_matrix.json":
        return sanitize_processing_matrix(payload)
    return payload


def normalize_string(value: object) -> str:
    if isinstance(value, str):
        return value.strip()
    return ""


def normalize_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def sanitize_metadata(item_id: str, metadata: dict) -> dict:
    source = metadata.get("metadata", {}) if isinstance(metadata.get("metadata"), dict) else {}
    return {
        "item_id": item_id,
        "title": normalize_string(source.get("Title")) or normalize_string(metadata.get("Title")) or item_id,
        "date": normalize_string(source.get("Date")) or normalize_string(metadata.get("Date")),
        "creator": normalize_string(source.get("Creator")),
        "description": normalize_string(source.get("Description")),
        "rights": normalize_string(source.get("Rights")),
        "ark": normalize_string(source.get("ARK")),
        "reference_url": normalize_string(source.get("Reference\xa0URL")) or normalize_string(metadata.get("item_url")),
        "source_label": "Topolski Chronicles digital collection",
    }


def sanitize_page(page: dict) -> dict:
    entities = page.get("entities", {}) if isinstance(page.get("entities"), dict) else {}
    return {
        "page_number": int(page.get("page_number", 0)),
        "typeset_text": normalize_string(page.get("typeset_text")),
        "handwritten_text": normalize_string(page.get("handwritten_text")),
        "sketch_descriptions": normalize_list(page.get("sketch_descriptions")),
        "entities": {
            "people": normalize_list(entities.get("people")),
            "places": normalize_list(entities.get("places")),
            "events": normalize_list(entities.get("events")),
            "dates": normalize_list(entities.get("dates")),
        },
        "page_summary": normalize_string(page.get("page_summary")),
        "model": normalize_string(page.get("model")),
        "transcribed_at": normalize_string(page.get("transcribed_at")),
    }


def build_artifact_library() -> tuple[int, int]:
    ARTIFACT_LIBRARY_DIR.mkdir(parents=True, exist_ok=True)
    item_count = 0
    page_count = 0

    for metadata_path in sorted(STAGED_DATA_DIR.glob("*.json")):
        item_id = metadata_path.stem
        transcription_path = STAGED_DATA_DIR / item_id / "transcription.json"
        if not transcription_path.exists():
            continue

        metadata = load_json(metadata_path)
        transcription = load_json(transcription_path)
        pages = [sanitize_page(page) for page in transcription.get("pages", []) if int(page.get("page_number", 0) or 0) > 0]
        if not pages:
            continue

        payload = {
            "schema_version": "2026-04-19-topolski-public-artifact-v1",
            "artifact_type": "topolski_item_assessment",
            "item": sanitize_metadata(item_id, metadata),
            "page_count": len(pages),
            "pages": pages,
        }
        write_json(ARTIFACT_LIBRARY_DIR / f"{item_id}.json", payload)
        item_count += 1
        page_count += len(pages)

    write_json(
        OUTPUT_DIR / "artifact_library_manifest.json",
        {
            "schema_version": "2026-04-19-topolski-public-artifact-library-v1",
            "artifact_type": "topolski_public_artifact_library",
            "item_count": item_count,
            "page_count": page_count,
            "artifact_dir": "published_artifacts/artifact_library",
        },
    )

    return item_count, page_count


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    copied = 0
    missing = 0

    for name in FILES_TO_COPY:
        source = DATA_DIR / name
        target = OUTPUT_DIR / name
        if not source.exists():
            print(f"missing: {source}")
            missing += 1
            continue
        if source.suffix == ".json":
            payload = load_json(source)
            write_json(target, sanitize_copied_payload(name, payload))
        else:
            shutil.copy2(source, target)
        print(f"copied: {source} -> {target}")
        copied += 1

    artifact_items, artifact_pages = build_artifact_library()
    print(f"artifact_library: items={artifact_items} pages={artifact_pages}")
    print(f"done: copied={copied} missing={missing}")


if __name__ == "__main__":
    main()
