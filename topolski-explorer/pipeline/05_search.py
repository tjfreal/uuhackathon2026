"""
05_search.py — Topolski Explorer Search App

Local-first Flask app:
  1. Embed query with OpenAI text embeddings
  2. Query local ChromaDB
  3. Aggregate chunk hits into page-level results
  4. Optionally rerank with an API model if enabled
  5. Render local search results against saved files

Core behavior:
  - Search remains local against Chroma and saved local metadata
  - Partial corpora are fine; the app reflects current indexed state
  - Reranking is optional and degrades cleanly to local-only ordering
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from urllib.parse import quote

import chromadb
from dotenv import load_dotenv
from flask import Flask, abort, render_template, request, send_file
from openai import OpenAI
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
STAGED_DATA_DIR = Path(os.getenv("STAGED_DATA_DIR", "data/staged")).resolve()
CHROMA_DB_PATH = Path(os.getenv("CHROMA_DB_PATH", "data/chroma"))
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "topolski_explorer")
FEATURE_MANIFEST_PATH = Path(os.getenv("FEATURE_MANIFEST_PATH", "data/feature_manifest.json"))
LAYOUT_MANIFEST_PATH = Path(os.getenv("LAYOUT_MANIFEST_PATH", "data/layout_manifest.json"))
PROCESSING_MATRIX_PATH = Path(os.getenv("PROCESSING_MATRIX_PATH", "data/processing_matrix.json"))
REGION_CROP_MANIFEST_PATH = Path(os.getenv("REGION_CROP_MANIFEST_PATH", "data/region_crop_manifest.json"))
REGION_TRANSCRIPTION_MANIFEST_PATH = Path(
    os.getenv("REGION_TRANSCRIPTION_MANIFEST_PATH", "data/region_transcription_manifest_sample.json")
)
EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
RERANK_MODEL = os.getenv("OPENAI_RERANK_MODEL", "gpt-4o-mini")
ENABLE_RERANK = os.getenv("ENABLE_RERANK", "false").lower() == "true"
FLASK_PORT = int(os.getenv("FLASK_PORT", "5050"))
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"

RETRIEVAL_K = int(os.getenv("RETRIEVAL_K", "30"))
PAGE_CANDIDATE_LIMIT = int(os.getenv("PAGE_CANDIDATE_LIMIT", "12"))
RESULTS_TO_SHOW = int(os.getenv("RESULTS_TO_SHOW", "8"))

CHUNK_WEIGHTS = {
    "summary": 1.0,
    "blended": 0.96,
    "entities": 0.9,
    "text": 0.84,
    "sketch": 0.88,
}

oai = OpenAI()
chroma = chromadb.PersistentClient(path=str(CHROMA_DB_PATH))
collection = chroma.get_or_create_collection(
    name=CHROMA_COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"},
)

app = Flask(__name__, template_folder=str(BASE_DIR / "templates"))


def normalize_distance(distance: float | None) -> float:
    if distance is None:
        return 1.0
    try:
        return max(0.0, min(float(distance), 2.0))
    except (TypeError, ValueError):
        return 1.0


def compute_similarity(distance: float | None, chunk_type: str) -> float:
    base = 1.0 - (normalize_distance(distance) / 2.0)
    return round(base * CHUNK_WEIGHTS.get(chunk_type, 0.82), 4)


def shorten_text(text: str, limit: int = 420) -> str:
    cleaned = " ".join((text or "").split())
    if len(cleaned) <= limit:
        return cleaned
    return f"{cleaned[:limit - 1].rstrip()}…"


def image_url_for(path_value: str) -> str:
    if not path_value:
        return ""
    return f"/image?path={quote(path_value)}"


def safe_display_url(url: str) -> str:
    return url if url else "#"


def load_json_if_exists(path: Path) -> dict | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def summarize_region_manifest(manifest: dict | None) -> dict:
    if not manifest:
        return {"exists": False, "item_count": 0, "page_count": 0, "region_count": 0, "model": ""}

    items = manifest.get("items", {})
    item_count = 0
    page_count = 0
    region_count = 0
    for item in items.values():
        pages = item.get("pages", {})
        if pages:
            item_count += 1
        page_count += len(pages)
        for page in pages.values():
            region_count += len(page.get("regions", []))

    return {
        "exists": True,
        "item_count": item_count,
        "page_count": page_count,
        "region_count": region_count,
        "model": manifest.get("model", ""),
    }


@retry(
    retry=retry_if_exception_type(Exception),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=10),
    reraise=True,
)
def embed_query(query: str) -> list[float]:
    response = oai.embeddings.create(model=EMBED_MODEL, input=[query])
    return response.data[0].embedding


def retrieve(query_embedding: list[float]) -> list[dict]:
    if collection.count() == 0:
        return []

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=RETRIEVAL_K,
        include=["documents", "metadatas", "distances"],
    )

    page_hits: dict[tuple[str, int], dict] = {}
    ids = results.get("ids", [[]])[0]
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for chunk_id, document, metadata, distance in zip(ids, documents, metadatas, distances):
        if not metadata:
            continue

        item_id = metadata.get("item_id")
        page_number = metadata.get("page_number")
        if item_id is None or page_number is None:
            continue

        page_key = (str(item_id), int(page_number))
        similarity = compute_similarity(distance, metadata.get("chunk_type", ""))
        source_text = metadata.get("source_text") or document or ""

        hit = page_hits.setdefault(
            page_key,
            {
                "chunk_id": chunk_id,
                "item_id": str(item_id),
                "page_number": int(page_number),
                "item_title": metadata.get("item_title", ""),
                "item_date": metadata.get("item_date", ""),
                "collection_url": metadata.get("collection_url", ""),
                "image_path": metadata.get("image_path", ""),
                "best_chunk_type": metadata.get("chunk_type", ""),
                "best_distance": normalize_distance(distance),
                "score": similarity,
                "matched_chunks": [],
                "source_text": "",
            },
        )

        hit["matched_chunks"].append(
            {
                "chunk_id": chunk_id,
                "chunk_type": metadata.get("chunk_type", ""),
                "distance": normalize_distance(distance),
                "score": similarity,
                "source_text": shorten_text(source_text, limit=260),
            }
        )
        hit["matched_chunks"].sort(key=lambda chunk: chunk["score"], reverse=True)

        if similarity > hit["score"]:
            hit["chunk_id"] = chunk_id
            hit["best_chunk_type"] = metadata.get("chunk_type", "")
            hit["best_distance"] = normalize_distance(distance)
            hit["score"] = similarity

        top_chunks = hit["matched_chunks"][:3]
        hit["matched_chunk_types"] = [chunk["chunk_type"] for chunk in top_chunks]
        hit["source_text"] = "\n".join(chunk["source_text"] for chunk in top_chunks if chunk["source_text"])
        hit["display_image_url"] = image_url_for(hit["image_path"])
        hit["collection_url"] = safe_display_url(hit["collection_url"])

    ranked_pages = sorted(
        page_hits.values(),
        key=lambda page: (
            page["score"],
            -page["best_distance"],
            len(page.get("matched_chunks", [])),
        ),
        reverse=True,
    )
    return ranked_pages[:PAGE_CANDIDATE_LIMIT]


def rerank(query: str, candidates: list[dict]) -> list[dict]:
    if not candidates:
        return []

    if not ENABLE_RERANK:
        for candidate in candidates:
            candidate["relevance_score"] = round(candidate["score"] * 10, 1)
            candidate["explanation"] = "Ordered by local embedding similarity across saved page signals."
        return candidates[:RESULTS_TO_SHOW]

    candidate_lines = []
    for index, candidate in enumerate(candidates):
        candidate_lines.append(
            "\n".join(
                [
                    f"Result {index}",
                    f"Item: {candidate['item_title'] or candidate['item_id']}",
                    f"Date: {candidate['item_date']}",
                    f"Page: {candidate['page_number']}",
                    f"Matched signals: {', '.join(candidate.get('matched_chunk_types', []))}",
                    f"Evidence: {candidate.get('source_text', '')[:900]}",
                ]
            )
        )

    prompt = (
        "You are reranking archive search results.\n"
        f"Query: {query}\n\n"
        "Evaluate the candidate pages below. Return JSON with a single key `results` whose value is a list.\n"
        "Each list item must contain `result_index`, `relevance_score` (0-10), and `explanation`.\n"
        "Prefer concise, specific explanations grounded in the retrieved evidence.\n\n"
        + "\n\n".join(candidate_lines)
    )

    try:
        response = oai.chat.completions.create(
            model=RERANK_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": "Return valid JSON only. Keep explanations to one sentence each.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=1200,
        )
        parsed = json.loads(response.choices[0].message.content)
        rankings = parsed.get("results", [])
        scored = []
        for rank in rankings:
            idx = rank.get("result_index", -1)
            if not isinstance(idx, int) or not (0 <= idx < len(candidates)):
                continue
            candidate = candidates[idx].copy()
            candidate["relevance_score"] = rank.get("relevance_score", round(candidate["score"] * 10, 1))
            candidate["explanation"] = rank.get(
                "explanation",
                "Ordered by local embedding similarity across saved page signals.",
            )
            scored.append(candidate)
        if not scored:
            raise ValueError("No valid rerank results returned.")
        scored.sort(
            key=lambda candidate: (
                float(candidate.get("relevance_score", 0)),
                float(candidate.get("score", 0)),
            ),
            reverse=True,
        )
        return scored[:RESULTS_TO_SHOW]
    except Exception as exc:
        log.warning("Reranking failed; falling back to local ordering: %s", exc)
        for candidate in candidates:
            candidate["relevance_score"] = round(candidate["score"] * 10, 1)
            candidate["explanation"] = "Reranking unavailable; ordered by local embedding similarity."
        return candidates[:RESULTS_TO_SHOW]


def corpus_stats() -> dict:
    stats = {"items": 0, "pages": 0, "chunks": collection.count()}
    if stats["chunks"] == 0:
        return stats

    snapshot = collection.get(include=["metadatas"])
    metadatas = snapshot.get("metadatas", [])
    page_keys = set()
    item_ids = set()
    for metadata in metadatas:
        if not metadata:
            continue
        item_id = metadata.get("item_id")
        page_number = metadata.get("page_number")
        if item_id is not None:
            item_ids.add(str(item_id))
        if item_id is not None and page_number is not None:
            page_keys.add((str(item_id), int(page_number)))
    stats["items"] = len(item_ids)
    stats["pages"] = len(page_keys)
    return stats


def build_dashboard_data() -> dict:
    staged_items: list[dict] = []
    staged_page_count = 0
    transcribed_items = 0
    transcribed_pages = 0

    feature_manifest = load_json_if_exists(FEATURE_MANIFEST_PATH)
    layout_manifest = load_json_if_exists(LAYOUT_MANIFEST_PATH)
    processing_matrix = load_json_if_exists(PROCESSING_MATRIX_PATH)
    region_crop_manifest = load_json_if_exists(REGION_CROP_MANIFEST_PATH)
    region_transcription_manifest = load_json_if_exists(REGION_TRANSCRIPTION_MANIFEST_PATH)
    indexed_stats = corpus_stats()

    item_dirs = sorted(path for path in STAGED_DATA_DIR.iterdir() if path.is_dir()) if STAGED_DATA_DIR.exists() else []
    for item_dir in item_dirs:
        item_id = item_dir.name
        metadata_path = STAGED_DATA_DIR / f"{item_id}.json"
        transcription_path = item_dir / "transcription.json"

        title = item_id
        page_count = 0
        if metadata_path.exists():
            try:
                metadata = load_json_if_exists(metadata_path) or {}
                title = metadata.get("metadata", {}).get("Title") or metadata.get("Title") or item_id
                page_count = len(metadata.get("page_images", [])) if isinstance(metadata.get("page_images"), list) else 0
            except Exception:
                pass

        transcribed_page_count = 0
        if transcription_path.exists():
            transcribed_items += 1
            try:
                transcription = load_json_if_exists(transcription_path) or {}
                transcribed_page_count = len(transcription.get("pages", []))
            except Exception:
                transcribed_page_count = 0
            transcribed_pages += transcribed_page_count
        staged_page_count += page_count

        staged_items.append(
            {
                "item_id": item_id,
                "title": title,
                "page_count": page_count,
                "transcribed_page_count": transcribed_page_count,
            }
        )

    feature_items = (feature_manifest or {}).get("items", {})
    item_rows = []
    sketch_heavy_items = []
    handwriting_heavy_items = []
    weak_items = []
    likely_index_pages = []
    feature_counts = ((feature_manifest or {}).get("corpus_summary", {})).get("feature_counts", {})

    for staged_item in staged_items:
        item_id = staged_item["item_id"]
        feature_item = feature_items.get(item_id, {})
        feature_item_pages = feature_item.get("pages", [])
        feature_item_counts = feature_item.get("feature_counts", {})
        indexed_page_count = feature_item.get("indexed_page_count", 0)
        weak_pages = feature_item.get("weakly_characterized_pages", [])
        sketch_pages = int(feature_item_counts.get("has_sketches", 0))
        handwriting_pages = int(feature_item_counts.get("has_handwritten_text", 0))
        index_pages = [page["page_number"] for page in feature_item_pages if page.get("is_index_like")]

        row = {
            **staged_item,
            "indexed_page_count": indexed_page_count,
            "weak_page_count": len(weak_pages),
            "sketch_page_count": sketch_pages,
            "handwriting_page_count": handwriting_pages,
            "index_page_count": len(index_pages),
        }
        item_rows.append(row)

        if sketch_pages:
            sketch_heavy_items.append(row)
        if handwriting_pages:
            handwriting_heavy_items.append(row)
        if weak_pages:
            weak_items.append({**row, "weak_pages": weak_pages})
        for page_number in index_pages:
            likely_index_pages.append(
                {
                    "item_id": item_id,
                    "title": staged_item["title"],
                    "page_number": page_number,
                }
            )

    sketch_heavy_items.sort(key=lambda item: (item["sketch_page_count"], item["page_count"]), reverse=True)
    handwriting_heavy_items.sort(key=lambda item: (item["handwriting_page_count"], item["page_count"]), reverse=True)
    weak_items.sort(key=lambda item: (item["weak_page_count"], item["page_count"]), reverse=True)
    likely_index_pages.sort(key=lambda item: (item["item_id"], item["page_number"]))
    item_rows.sort(key=lambda item: item["item_id"])

    matrix_state = (processing_matrix or {}).get("artifact_state", {})
    matrix_assessment = (processing_matrix or {}).get("meta_assessment", {})
    approaches = (processing_matrix or {}).get("approaches", [])
    active_approaches = [
        {
            "label": approach.get("label", approach.get("approach_id", "unknown")),
            "status": approach.get("status", "unknown"),
        }
        for approach in approaches
        if approach.get("status") in {"active", "provisional"}
    ]
    region_summary = summarize_region_manifest(region_transcription_manifest)
    crop_state = matrix_state.get("crop_manifest", {})
    if not crop_state.get("exists") and region_crop_manifest:
        crop_items = region_crop_manifest.get("items", {})
        crop_state = {
            "exists": True,
            "item_count": len(crop_items),
            "page_count": sum(len((item or {}).get("pages", {})) for item in crop_items.values()),
            "crop_count": sum(
                len((page or {}).get("regions", []))
                for item in crop_items.values()
                for page in ((item or {}).get("pages", {})).values()
            ),
        }
    layout_state = matrix_state.get("layout_manifest", {})
    unresolved_questions = matrix_assessment.get("unresolved_questions", [])

    return {
        "summary": {
            "staged_items": len(staged_items),
            "staged_pages": staged_page_count,
            "transcribed_items": transcribed_items,
            "transcribed_pages": transcribed_pages,
            "indexed_items": indexed_stats["items"],
            "indexed_pages": indexed_stats["pages"],
            "indexed_chunks": indexed_stats["chunks"],
        },
        "feature_manifest_available": feature_manifest is not None,
        "layout_manifest_available": layout_manifest is not None,
        "layout_item_count": ((layout_manifest or {}).get("corpus_summary", {})).get("item_count", 0),
        "layout_page_count": ((layout_manifest or {}).get("corpus_summary", {})).get("page_count", 0),
        "feature_counts": feature_counts,
        "processing_matrix": {
            "available": processing_matrix is not None,
            "verdict": matrix_assessment.get("verdict", "not_built"),
            "verdict_text": matrix_assessment.get(
                "verdict_text",
                "Processing matrix not built yet.",
            ),
            "active_approaches": active_approaches[:6],
            "active_approach_count": matrix_assessment.get("active_or_provisional_approach_count", len(active_approaches)),
            "implemented_approach_count": matrix_assessment.get("implemented_approach_count", len(approaches)),
            "interesting_signals": matrix_assessment.get("interesting_signals", [])[:3],
            "unresolved_questions": unresolved_questions[:3],
        },
        "region_experiment": {
            "crop_manifest_available": bool(crop_state.get("exists")),
            "crop_count": int(crop_state.get("crop_count", 0) or 0),
            "crop_item_count": int(crop_state.get("item_count", 0) or 0),
            "crop_page_count": int(crop_state.get("page_count", 0) or 0),
            "sample_available": region_summary["exists"],
            "sample_item_count": region_summary["item_count"],
            "sample_page_count": region_summary["page_count"],
            "sample_region_count": region_summary["region_count"],
            "sample_model": region_summary["model"],
        },
        "layout_caution": {
            "provisional": bool(layout_state.get("provisional", True)),
            "message": (
                "Layout bounds are provisional right now. Region crops are useful comparison artifacts, "
                "not measured geometry you should treat as archival fact."
            ),
        },
        "likely_index_pages": likely_index_pages[:12],
        "sketch_heavy_items": sketch_heavy_items[:10],
        "handwriting_heavy_items": handwriting_heavy_items[:10],
        "weak_items": weak_items[:10],
        "item_rows": item_rows[:25],
    }


def run_search(query: str) -> list[dict]:
    log.info("Query: %r", query)
    query_embedding = embed_query(query)
    candidates = retrieve(query_embedding)
    log.info("Retrieved %s page candidates.", len(candidates))
    results = rerank(query, candidates)
    log.info("Returning %s results.", len(results))
    return results


@app.route("/")
def index():
    return render_template(
        "index.html",
        view="search",
        results=None,
        query="",
        error=None,
        stats=corpus_stats(),
        rerank_enabled=ENABLE_RERANK,
        dashboard=None,
    )


@app.route("/search", methods=["POST"])
def search():
    query = request.form.get("query", "").strip()
    if not query:
        return render_template(
            "index.html",
            view="search",
            results=[],
            query="",
            error="Please enter a query.",
            stats=corpus_stats(),
            rerank_enabled=ENABLE_RERANK,
            dashboard=None,
        )

    try:
        results = run_search(query)
        error = None
        if collection.count() == 0:
            error = "The local index is empty. Run 04_embed_index.py after transcription outputs are available."
    except Exception as exc:
        log.error("Search error: %s", exc)
        results = []
        error = "Search failed. Check logs."

    return render_template(
        "index.html",
        view="search",
        results=results,
        query=query,
        error=error,
        stats=corpus_stats(),
        rerank_enabled=ENABLE_RERANK,
        dashboard=None,
    )


@app.route("/dashboard")
def dashboard():
    return render_template(
        "index.html",
        view="dashboard",
        results=None,
        query="",
        error=None,
        stats=corpus_stats(),
        rerank_enabled=ENABLE_RERANK,
        dashboard=build_dashboard_data(),
    )


@app.route("/image")
def serve_image():
    path_value = request.args.get("path", "").strip()
    if not path_value:
        abort(404)

    requested = Path(path_value).expanduser()
    if not requested.is_absolute():
        requested = (STAGED_DATA_DIR / requested).resolve()
    else:
        requested = requested.resolve()

    allowed_roots = {STAGED_DATA_DIR}
    for item_dir in STAGED_DATA_DIR.iterdir() if STAGED_DATA_DIR.exists() else []:
        if item_dir.is_dir():
            allowed_roots.add(item_dir.resolve())

    if not any(str(requested).startswith(str(root) + os.sep) or requested == root for root in allowed_roots):
        abort(403)
    if not requested.exists() or not requested.is_file():
        abort(404)
    return send_file(requested)


if __name__ == "__main__":
    log.info("Starting Topolski Explorer on port %s", FLASK_PORT)
    log.info("ChromaDB: %s (%s chunks indexed)", CHROMA_DB_PATH, collection.count())
    app.run(host="0.0.0.0", port=FLASK_PORT, debug=FLASK_DEBUG)
