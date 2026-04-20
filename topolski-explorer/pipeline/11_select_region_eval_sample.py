"""
11_select_region_eval_sample.py

Build a deterministic evaluation subset of pages and regions from the current corpus slice.

The goal is not random sampling. The goal is to choose pages that stress the system in ways
that matter:
  - index-like or list-like pages
  - handwriting-heavy pages
  - sketch-heavy pages
  - mixed-layout pages
  - weakly characterized pages that likely need region-aware recovery

This output is meant to guide exacting comparison work across whole-page and region-aware lanes.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


FEATURE_MANIFEST_PATH = Path(os.getenv("FEATURE_MANIFEST_PATH", "data/feature_manifest.json"))
LAYOUT_MANIFEST_PATH = Path(os.getenv("LAYOUT_MANIFEST_PATH", "data/layout_manifest.json"))
REGION_CROP_MANIFEST_PATH = Path(os.getenv("REGION_CROP_MANIFEST_PATH", "data/region_crop_manifest.json"))
OUTPUT_PATH = Path(os.getenv("REGION_EVAL_SAMPLE_PATH", "data/region_eval_sample.json"))
PAGES_PER_BUCKET = int(os.getenv("REGION_EVAL_PAGES_PER_BUCKET", "4"))


@dataclass(frozen=True)
class CandidatePage:
    bucket: str
    item_id: str
    title: str
    page_number: int
    score: int
    rationale: str
    feature_flags: dict[str, bool]
    word_counts: dict[str, int]
    sketch_count: int
    entity_count: int
    indexed_chunk_types: list[str]
    layout_region_types: list[str]
    crop_region_types: list[str]


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=True)
        handle.write("\n")


def coerce_pages(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return list(value.values())
    return []


def build_layout_lookup(layout_manifest: dict[str, Any]) -> dict[tuple[str, int], list[str]]:
    lookup: dict[tuple[str, int], list[str]] = {}
    for item_id, item in (layout_manifest.get("items") or {}).items():
        for page in coerce_pages(item.get("pages")):
            page_number = int(page.get("page_number", 0))
            region_types = sorted(
                {
                    region.get("region_type", "")
                    for region in page.get("regions", [])
                    if region.get("region_type")
                }
            )
            lookup[(str(item_id), page_number)] = region_types
    return lookup


def build_crop_lookup(crop_manifest: dict[str, Any]) -> dict[tuple[str, int], list[str]]:
    lookup: dict[tuple[str, int], list[str]] = {}
    for item_id, item in (crop_manifest.get("items") or {}).items():
        for page in coerce_pages(item.get("pages")):
            page_number = int(page.get("page_number", 0))
            region_types = sorted(
                {
                    region.get("region_type", "")
                    for region in page.get("regions", [])
                    if region.get("region_type")
                }
            )
            lookup[(str(item_id), page_number)] = region_types
    return lookup


def build_weak_page_lookup(feature_manifest: dict[str, Any]) -> dict[str, set[int]]:
    lookup: dict[str, set[int]] = {}
    for item_id, item in (feature_manifest.get("items") or {}).items():
        weak_pages = set(int(page) for page in item.get("weakly_characterized_pages", []))
        lookup[str(item_id)] = weak_pages
    return lookup


def candidate_pages(
    feature_manifest: dict[str, Any],
    layout_lookup: dict[tuple[str, int], list[str]],
    crop_lookup: dict[tuple[str, int], list[str]],
) -> list[CandidatePage]:
    pages: list[CandidatePage] = []
    weak_lookup = build_weak_page_lookup(feature_manifest)

    for item_id, item in (feature_manifest.get("items") or {}).items():
        title = item.get("title") or str(item_id)
        for page in item.get("pages", []):
            page_number = int(page.get("page_number", 0))
            page_key = (str(item_id), page_number)
            feature_flags = {
                "has_typeset_text": bool(page.get("has_typeset_text")),
                "has_handwritten_text": bool(page.get("has_handwritten_text")),
                "has_sketches": bool(page.get("has_sketches")),
                "has_entities": bool(page.get("has_entities")),
                "has_summary": bool(page.get("has_summary")),
                "is_index_like": bool(page.get("is_index_like")),
                "is_list_like": bool(page.get("is_list_like")),
                "is_text_heavy": bool(page.get("is_text_heavy")),
                "is_image_heavy": bool(page.get("is_image_heavy")),
            }
            word_counts = page.get("word_counts", {}) or {}
            sketch_count = int(page.get("sketch_count", 0) or 0)
            entity_count = int(page.get("entity_count", 0) or 0)
            indexed_chunk_types = sorted(page.get("indexed_chunk_types", []) or [])
            layout_region_types = layout_lookup.get(page_key, [])
            crop_region_types = crop_lookup.get(page_key, [])
            is_weak = page_number in weak_lookup.get(str(item_id), set())

            bucket_specs: list[tuple[str, int, str]] = []

            if feature_flags["is_index_like"] or feature_flags["is_list_like"]:
                score = (
                    100
                    + word_counts.get("typeset", 0)
                    + entity_count * 2
                    + len(layout_region_types)
                )
                bucket_specs.append(
                    ("index_like", score, "Dense names, places, or list-like structure make this a likely index test page.")
                )

            if feature_flags["has_handwritten_text"]:
                score = (
                    100
                    + word_counts.get("handwritten", 0) * 3
                    + len(crop_region_types)
                )
                bucket_specs.append(
                    ("handwriting_heavy", score, "Handwriting was detected here, which makes it a good stress test for region-aware rereads.")
                )

            if feature_flags["has_sketches"]:
                score = (
                    100
                    + sketch_count * 5
                    + (10 if feature_flags["is_image_heavy"] else 0)
                    + len(indexed_chunk_types)
                )
                bucket_specs.append(
                    ("sketch_heavy", score, "Sketch density is high enough to test visual-semantic retrieval against text-centric lanes.")
                )

            if feature_flags["has_typeset_text"] and feature_flags["has_sketches"] and len(layout_region_types) >= 2:
                score = (
                    100
                    + word_counts.get("typeset", 0)
                    + sketch_count * 4
                    + len(layout_region_types) * 3
                )
                bucket_specs.append(
                    ("mixed_layout", score, "This page appears to mix text and sketches across multiple region types.")
                )

            if is_weak:
                score = 100 + len(layout_region_types) + len(crop_region_types)
                bucket_specs.append(
                    ("weakly_characterized", score, "The current pipeline considers this page weakly characterized, making it a strong comparison target.")
                )

            for bucket, score, rationale in bucket_specs:
                pages.append(
                    CandidatePage(
                        bucket=bucket,
                        item_id=str(item_id),
                        title=title,
                        page_number=page_number,
                        score=score,
                        rationale=rationale,
                        feature_flags=feature_flags,
                        word_counts={
                            "typeset": int(word_counts.get("typeset", 0) or 0),
                            "handwritten": int(word_counts.get("handwritten", 0) or 0),
                            "summary": int(word_counts.get("summary", 0) or 0),
                        },
                        sketch_count=sketch_count,
                        entity_count=entity_count,
                        indexed_chunk_types=indexed_chunk_types,
                        layout_region_types=layout_region_types,
                        crop_region_types=crop_region_types,
                    )
                )

    return pages


def select_pages(candidates: list[CandidatePage]) -> dict[str, list[CandidatePage]]:
    grouped: dict[str, list[CandidatePage]] = {}
    for candidate in candidates:
        grouped.setdefault(candidate.bucket, []).append(candidate)

    selections: dict[str, list[CandidatePage]] = {}
    chosen_pages: set[tuple[str, int]] = set()

    for bucket in sorted(grouped):
        ranked = sorted(
            grouped[bucket],
            key=lambda candidate: (-candidate.score, candidate.item_id, candidate.page_number),
        )
        picked: list[CandidatePage] = []
        for candidate in ranked:
            page_key = (candidate.item_id, candidate.page_number)
            if page_key in chosen_pages:
                continue
            picked.append(candidate)
            chosen_pages.add(page_key)
            if len(picked) >= PAGES_PER_BUCKET:
                break
        selections[bucket] = picked

    return selections


def build_output(
    feature_manifest: dict[str, Any],
    layout_manifest: dict[str, Any],
    crop_manifest: dict[str, Any],
) -> dict[str, Any]:
    layout_lookup = build_layout_lookup(layout_manifest)
    crop_lookup = build_crop_lookup(crop_manifest)
    candidates = candidate_pages(feature_manifest, layout_lookup, crop_lookup)
    selections = select_pages(candidates)

    buckets: list[dict[str, Any]] = []
    total_selected_pages = 0
    for bucket_name, pages in selections.items():
        total_selected_pages += len(pages)
        buckets.append(
            {
                "bucket": bucket_name,
                "page_count": len(pages),
                "pages": [
                    {
                        "item_id": page.item_id,
                        "title": page.title,
                        "page_number": page.page_number,
                        "score": page.score,
                        "rationale": page.rationale,
                        "feature_flags": page.feature_flags,
                        "word_counts": page.word_counts,
                        "sketch_count": page.sketch_count,
                        "entity_count": page.entity_count,
                        "indexed_chunk_types": page.indexed_chunk_types,
                        "layout_region_types": page.layout_region_types,
                        "crop_region_types": page.crop_region_types,
                    }
                    for page in pages
                ],
            }
        )

    return {
        "schema_version": "2026-04-19-region-eval-sample-v1",
        "notes": [
            "This is a deterministic selection of representative pages for exacting comparison work.",
            "Selections are intentionally stress cases, not a statistically neutral sample.",
        ],
        "source_artifacts": {
            "feature_manifest": FEATURE_MANIFEST_PATH.as_posix(),
            "layout_manifest": LAYOUT_MANIFEST_PATH.as_posix(),
            "region_crop_manifest": REGION_CROP_MANIFEST_PATH.as_posix(),
        },
        "selection_parameters": {
            "pages_per_bucket": PAGES_PER_BUCKET,
        },
        "corpus_context": {
            "feature_item_count": len((feature_manifest.get("items") or {})),
            "layout_item_count": len((layout_manifest.get("items") or {})),
            "crop_item_count": len((crop_manifest.get("items") or {})),
        },
        "summary": {
            "bucket_count": len(buckets),
            "selected_page_count": total_selected_pages,
        },
        "buckets": buckets,
    }


def main() -> None:
    feature_manifest = load_json(FEATURE_MANIFEST_PATH)
    layout_manifest = load_json(LAYOUT_MANIFEST_PATH)
    crop_manifest = load_json(REGION_CROP_MANIFEST_PATH)
    payload = build_output(feature_manifest, layout_manifest, crop_manifest)
    write_json(OUTPUT_PATH, payload)
    print(f"Wrote region eval sample to {OUTPUT_PATH}")
    print(f"Selected {payload['summary']['selected_page_count']} pages across {payload['summary']['bucket_count']} buckets")


if __name__ == "__main__":
    main()
