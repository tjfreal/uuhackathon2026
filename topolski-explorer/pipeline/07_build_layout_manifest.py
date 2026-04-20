"""
07_build_layout_manifest.py — Build Layout Manifest v1

Creates a first-pass layout scaffold from saved page-level extraction outputs.
This does not claim true geometry. It records provisional region guesses so the
next iteration can become explicitly layout-aware instead of page-monolithic.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()

STAGED_DATA_DIR = Path(os.getenv("STAGED_DATA_DIR", "data/staged"))
LAYOUT_MANIFEST_PATH = Path(os.getenv("LAYOUT_MANIFEST_PATH", "data/layout_manifest.json"))


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


def provisional_bounds(label: str) -> dict[str, Any]:
    presets = {
        "typeset_block": {"x": 0.1, "y": 0.12, "w": 0.8, "h": 0.46},
        "handwritten_block": {"x": 0.08, "y": 0.08, "w": 0.84, "h": 0.22},
        "caption": {"x": 0.1, "y": 0.8, "w": 0.8, "h": 0.12},
        "footer": {"x": 0.05, "y": 0.9, "w": 0.9, "h": 0.08},
        "sidebar": {"x": 0.78, "y": 0.1, "w": 0.17, "h": 0.7},
        "index_or_list": {"x": 0.08, "y": 0.1, "w": 0.84, "h": 0.76},
        "sketch_region": {"x": 0.08, "y": 0.18, "w": 0.84, "h": 0.58},
        "mixed_region": {"x": 0.06, "y": 0.08, "w": 0.88, "h": 0.84},
    }
    return {
        "provisional": True,
        "mode": "page_fraction_guess",
        **presets.get(label, presets["mixed_region"]),
    }


def infer_region_types(page: dict[str, Any]) -> list[dict[str, Any]]:
    typeset_text = normalize_text(page.get("typeset_text"))
    handwritten_text = normalize_text(page.get("handwritten_text"))
    summary = normalize_text(page.get("page_summary"))
    sketches = normalize_list(page.get("sketch_descriptions"))

    lower_typeset = typeset_text.lower()
    regions: list[dict[str, Any]] = []

    def add_region(region_type: str, evidence: dict[str, Any]) -> None:
        regions.append(
            {
                "region_type": region_type,
                "bounds": provisional_bounds(region_type),
                "evidence": evidence,
            }
        )

    if any(token in lower_typeset for token in ("index", "list of drawings", "numbers refer to drawings")):
        add_region("index_or_list", {"source": "typeset_text", "reason": "index/list keywords"})

    if typeset_text:
        add_region(
            "typeset_block",
            {"source": "typeset_text", "word_count": len(typeset_text.split())},
        )

    if handwritten_text:
        target = "sidebar" if len(handwritten_text.split()) <= 8 else "handwritten_block"
        add_region(
            target,
            {"source": "handwritten_text", "word_count": len(handwritten_text.split())},
        )

    if sketches:
        add_region(
            "sketch_region",
            {"source": "sketch_descriptions", "sketch_count": len(sketches)},
        )

    if summary and not regions:
        add_region("mixed_region", {"source": "page_summary", "reason": "summary-only fallback"})

    if summary and any(token in summary.lower() for token in ("footer", "caption", "label", "inset")):
        add_region("caption", {"source": "page_summary", "reason": "caption/inset cue"})

    if typeset_text and typeset_text.count("\n") >= 8:
        add_region("footer", {"source": "typeset_text", "reason": "dense multiline tail may imply footer/list spill"})

    if not regions:
        add_region("mixed_region", {"source": "fallback", "reason": "no stronger signal available"})

    return regions


def build_manifest() -> dict[str, Any]:
    item_dirs = sorted(path for path in STAGED_DATA_DIR.iterdir() if path.is_dir()) if STAGED_DATA_DIR.exists() else []
    items: dict[str, Any] = {}
    page_count = 0

    for item_dir in item_dirs:
        item_id = item_dir.name
        transcription_path = item_dir / "transcription.json"
        if not transcription_path.exists():
            continue

        transcription = load_json(transcription_path)
        item_pages: list[dict[str, Any]] = []
        for page in transcription.get("pages", []):
            page_number = int(page.get("page_number", 0))
            regions = infer_region_types(page)
            item_pages.append(
                {
                    "page_number": page_number,
                    "layout_confidence": "provisional",
                    "regions": regions,
                    "notes": [
                        "Bounds are inferred placeholders, not measured geometry.",
                        "This manifest exists to make region-aware v2 concrete, not to fake precision.",
                    ],
                }
            )
            page_count += 1
        items[item_id] = {"page_count": len(item_pages), "pages": item_pages}

    return {
        "schema_version": "2026-04-19-layout-manifest-v1",
        "manifest_path": LAYOUT_MANIFEST_PATH.as_posix(),
        "provisional": True,
        "notes": [
            "This is a scaffold for layout-aware extraction.",
            "Region bounds are page-fraction guesses derived from current page-level signals.",
            "True geometry should be added in a later segmentation stage.",
        ],
        "corpus_summary": {
            "item_count": len(items),
            "page_count": page_count,
        },
        "items": items,
    }


def main() -> None:
    manifest = build_manifest()
    write_json(LAYOUT_MANIFEST_PATH, manifest)
    print(f"Wrote layout manifest to {LAYOUT_MANIFEST_PATH}")
    print(
        f"Items: {manifest['corpus_summary']['item_count']} "
        f"Pages: {manifest['corpus_summary']['page_count']}"
    )


if __name__ == "__main__":
    main()
