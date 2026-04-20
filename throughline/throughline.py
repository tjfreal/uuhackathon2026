#!/usr/bin/env python3

import argparse
import hashlib
import json
import math
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence


MODEL_NAME = "nomic-ai/nomic-embed-text-v1.5"
EMBED_DIM = 768
BATCH_SIZE = 32
TEXT_EXTENSIONS = {
    ".md",
    ".markdown",
    ".txt",
    ".rst",
    ".text",
    ".org",
}
SPAN_CONFIGS = {
    "span_25": {"word_window": 19, "word_step": 10},
    "span_75": {"word_window": 58, "word_step": 29},
    "span_200": {"word_window": 154, "word_step": 77},
}
SCRIPT_DIR = Path(__file__).resolve().parent
INDICES_DIR = SCRIPT_DIR / "indices"
STATE_PATH = SCRIPT_DIR / ".throughline_state.json"


@dataclass
class SourceFile:
    path: Path
    rel_path: str
    mtime: float


def load_model() -> Any:
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise SystemExit(
            "Missing runtime dependency `sentence-transformers`. Activate the expected venv before running."
        ) from exc

    try:
        return SentenceTransformer(MODEL_NAME, trust_remote_code=True)
    except Exception as exc:
        raise SystemExit(
            "Failed to load embedding model "
            f"`{MODEL_NAME}`. If you are offline, make sure it has already been downloaded into the active environment."
        ) from exc


def embed_texts(model: Any, texts: Sequence[str], prefix: str):
    try:
        import numpy as np
    except ImportError as exc:
        raise SystemExit("Missing runtime dependency `numpy`. Activate the expected venv before running.") from exc

    if not texts:
        return np.zeros((0, EMBED_DIM), dtype=np.float32)
    prefixed = [f"{prefix}{text}" for text in texts]
    vectors = model.encode(
        prefixed,
        batch_size=BATCH_SIZE,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )
    return np.asarray(vectors, dtype=np.float32)


def load_state() -> Dict[str, object]:
    if not STATE_PATH.exists():
        return {}
    try:
        return json.loads(STATE_PATH.read_text())
    except json.JSONDecodeError:
        return {}


def save_state(state: Dict[str, object]) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2) + "\n")


def prompt_for_path() -> Path:
    raw = input("Directory to index: ").strip()
    if not raw:
        raise SystemExit("No directory supplied.")
    return Path(raw).expanduser().resolve()


def prompt_for_query() -> str:
    query = input("Query: ").strip()
    if not query:
        raise SystemExit("No query supplied.")
    return query


def slugify_path(path: Path) -> str:
    normalized = str(path.resolve())
    digest = hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:10]
    stem = re.sub(r"[^a-zA-Z0-9]+", "-", path.name.lower()).strip("-") or "corpus"
    return f"{stem}-{digest}"


def discover_text_files(root: Path) -> List[SourceFile]:
    files: List[SourceFile] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        try:
            rel_path = str(path.relative_to(root))
            mtime = path.stat().st_mtime
        except OSError:
            continue
        files.append(SourceFile(path=path, rel_path=rel_path, mtime=mtime))
    return files


def read_text_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def generate_chunks(text: str, rel_path: str, span_name: str, word_window: int, word_step: int) -> Iterable[Dict[str, object]]:
    words = text.split()
    if not words:
        return
    for start in range(0, len(words), word_step):
        end = min(start + word_window, len(words))
        chunk_text = " ".join(words[start:end]).strip()
        if len(chunk_text) < 30:
            continue
        yield {
            "file": rel_path,
            "span": span_name,
            "word_start": start,
            "word_end": end,
            "text": chunk_text,
        }
        if end >= len(words):
            break


def corpus_needs_rebuild(span_dir: Path, files: Sequence[SourceFile]) -> bool:
    meta_path = span_dir / "meta.json"
    chunks_path = span_dir / "chunks.jsonl"
    if not meta_path.exists() or not chunks_path.exists():
        return True
    try:
        meta = json.loads(meta_path.read_text())
    except json.JSONDecodeError:
        return True
    last_built = float(meta.get("last_built", 0))
    prior_count = int(meta.get("source_file_count", -1))
    if prior_count != len(files):
        return True
    return any(source_file.mtime > last_built for source_file in files)


