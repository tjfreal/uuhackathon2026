"""
10_build_processing_matrix.py — Build Processing Approaches Matrix

Creates a deterministic report over the Topolski pipeline's current processing
approaches. The matrix is meant to be inspectable, durable, and honest about
what exists now versus what is only scaffolded or still hypothetical.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()

DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
STAGED_DATA_DIR = Path(os.getenv("STAGED_DATA_DIR", "data/staged"))
CHROMA_DB_PATH = Path(os.getenv("CHROMA_DB_PATH", "data/chroma"))
FEATURE_MANIFEST_PATH = Path(os.getenv("FEATURE_MANIFEST_PATH", "data/feature_manifest.json"))
LAYOUT_MANIFEST_PATH = Path(os.getenv("LAYOUT_MANIFEST_PATH", "data/layout_manifest.json"))
CROP_MANIFEST_PATH = Path(os.getenv("CROP_MANIFEST_PATH", "data/crop_manifest.json"))
if CROP_MANIFEST_PATH.name == "crop_manifest.json":
    CROP_MANIFEST_PATH = Path(os.getenv("REGION_CROP_MANIFEST_PATH", "data/region_crop_manifest.json"))
REGION_TRANSCRIPTION_MANIFEST_PATH = Path(
    os.getenv("REGION_TRANSCRIPTION_MANIFEST_PATH", "data/region_transcription_manifest.json")
)
PROCESSING_MATRIX_JSON_PATH = Path(
    os.getenv("PROCESSING_MATRIX_JSON_PATH", "data/processing_matrix.json")
)
PROCESSING_MATRIX_MD_PATH = Path(
    os.getenv("PROCESSING_MATRIX_MD_PATH", "data/processing_matrix.md")
)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def unique_sorted(values: list[str]) -> list[str]:
    return sorted({value for value in values if value})


def count_transcription_artifacts() -> dict[str, Any]:
    summary = {
        "staged_item_count": 0,
        "transcribed_item_count": 0,
        "staged_page_count": 0,
        "transcribed_page_count": 0,
        "chunk_types_present": [],
    }
    chunk_types_present: set[str] = set()

    if not STAGED_DATA_DIR.exists():
        return summary

    item_dirs = sorted(path for path in STAGED_DATA_DIR.iterdir() if path.is_dir())
    summary["staged_item_count"] = len(item_dirs)

    for item_dir in item_dirs:
        metadata_path = STAGED_DATA_DIR / f"{item_dir.name}.json"
        if metadata_path.exists():
            metadata = load_json(metadata_path)
            page_images = metadata.get("page_images", [])
            if isinstance(page_images, list):
                summary["staged_page_count"] += len(page_images)

        transcription_path = item_dir / "transcription.json"
        if not transcription_path.exists():
            continue

        transcription = load_json(transcription_path)
        pages = transcription.get("pages", [])
        if isinstance(pages, list):
            summary["transcribed_item_count"] += 1
            summary["transcribed_page_count"] += len(pages)
            for page in pages:
                if page.get("typeset_text"):
                    chunk_types_present.add("text")
                if page.get("handwritten_text"):
                    chunk_types_present.add("handwriting")
                if page.get("sketch_descriptions"):
                    chunk_types_present.add("sketch")
                if page.get("entities"):
                    chunk_types_present.add("entities")
                if page.get("page_summary"):
                    chunk_types_present.add("summary")

    summary["chunk_types_present"] = sorted(chunk_types_present)
    return summary


def summarize_feature_manifest() -> dict[str, Any]:
    if not FEATURE_MANIFEST_PATH.exists():
        return {
            "exists": False,
            "item_count": 0,
            "page_count": 0,
            "indexed_page_count": 0,
            "feature_flags_present": [],
        }

    manifest = load_json(FEATURE_MANIFEST_PATH)
    corpus = manifest.get("corpus_summary", {})
    feature_counts = corpus.get("feature_counts", {})
    return {
        "exists": True,
        "item_count": int(corpus.get("staged_item_count", 0)),
        "page_count": int(corpus.get("transcribed_page_count", 0)),
        "indexed_page_count": int(corpus.get("indexed_page_count", 0)),
        "feature_flags_present": sorted(feature_counts.keys()),
    }


def summarize_layout_manifest() -> dict[str, Any]:
    if not LAYOUT_MANIFEST_PATH.exists():
        return {
            "exists": False,
            "item_count": 0,
            "page_count": 0,
            "region_types_present": [],
            "provisional": True,
        }

    manifest = load_json(LAYOUT_MANIFEST_PATH)
    region_types: set[str] = set()
    for item in manifest.get("items", {}).values():
        for page in item.get("pages", []):
            for region in page.get("regions", []):
                region_type = region.get("region_type")
                if region_type:
                    region_types.add(str(region_type))

    corpus = manifest.get("corpus_summary", {})
    return {
        "exists": True,
        "item_count": int(corpus.get("item_count", 0)),
        "page_count": int(corpus.get("page_count", 0)),
        "region_types_present": sorted(region_types),
        "provisional": bool(manifest.get("provisional", False)),
    }


def summarize_crop_manifest() -> dict[str, Any]:
    if not CROP_MANIFEST_PATH.exists():
        return {
            "exists": False,
            "item_count": 0,
            "page_count": 0,
            "crop_count": 0,
        }

    manifest = load_json(CROP_MANIFEST_PATH)
    corpus = manifest.get("corpus_summary", {})
    return {
        "exists": True,
        "item_count": int(corpus.get("item_count", 0)),
        "page_count": int(corpus.get("page_count", 0)),
        "crop_count": int(corpus.get("crop_count", 0)),
    }


def summarize_region_transcription_manifest() -> dict[str, Any]:
    if not REGION_TRANSCRIPTION_MANIFEST_PATH.exists():
        return {
            "exists": False,
            "item_count": 0,
            "page_count": 0,
            "region_count": 0,
        }

    manifest = load_json(REGION_TRANSCRIPTION_MANIFEST_PATH)
    corpus = manifest.get("corpus_summary", {})
    if corpus:
        item_count = int(corpus.get("item_count", 0))
        page_count = int(corpus.get("page_count", 0))
        region_count = int(corpus.get("region_count", 0))
    else:
        items = manifest.get("items", {})
        if isinstance(items, dict):
            item_values = list(items.values())
            item_count = len(item_values)
            page_count = 0
            region_count = 0
            for item in item_values:
                pages = item.get("pages", {})
                page_values = list(pages.values()) if isinstance(pages, dict) else pages
                page_count += len(page_values)
                for page in page_values:
                    region_count += len(page.get("regions", []))
        elif isinstance(items, list):
            item_count = len(items)
            page_count = 0
            region_count = 0
            for item in items:
                page_values = item.get("pages", [])
                if isinstance(page_values, dict):
                    page_values = list(page_values.values())
                page_count += len(page_values)
                for page in page_values:
                    region_count += len(page.get("regions", []))
        else:
            item_count = 0
            page_count = 0
            region_count = 0

    return {
        "exists": True,
        "item_count": item_count,
        "page_count": page_count,
        "region_count": region_count,
    }


def summarize_index_state() -> dict[str, Any]:
    sqlite_path = CHROMA_DB_PATH / "chroma.sqlite3"
    return {
        "exists": sqlite_path.exists(),
        "path": sqlite_path.as_posix(),
    }


def detect_status(exists: bool, page_count: int = 0, provisional: bool = False) -> str:
    if not exists:
        return "not_started"
    if provisional:
        return "provisional"
    if page_count > 0:
        return "active"
    return "scaffolded"


def build_approach_matrix(
    transcriptions: dict[str, Any],
    features: dict[str, Any],
    layouts: dict[str, Any],
    crops: dict[str, Any],
    region_transcriptions: dict[str, Any],
    index_state: dict[str, Any],
) -> list[dict[str, Any]]:
    staged_pages = transcriptions["staged_page_count"]
    transcribed_pages = transcriptions["transcribed_page_count"]

    return [
        {
            "approach_id": "whole_page_vision",
            "label": "Whole-page vision pass",
            "status": detect_status(transcribed_pages > 0, transcribed_pages),
            "currently_runnable": staged_pages > 0,
            "inputs": [
                "Rendered page images from data/staged/{item_id}/pages/",
                "OpenAI vision-capable model",
            ],
            "outputs": [
                "Per-item transcription.json",
                "Page-level typeset text, handwritten text, sketch descriptions, entities, page summary",
            ],
            "artifact_paths": unique_sorted(
                [
                    STAGED_DATA_DIR.as_posix(),
                ]
            ),
            "evidence": {
                "staged_pages": staged_pages,
                "transcribed_pages": transcribed_pages,
                "chunk_types_present": transcriptions["chunk_types_present"],
            },
            "known_strengths": [
                "Makes the corpus searchable quickly from a cold start.",
                "Captures broad scene semantics and a first pass over mixed text plus image content.",
                "Produces durable local artifacts that can feed later indexing and evaluation.",
            ],
            "known_weaknesses": [
                "Single-pass page reading is weak on small sidebars, footers, marginalia, and dense mixed layouts.",
                "Region boundaries are implicit rather than measured.",
                "Large broadsheet pages compress too much detail into one model call.",
            ],
            "open_questions": [
                "How often does the page pass miss small but important text regions?",
                "Which page classes actually need region rereads versus only better prompts?",
                "How stable is handwriting recovery across visually dense pages?",
            ],
        },
        {
            "approach_id": "page_text_embeddings",
            "label": "Page-level text embeddings",
            "status": detect_status(index_state["exists"], transcribed_pages),
            "currently_runnable": transcribed_pages > 0 and index_state["exists"],
            "inputs": [
                "Saved page-level transcription outputs",
                "Embedding model over extracted text fields",
            ],
            "outputs": [
                "Local Chroma vectors for page-derived text lanes",
                "Searchable page-level semantic retrieval",
            ],
            "artifact_paths": unique_sorted([CHROMA_DB_PATH.as_posix()]),
            "evidence": {
                "index_present": index_state["exists"],
                "transcribed_pages": transcribed_pages,
            },
            "known_strengths": [
                "Durable local retrieval once embeddings are written.",
                "Cheap to query compared with repeated live model calls.",
                "Good baseline for topical and entity-led search.",
            ],
            "known_weaknesses": [
                "Only as good as the upstream page extraction.",
                "Page granularity can blur local matches into broad page-level hits.",
                "Weak text recovery leads directly to weak recall.",
            ],
            "open_questions": [
                "Would smaller text windows outperform page-level chunks for specific topical queries?",
                "How much recall is lost when text recovery is incomplete but sketch understanding is strong?",
            ],
        },
        {
            "approach_id": "blended_retrieval",
            "label": "Blended retrieval lanes",
            "status": detect_status(index_state["exists"], transcribed_pages),
            "currently_runnable": transcribed_pages > 0 and index_state["exists"],
            "inputs": [
                "Page text",
                "Sketch descriptions",
                "Entities",
                "Page summaries",
            ],
            "outputs": [
                "Multi-lane index supporting text, sketch, entities, summary, and blended retrieval",
                "Aggregated result evidence at page level",
            ],
            "artifact_paths": unique_sorted([CHROMA_DB_PATH.as_posix(), FEATURE_MANIFEST_PATH.as_posix()]),
            "evidence": {
                "index_present": index_state["exists"],
                "feature_manifest_present": features["exists"],
                "available_feature_flags": features["feature_flags_present"],
            },
            "known_strengths": [
                "Better matches visual or thematic queries than plain OCR-style text alone.",
                "Preserves multiple semantic readings of the same page.",
                "Makes the collection more explorable even before layout-aware extraction exists.",
            ],
            "known_weaknesses": [
                "Difficult to interpret when lanes disagree.",
                "Still page-monolithic underneath; evidence is mixed together before boundaries are reliable.",
                "Needs explicit evaluation to show which lane helped each query.",
            ],
            "open_questions": [
                "Which lane carries the real wins for topics like crowds, architecture, ceremonies, or travel?",
                "Should certain query types route to specific lanes rather than blended search?",
            ],
        },
        {
            "approach_id": "provisional_layout_manifest",
            "label": "Provisional layout manifest",
            "status": detect_status(layouts["exists"], layouts["page_count"], provisional=layouts["provisional"]),
            "currently_runnable": transcribed_pages > 0,
            "inputs": [
                "Saved page-level transcription outputs",
                "Heuristic region typing and provisional page-fraction bounds",
            ],
            "outputs": [
                "data/layout_manifest.json",
                "Region candidates such as typeset_block, handwritten_block, caption, footer, sidebar, index_or_list, sketch_region",
            ],
            "artifact_paths": unique_sorted([LAYOUT_MANIFEST_PATH.as_posix()]),
            "evidence": {
                "layout_manifest_present": layouts["exists"],
                "page_count": layouts["page_count"],
                "region_types_present": layouts["region_types_present"],
                "provisional": layouts["provisional"],
            },
            "known_strengths": [
                "Turns the next-stage layout problem into something concrete and inspectable.",
                "Provides a deterministic scaffold for downstream crop generation.",
                "Makes hidden uncertainty visible instead of pretending page-level extraction is enough.",
            ],
            "known_weaknesses": [
                "Bounds are guessed, not measured.",
                "Carries no direct proof that a detected region is geometrically correct.",
                "Useful for planning, not yet trustworthy for archival claims.",
            ],
            "open_questions": [
                "What segmentation strategy should replace heuristic bounds first?",
                "Which region classes matter most for actual retrieval gains: sidebars, index blocks, captions, or handwriting zones?",
            ],
        },
        {
            "approach_id": "region_crops",
            "label": "Region crops",
            "status": detect_status(crops["exists"], crops["page_count"]),
            "currently_runnable": layouts["exists"],
            "inputs": [
                "Layout manifest or future measured segmentation output",
                "Original rendered page images",
            ],
            "outputs": [
                "Crop manifest",
                "Saved region image files suitable for targeted rereads",
            ],
            "artifact_paths": unique_sorted([CROP_MANIFEST_PATH.as_posix()]),
            "evidence": {
                "crop_manifest_present": crops["exists"],
                "crop_count": crops["crop_count"],
                "page_count": crops["page_count"],
            },
            "known_strengths": [
                "Provides a path to recover small inserts, footers, sidebars, and hard-to-read corners.",
                "Allows multiple targeted rereads instead of one lossy page pass.",
                "Creates a bridge from layout theory to measurable extraction improvements.",
            ],
            "known_weaknesses": [
                (
                    "Current crops are still driven by provisional layout guesses rather than measured segmentation."
                    if crops["exists"]
                    else "Not implemented yet in the current corpus build."
                ),
                "Quality depends heavily on the upstream layout manifest.",
                "Can multiply cost and complexity quickly if region counts explode.",
            ],
            "open_questions": [
                "How many region crops per page are enough before costs stop paying off?",
                "Should crop generation be heuristic, model-assisted, or both?",
            ],
        },
        {
            "approach_id": "region_level_transcription",
            "label": "Region-level transcription",
            "status": detect_status(region_transcriptions["exists"], region_transcriptions["page_count"]),
            "currently_runnable": crops["exists"] or layouts["exists"],
            "inputs": [
                "Region crops or layout-directed page subareas",
                "Vision model prompts specialized by region type",
            ],
            "outputs": [
                "Region transcription manifest",
                "Structured local evidence about what was found where on a page",
            ],
            "artifact_paths": unique_sorted([REGION_TRANSCRIPTION_MANIFEST_PATH.as_posix()]),
            "evidence": {
                "region_transcription_manifest_present": region_transcriptions["exists"],
                "region_count": region_transcriptions["region_count"],
                "page_count": region_transcriptions["page_count"],
            },
            "known_strengths": [
                "Best candidate for boundary-aware recovery of complex pages.",
                "Supports certifying what page components are actually present and indexed.",
                "Should make dashboard trust surfaces much more meaningful.",
            ],
            "known_weaknesses": [
                (
                    "Current evidence comes from a partial or sample region-transcription pass rather than the whole corpus."
                    if region_transcriptions["exists"]
                    else "Not implemented yet in the current corpus build."
                ),
                "Needs careful prompt design and normalization to avoid inconsistent region outputs.",
                "Will require explicit evaluation to prove it is better rather than just more elaborate.",
            ],
            "open_questions": [
                "Which region types merit their own prompts and schemas?",
                "How should region evidence roll back up into page-level and item-level retrieval?",
                "What new failure modes appear when multiple partial reads disagree?",
            ],
        },
    ]


def build_meta_assessment(approaches: list[dict[str, Any]], transcriptions: dict[str, Any]) -> dict[str, Any]:
    active_or_provisional = [a for a in approaches if a["status"] in {"active", "provisional"}]
    implemented = [a for a in approaches if a["status"] != "not_started"]
    page_level_ready = any(a["approach_id"] == "whole_page_vision" and a["status"] != "not_started" for a in approaches)
    retrieval_ready = any(a["approach_id"] == "blended_retrieval" and a["status"] != "not_started" for a in approaches)
    layout_ready = any(a["approach_id"] == "provisional_layout_manifest" and a["status"] != "not_started" for a in approaches)

    interesting_signals: list[str] = []
    if page_level_ready and transcriptions["transcribed_page_count"] > 0:
        interesting_signals.append(
            "Whole-page vision is already yielding mixed text-plus-sketch readings across a nontrivial corpus slice."
        )
    if retrieval_ready:
        interesting_signals.append(
            "The project has moved beyond OCR replacement into multi-lane semantic retrieval over sketches, entities, summaries, and text."
        )
    if layout_ready:
        interesting_signals.append(
            "The rebuild is explicitly confronting layout uncertainty instead of hiding it behind a single-pass search demo."
        )

    unresolved_questions = [
        "Can region-aware rereads materially outperform page-monolithic extraction on marginalia, footers, and insets?",
        "Which processing lane produces the most trustworthy retrieval wins for real research queries?",
        "How should the project certify indexed features so a user can trust what a result actually represents?",
    ]

    if len(interesting_signals) >= 3:
        verdict = "yes_but_incomplete"
        verdict_text = (
            "Yes, this is already interesting: it demonstrates a credible path from mixed-layout broadsheets "
            "to local semantic retrieval, but the strongest unanswered question is still layout-aware certification."
        )
    elif interesting_signals:
        verdict = "promising_not_yet_proven"
        verdict_text = (
            "There is real signal here, but not yet enough layered evidence to claim the approach is genuinely novel or robust."
        )
    else:
        verdict = "not_yet"
        verdict_text = (
            "Not yet. The corpus has not accumulated enough working approaches to answer the meta-question convincingly."
        )

    return {
        "verdict": verdict,
        "verdict_text": verdict_text,
        "implemented_approach_count": len(implemented),
        "active_or_provisional_approach_count": len(active_or_provisional),
        "interesting_signals": interesting_signals,
        "unresolved_questions": unresolved_questions,
    }


def build_report() -> dict[str, Any]:
    transcriptions = count_transcription_artifacts()
    features = summarize_feature_manifest()
    layouts = summarize_layout_manifest()
    crops = summarize_crop_manifest()
    region_transcriptions = summarize_region_transcription_manifest()
    index_state = summarize_index_state()

    approaches = build_approach_matrix(
        transcriptions=transcriptions,
        features=features,
        layouts=layouts,
        crops=crops,
        region_transcriptions=region_transcriptions,
        index_state=index_state,
    )
    meta_assessment = build_meta_assessment(approaches, transcriptions)

    return {
        "schema_version": "2026-04-19-processing-matrix-v1",
        "generated_artifacts": {
            "json": PROCESSING_MATRIX_JSON_PATH.as_posix(),
            "markdown": PROCESSING_MATRIX_MD_PATH.as_posix(),
        },
        "artifact_state": {
            "transcriptions": transcriptions,
            "feature_manifest": features,
            "layout_manifest": layouts,
            "crop_manifest": crops,
            "region_transcription_manifest": region_transcriptions,
            "index_state": index_state,
        },
        "meta_question": "Did we do anything interesting here or not?",
        "meta_assessment": meta_assessment,
        "approaches": approaches,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Topolski Processing Approaches Matrix",
        "",
        f"Meta-question: {report['meta_question']}",
        "",
        f"Verdict: **{report['meta_assessment']['verdict']}**",
        "",
        report["meta_assessment"]["verdict_text"],
        "",
        "## Interesting Signals",
        "",
    ]

    signals = report["meta_assessment"]["interesting_signals"] or ["None yet."]
    for signal in signals:
        lines.append(f"- {signal}")

    lines.extend(["", "## Unresolved Questions", ""])
    for question in report["meta_assessment"]["unresolved_questions"]:
        lines.append(f"- {question}")

    artifact_state = report["artifact_state"]
    lines.extend(
        [
            "",
            "## Current Artifact State",
            "",
            f"- Staged items: {artifact_state['transcriptions']['staged_item_count']}",
            f"- Staged pages: {artifact_state['transcriptions']['staged_page_count']}",
            f"- Transcribed items: {artifact_state['transcriptions']['transcribed_item_count']}",
            f"- Transcribed pages: {artifact_state['transcriptions']['transcribed_page_count']}",
            f"- Feature manifest present: {artifact_state['feature_manifest']['exists']}",
            f"- Layout manifest present: {artifact_state['layout_manifest']['exists']}",
            f"- Crop manifest present: {artifact_state['crop_manifest']['exists']}",
            f"- Region transcription manifest present: {artifact_state['region_transcription_manifest']['exists']}",
            f"- Local index present: {artifact_state['index_state']['exists']}",
            "",
            "## Approach Matrix",
            "",
        ]
    )

    for approach in report["approaches"]:
        lines.extend(
            [
                f"### {approach['label']}",
                "",
                f"- Status: `{approach['status']}`",
                f"- Currently runnable: `{approach['currently_runnable']}`",
                f"- Inputs: {', '.join(approach['inputs'])}",
                f"- Outputs: {', '.join(approach['outputs'])}",
                f"- Artifact paths: {', '.join(approach['artifact_paths']) or 'None'}",
                "- Known strengths:",
            ]
        )
        for entry in approach["known_strengths"]:
            lines.append(f"  - {entry}")
        lines.append("- Known weaknesses:")
        for entry in approach["known_weaknesses"]:
            lines.append(f"  - {entry}")
        lines.append("- Open questions:")
        for entry in approach["open_questions"]:
            lines.append(f"  - {entry}")
        lines.append("- Evidence:")
        for key, value in approach["evidence"].items():
            lines.append(f"  - {key}: {value}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    report = build_report()
    write_json(PROCESSING_MATRIX_JSON_PATH, report)
    write_text(PROCESSING_MATRIX_MD_PATH, render_markdown(report))
    print(f"Wrote processing matrix JSON to {PROCESSING_MATRIX_JSON_PATH}")
    print(f"Wrote processing matrix Markdown to {PROCESSING_MATRIX_MD_PATH}")
    print(f"Verdict: {report['meta_assessment']['verdict']}")


if __name__ == "__main__":
    main()