def build_index(root: Path, force: bool = False) -> Path:
    root = root.expanduser().resolve()
    if not root.is_dir():
        raise SystemExit(f"Not a directory: {root}")

    source_files = discover_text_files(root)
    if not source_files:
        raise SystemExit(f"No supported text files found in {root}")

    index_root = INDICES_DIR / slugify_path(root)
    index_root.mkdir(parents=True, exist_ok=True)

    print(f"Index root: {index_root}")
    print(f"Corpus root: {root}")
    print(f"Files found: {len(source_files)}")

    model: Optional[Any] = None
    built_any = False

    for span_name, config in SPAN_CONFIGS.items():
        span_dir = index_root / span_name
        span_dir.mkdir(parents=True, exist_ok=True)
        if not force and not corpus_needs_rebuild(span_dir, source_files):
            print(f"[skip] {span_name}: unchanged since last build")
            continue

        if model is None:
            print(f"Loading embedding model: {MODEL_NAME}")
            model = load_model()

        word_window = config["word_window"]
        word_step = config["word_step"]
        print(f"[build] {span_name}: window={word_window} step={word_step}")

        raw_chunks: List[Dict[str, object]] = []
        for index, source_file in enumerate(source_files, start=1):
            text = read_text_file(source_file.path)
            raw_chunks.extend(
                generate_chunks(
                    text=text,
                    rel_path=source_file.rel_path,
                    span_name=span_name,
                    word_window=word_window,
                    word_step=word_step,
                )
            )
            if index % 100 == 0 or index == len(source_files):
                print(f"  scanned {index}/{len(source_files)} files", end="\r", flush=True)
        print(" " * 80, end="\r")

        if not raw_chunks:
            print(f"  no chunks produced for {span_name}")
            continue

        texts = [chunk["text"] for chunk in raw_chunks]
        vectors = embed_texts(model, texts, prefix="search_document: ")
        chunks_path = span_dir / "chunks.jsonl"
        with chunks_path.open("w", encoding="utf-8") as handle:
            for chunk, vector in zip(raw_chunks, vectors):
                row = dict(chunk)
                row["vector"] = vector.tolist()
                handle.write(json.dumps(row) + "\n")

        now = time.time()
        meta = {
            "model": MODEL_NAME,
            "span": span_name,
            "word_window": word_window,
            "word_step": word_step,
            "embed_dim": EMBED_DIM,
            "last_built": now,
            "chunk_count": len(raw_chunks),
            "source_file_count": len(source_files),
            "corpus_root": str(root),
        }
        (span_dir / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")
        built_any = True
        print(f"  wrote {len(raw_chunks)} chunks")

    state = load_state()
    state["active_index_dir"] = str(index_root)
    state["active_corpus_root"] = str(root)
    state["updated_at"] = time.time()
    save_state(state)

    if built_any:
        print("Index build complete.")
    else:
        print("Index is already current.")
    return index_root


def load_span_chunks(span_dir: Path) -> List[Dict[str, object]]:
    chunks_path = span_dir / "chunks.jsonl"
    if not chunks_path.exists():
        return []
    rows: List[Dict[str, object]] = []
    with chunks_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            rows.append(json.loads(line))
    return rows


def resolve_index_dir(explicit: Optional[str]) -> Path:
    if explicit:
        path = Path(explicit).expanduser().resolve()
    else:
        state = load_state()
        raw = state.get("active_index_dir")
        if not raw:
            raise SystemExit("No active index found. Run `throughline.py index` first.")
        path = Path(str(raw)).expanduser().resolve()
    if not path.is_dir():
        raise SystemExit(f"Index directory does not exist: {path}")
    return path


def preview_text(text: str, limit: int = 120) -> str:
    clean = re.sub(r"\s+", " ", text).strip()
    if len(clean) <= limit:
        return clean
    return clean[: limit - 3].rstrip() + "..."


def shorten_path(path: str, limit: int = 52) -> str:
    if len(path) <= limit:
        return path
    return "..." + path[-(limit - 3) :]


def query_all_spans(query_text: str, index_dir: Path, n_per_span: int = 8) -> Dict[str, object]:
    model = load_model()
    query_vector = embed_texts(model, [query_text], prefix="search_query: ")[0]

    spans: Dict[str, List[Dict[str, object]]] = {}
    appearance_map: Dict[str, Dict[str, object]] = {}

    for span_name in SPAN_CONFIGS:
        span_dir = index_dir / span_name
        rows = load_span_chunks(span_dir)
        if not rows:
            spans[span_name] = []
            continue

        import numpy as np

        vectors = np.asarray([row["vector"] for row in rows], dtype=np.float32)
        scores = np.dot(vectors, query_vector)

        best_by_file: Dict[str, Dict[str, object]] = {}
        for row, score in zip(rows, scores):
            file_key = row["file"]
            candidate = {
                "file": file_key,
                "score": float(score),
                "text": row["text"],
                "word_start": int(row["word_start"]),
                "word_end": int(row["word_end"]),
                "span": span_name,
            }
            current = best_by_file.get(file_key)
            if current is None or candidate["score"] > current["score"]:
                best_by_file[file_key] = candidate

        ranked = sorted(best_by_file.values(), key=lambda item: item["score"], reverse=True)[:n_per_span]
        spans[span_name] = ranked

        for item in ranked:
            entry = appearance_map.setdefault(
                item["file"],
                {"file": item["file"], "span_count": 0, "best_score": -math.inf, "spans": []},
            )
            entry["span_count"] += 1
            entry["best_score"] = max(entry["best_score"], item["score"])
            entry["spans"].append(span_name)

    throughlines = [
        {
            "file": file_info["file"],
            "span_count": file_info["span_count"],
            "best_score": file_info["best_score"],
            "spans": sorted(file_info["spans"]),
        }
        for file_info in appearance_map.values()
        if file_info["span_count"] >= 2
    ]
    throughlines.sort(key=lambda item: (-item["span_count"], -item["best_score"], item["file"]))

    throughline_badges = {
        item["file"]: f"{item['span_count']}/3 spans"
        for item in throughlines
    }

    return {
        "query": query_text,
        "index_dir": str(index_dir),
        "spans": spans,
        "throughlines": throughlines,
        "throughline_badges": throughline_badges,
    }


def print_results(results: Dict[str, object], n_per_span: int) -> None:
    print()
    print(f'Query: "{results["query"]}"')
    print(f'Index: {results["index_dir"]}')
    print()

    throughlines = results["throughlines"]
    if throughlines:
        print("Throughlines")
        print("------------")
        for item in throughlines:
            spans = ", ".join(item["spans"])
            score = f"{item['best_score']:.4f}"
            print(f"{item['span_count']}/3  {shorten_path(item['file'])}  score={score}  spans=[{spans}]")
    else:
        print("Throughlines")
        print("------------")
        print("No files appeared in 2+ spans.")

    badges = results["throughline_badges"]
    for span_name, items in results["spans"].items():
        print()
        print(f"{span_name} (top {n_per_span})")
        print("-" * (len(span_name) + 9 + len(str(n_per_span))))
        if not items:
            print("No results.")
            continue
        for rank, item in enumerate(items, start=1):
            badge = badges.get(item["file"], "-")
            path = shorten_path(item["file"])
            preview = preview_text(item["text"])
            score = f"{item['score']:.4f}"
            offsets = f"{item['word_start']}-{item['word_end']}"
            print(f"{rank:>2}. [{badge:<9}] {path}")
            print(f"    score={score} words={offsets}")
            print(f"    {preview}")


def command_index(args: argparse.Namespace) -> int:
    root = Path(args.root).expanduser() if args.root else prompt_for_path()
    build_index(root=root, force=args.force)
    return 0


def command_query(args: argparse.Namespace) -> int:
    query = args.query if args.query else prompt_for_query()
    index_dir = resolve_index_dir(args.index_dir)
    results = query_all_spans(query_text=query, index_dir=index_dir, n_per_span=args.n)
    print_results(results, n_per_span=args.n)
    return 0


def command_list_indices(_: argparse.Namespace) -> int:
    if not INDICES_DIR.exists():
        print("No indices directory found.")
        return 0

    state = load_state()
    active = state.get("active_index_dir")
    entries = sorted(path for path in INDICES_DIR.iterdir() if path.is_dir())
    if not entries:
        print("No indices found.")
        return 0

    for entry in entries:
        marker = "*" if active and Path(str(active)).resolve() == entry.resolve() else " "
        meta_path = entry / "span_25" / "meta.json"
        corpus_root = "unknown"
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text())
                corpus_root = meta.get("corpus_root", "unknown")
            except json.JSONDecodeError:
                pass
        print(f"{marker} {entry.name}  {corpus_root}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Multi-span semantic search with throughline detection.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    index_parser = subparsers.add_parser("index", help="Build or refresh span indices for a directory.")
    index_parser.add_argument("root", nargs="?", help="Directory containing text files to index.")
    index_parser.add_argument("--force", action="store_true", help="Rebuild even if the corpus looks unchanged.")
    index_parser.set_defaults(func=command_index)

    query_parser = subparsers.add_parser("query", help="Search the active index.")
    query_parser.add_argument("query", nargs="?", help="Query text.")
    query_parser.add_argument("--n", type=int, default=8, help="Results per span.")
    query_parser.add_argument("--index-dir", help="Explicit index directory to query.")
    query_parser.set_defaults(func=command_query)

    list_parser = subparsers.add_parser("list-indices", help="List known local indices.")
    list_parser.set_defaults(func=command_list_indices)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
