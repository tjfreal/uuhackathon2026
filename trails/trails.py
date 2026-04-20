#!/usr/bin/env python3

from __future__ import annotations

import argparse
import difflib
import json
import math
import os
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Iterable, Optional


TEXT_EXTENSIONS = {".md", ".markdown", ".txt", ".rst", ".text", ".org"}
FILENAME_DATE_RE = re.compile(r"^(?P<year>\d{4})[-_](?P<month>\d{2})[-_](?P<day>\d{2})(?:$|[-_])")
FRONTMATTER_DATE_RE = re.compile(r"^\s*date\s*:\s*(?P<value>\d{4}(?:-\d{2}(?:-\d{2})?)?)\s*$", re.IGNORECASE)
CONTENT_DATE_RE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
MARKDOWN_NOISE_RE = re.compile(r"[*_`>#\[\]\(\)|]+")
MODEL_NAME = "nomic-ai/nomic-embed-text-v1.5"
DEFAULT_N = 30


@dataclass
class DateInfo:
    value: Optional[date]
    confidence: str
    precision: str


@dataclass
class TimelineEntry:
    date: Optional[date]
    date_confidence: str
    date_precision: str
    path: Path
    rel_path: str
    excerpt: str


def warn(message: str) -> None:
    print(f"Warning: {message}", file=sys.stderr)


def discover_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in TEXT_EXTENSIONS
    )


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def parse_date_value(value: str, confidence: str) -> Optional[DateInfo]:
    parts = value.strip().split("-")
    try:
        if len(parts) == 3:
            return DateInfo(date(int(parts[0]), int(parts[1]), int(parts[2])), confidence, "day")
        if len(parts) == 2:
            return DateInfo(date(int(parts[0]), int(parts[1]), 1), confidence, "month")
        if len(parts) == 1:
            return DateInfo(date(int(parts[0]), 1, 1), confidence, "year")
    except ValueError:
        return None
    return None


def extract_date(path: Path, text: str) -> tuple[Optional[date], str]:
    info = extract_date_info(path, text)
    return info.value, info.confidence


def extract_date_info(path: Path, text: str) -> DateInfo:
    stem_match = FILENAME_DATE_RE.match(path.stem)
    if stem_match:
        try:
            return DateInfo(
                date(
                    int(stem_match.group("year")),
                    int(stem_match.group("month")),
                    int(stem_match.group("day")),
                ),
                "filename",
                "day",
            )
        except ValueError:
            pass

    for line in text.splitlines()[:10]:
        match = FRONTMATTER_DATE_RE.match(line)
        if not match:
            continue
        info = parse_date_value(match.group("value"), "frontmatter")
        if info:
            return info

    earliest: Optional[date] = None
    for year_text, month_text, day_text in CONTENT_DATE_RE.findall(text):
        try:
            candidate = date(int(year_text), int(month_text), int(day_text))
        except ValueError:
            continue
        if earliest is None or candidate < earliest:
            earliest = candidate
    if earliest is not None:
        return DateInfo(earliest, "content", "day")

    return DateInfo(None, "none", "none")


def normalize_query_terms(query: str) -> list[str]:
    return [term.casefold() for term in query.split() if term.strip()]


def search_keyword(files: Iterable[Path], query: str) -> list[tuple[Path, str]]:
    terms = normalize_query_terms(query)
    matches: list[tuple[Path, str]] = []
    for path in files:
        filename_text = path.name.casefold()
        text = read_text(path)
        lower_text = text.casefold()

        if not terms:
            continue
        if not all(term in filename_text or term in lower_text for term in terms):
            continue

        matched_line = first_matching_line(text, terms)
        if not matched_line and all(term in filename_text for term in terms):
            matched_line = path.name
        matches.append((path, matched_line))
    return matches


def first_matching_line(text: str, terms: list[str]) -> str:
    for line in text.splitlines():
        lowered = line.casefold()
        if all(term in lowered for term in terms):
            return line
    return ""


def cosine_similarity(query_vector: Any, matrix: Any) -> Any:
    return matrix @ query_vector


def load_embedding_dependencies() -> tuple[Any, Any]:
    try:
        import numpy as np
    except ImportError as exc:
        raise RuntimeError("missing `numpy`") from exc

    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError("missing `sentence-transformers`") from exc

    return np, SentenceTransformer


def embed_query(query: str) -> Any:
    np, sentence_transformer = load_embedding_dependencies()
    model = sentence_transformer(MODEL_NAME, trust_remote_code=True)
    vector = model.encode(
        [f"search_query: {query}"],
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )[0]
    return np.asarray(vector, dtype=np.float32)


def search_embedding(files: Iterable[Path], query: str, index_dir: Path, limit: int) -> list[tuple[Path, str, float]]:
    file_list = list(files)
    files_by_rel = build_file_lookup(file_list)
    files_by_name = {path.name: path for path in file_list}
    chunks_path = index_dir / "chunks.jsonl"
    if not chunks_path.exists():
        raise SystemExit(f"Error: no embeddings index found at {index_dir}")

    query_vector = embed_query(query)
    np, _ = load_embedding_dependencies()

    best_by_file: dict[Path, tuple[str, float]] = {}
    with chunks_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            file_value = str(row.get("file", "")).strip()
            chunk_text = str(row.get("text", "")).strip()
            vector = row.get("vector")
            if not file_value or not chunk_text or not isinstance(vector, list):
                continue

            path = resolve_index_path(file_value, files_by_rel, files_by_name)
            if path is None:
                continue

            score = float(cosine_similarity(query_vector, np.asarray(vector, dtype=np.float32)))
            current = best_by_file.get(path)
            if current is None or score > current[1]:
                best_by_file[path] = (chunk_text, score)

    ranked = sorted(
        ((path, text, score) for path, (text, score) in best_by_file.items()),
        key=lambda item: item[2],
        reverse=True,
    )
    return ranked[:limit]


def resolve_index_path(file_value: str, files_by_rel: dict[str, Path], files_by_name: dict[str, Path]) -> Optional[Path]:
    candidates = [file_value, file_value.lstrip("./")]
    for candidate in candidates:
        if candidate in files_by_rel:
            return files_by_rel[candidate]
    return files_by_name.get(Path(file_value).name)


def build_file_lookup(files: list[Path]) -> dict[str, Path]:
    lookup: dict[str, Path] = {}
    if not files:
        return lookup

    common_root = Path(os.path.commonpath([str(path) for path in files]))
    if common_root.suffix.lower() in TEXT_EXTENSIONS:
        common_root = common_root.parent

    for path in files:
        lookup[str(path)] = path
        lookup[path.as_posix()] = path
        try:
            rel_path = path.relative_to(common_root)
            lookup[str(rel_path)] = path
            lookup[rel_path.as_posix()] = path
        except ValueError:
            pass
    return lookup


def extract_passage(path: Path, text: str, match_hint: str, context_lines: int = 3) -> str:
    lines = text.splitlines()
    hint = match_hint.strip().casefold()

    match_index = 0
    if hint:
        for index, line in enumerate(lines):
            if hint in line.casefold():
                match_index = index
                break

    start = max(0, match_index - context_lines)
    end = min(len(lines), match_index + context_lines + 1)
    window = lines[start:end] if lines else []
    excerpt = " ".join(clean_markdown(line) for line in window)
    excerpt = re.sub(r"\s+", " ", excerpt).strip()

    if not excerpt:
        excerpt = clean_markdown(text[:400])
        excerpt = re.sub(r"\s+", " ", excerpt).strip()

    if len(excerpt) > 200:
        return excerpt[:197].rstrip() + "..."
    return excerpt


def clean_markdown(text: str) -> str:
    cleaned = text.strip()
    cleaned = re.sub(r"^\s{0,3}#{1,6}\s*", "", cleaned)
    cleaned = re.sub(r"^\s*[-*+]\s+", "", cleaned)
    cleaned = re.sub(r"^\s*\d+\.\s+", "", cleaned)
    cleaned = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", cleaned)
    cleaned = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", cleaned)
    cleaned = cleaned.replace("**", "").replace("__", "").replace("*", "").replace("_", "").replace("`", "")
    cleaned = MARKDOWN_NOISE_RE.sub(" ", cleaned)
    return cleaned.strip()


def excerpt_similarity(left: str, right: str) -> float:
    if not left.strip() or not right.strip():
        return 0.0
    return difflib.SequenceMatcher(None, left.casefold(), right.casefold()).ratio()


def precision_rank(entry: TimelineEntry) -> int:
    ranks = {"day": 3, "month": 2, "year": 1, "none": 0}
    return ranks.get(entry.date_precision, 0)


def preferred_duplicate(current: TimelineEntry, candidate: TimelineEntry) -> TimelineEntry:
    current_daily = current.path.suffix.lower() == ".md" and bool(re.match(r"^\d{4}[-_]\d{2}[-_]\d{2}", current.path.stem))
    candidate_daily = candidate.path.suffix.lower() == ".md" and bool(re.match(r"^\d{4}[-_]\d{2}[-_]\d{2}", candidate.path.stem))
    if candidate_daily != current_daily:
        return candidate if candidate_daily else current
    if precision_rank(candidate) != precision_rank(current):
        return candidate if precision_rank(candidate) > precision_rank(current) else current
    if (candidate.date or date.max) != (current.date or date.max):
        return candidate if (candidate.date or date.max) < (current.date or date.max) else current
    return candidate if len(candidate.excerpt) >= len(current.excerpt) else current


def dedupe_entries(entries: list[TimelineEntry]) -> list[TimelineEntry]:
    deduped: list[TimelineEntry] = []
    for entry in entries:
        replaced = False
        for index, existing in enumerate(deduped):
            if excerpt_similarity(existing.excerpt, entry.excerpt) > 0.8:
                deduped[index] = preferred_duplicate(existing, entry)
                replaced = True
                break
        if not replaced:
            deduped.append(entry)
    return deduped


def sort_key(entry: TimelineEntry) -> tuple[int, date, int, str]:
    if entry.date is None:
        return (2, date.max, 0, entry.rel_path)
    exactness_bucket = 1 if entry.date_confidence == "content" else {"day": 0, "month": 1, "year": 1}.get(entry.date_precision, 1)
    return (exactness_bucket, entry.date, -precision_rank(entry), entry.rel_path)


def format_entry_date(entry: TimelineEntry) -> str:
    if entry.date is None:
        return "undated"
    if entry.date_confidence == "content":
        return f"{entry.date:%Y} (circa)"
    if entry.date_precision == "month":
        return f"{entry.date:%Y-%m}"
    if entry.date_precision == "year":
        return f"{entry.date:%Y}"
    return f"{entry.date:%Y-%m-%d}"


def filter_by_date(entry: TimelineEntry, since: Optional[date], until: Optional[date]) -> bool:
    if since is None and until is None:
        return True
    if entry.date is None:
        return False
    if since is not None and entry.date < since:
        return False
    if until is not None and entry.date > until:
        return False
    return True


def render_list(entries: list[TimelineEntry], query: str, show_dates: bool = False) -> str:
    lines = [f"## {query} arc", ""]
    for entry in entries:
        header = f"{format_entry_date(entry)}  {entry.rel_path}"
        if show_dates:
            header += f" [{entry.date_confidence}]"
        lines.append(header)
        lines.append(f"  {entry.excerpt}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_json(entries: list[TimelineEntry]) -> str:
    payload = [
        {
            "date": format_entry_date(entry),
            "date_confidence": entry.date_confidence,
            "file": entry.rel_path,
            "excerpt": entry.excerpt,
        }
        for entry in entries
    ]
    return json.dumps(payload, indent=2) + "\n"


def render_narrative(entries: list[TimelineEntry], query: str, show_dates: bool = False) -> str:
    timeline_text = render_list(entries, query, show_dates=show_dates)
    prompt = (
        f"Write a 3-5 paragraph narrative about the development of '{query}' across these dated excerpts. "
        "Stay grounded in the evidence, note shifts over time, and avoid bullet points.\n\n"
        f"{timeline_text}"
    )

    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    if anthropic_key:
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=anthropic_key)
            response = client.messages.create(
                model="claude-3-5-sonnet-latest",
                max_tokens=900,
                messages=[{"role": "user", "content": prompt}],
            )
            parts = []
            for block in response.content:
                text = getattr(block, "text", "")
                if text:
                    parts.append(text)
            if parts:
                return "\n".join(parts).strip() + "\n"
        except Exception as exc:
            warn(f"narrative mode failed with anthropic SDK ({exc}); falling back to list format")
            return timeline_text

    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=openai_key)
            response = client.responses.create(
                model="gpt-4.1-mini",
                input=prompt,
                max_output_tokens=900,
            )
            output_text = getattr(response, "output_text", "")
            if output_text:
                return output_text.strip() + "\n"
        except Exception as exc:
            warn(f"narrative mode failed with openai SDK ({exc}); falling back to list format")
            return timeline_text

    warn("narrative mode requested but no supported SDK/API key was available; falling back to list format")
    return timeline_text


def slugify_query(query: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", query.casefold()).strip("-")
    slug = slug[:40].rstrip("-")
    return slug or "timeline"


def resolve_output_path(out_arg: str, query: str) -> Path:
    out_path = Path(out_arg).expanduser()
    if out_path.exists() and out_path.is_dir():
        return out_path / f"{date.today():%Y-%m-%d}-{slugify_query(query)}.md"
    if out_arg.endswith(("/", "\\")):
        out_path.mkdir(parents=True, exist_ok=True)
        return out_path / f"{date.today():%Y-%m-%d}-{slugify_query(query)}.md"
    if out_path.suffix:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        return out_path
    out_path.mkdir(parents=True, exist_ok=True)
    return out_path / f"{date.today():%Y-%m-%d}-{slugify_query(query)}.md"


def parse_cli_date(value: Optional[str], flag: str) -> Optional[date]:
    if value is None:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise SystemExit(f"Error: invalid {flag} date: {value}") from exc


def assemble_entries(
    corpus_root: Path,
    files: list[Path],
    matches: list[tuple[Path, str]],
    since: Optional[date],
    until: Optional[date],
) -> list[TimelineEntry]:
    entries: list[TimelineEntry] = []
    for path, match_hint in matches:
        text = read_text(path)
        date_info = extract_date_info(path, text)
        rel_path = str(path.relative_to(corpus_root))
        excerpt = extract_passage(path, text, match_hint)
        if not excerpt:
            continue
        entry = TimelineEntry(
            date=date_info.value,
            date_confidence=date_info.confidence,
            date_precision=date_info.precision,
            path=path,
            rel_path=rel_path,
            excerpt=excerpt,
        )
        if filter_by_date(entry, since, until):
            entries.append(entry)
    return sorted(dedupe_entries(entries), key=sort_key)


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="trails.py")
    subparsers = parser.add_subparsers(dest="command", required=True)

    query_parser = subparsers.add_parser("query")
    query_parser.add_argument("topic")
    query_parser.add_argument("--corpus", default=".")
    query_parser.add_argument("--format", choices=("list", "narrative", "json"), default="list")
    query_parser.add_argument("--out")
    query_parser.add_argument("--n", type=int, default=DEFAULT_N)
    query_parser.add_argument("--index")
    query_parser.add_argument("--domain")
    query_parser.add_argument("--since")
    query_parser.add_argument("--until")
    query_parser.add_argument("--show-dates", action="store_true")
    return parser.parse_args(argv)


def run_query(args: argparse.Namespace) -> int:
    corpus_root = Path(args.corpus).expanduser().resolve()
    if args.domain:
        corpus_root = (corpus_root / args.domain).resolve()
    if not corpus_root.exists():
        print(f"Error: corpus path does not exist: {corpus_root}", file=sys.stderr)
        return 1
    if not corpus_root.is_dir():
        print(f"Error: corpus path does not exist: {corpus_root}", file=sys.stderr)
        return 1

    files = discover_files(corpus_root)
    if not files:
        print(f"No text files found in {corpus_root}")
        return 0

    since = parse_cli_date(args.since, "--since")
    until = parse_cli_date(args.until, "--until")

    if args.index:
        try:
            matches = [(path, chunk_text) for path, chunk_text, _score in search_embedding(files, args.topic, Path(args.index).expanduser().resolve(), args.n)]
        except RuntimeError as exc:
            warn(f"{exc}; falling back to keyword mode")
            matches = search_keyword(files, args.topic)
        except SystemExit:
            raise
    else:
        matches = search_keyword(files, args.topic)

    if not matches:
        print(f'No matches found for "{args.topic}" in {len(files)} files.')
        return 0

    entries = assemble_entries(corpus_root, files, matches, since, until)
    if args.n > 0:
        entries = entries[: args.n]
    if not entries:
        print(f'No matches found for "{args.topic}" in {len(files)} files.')
        return 0

    if args.format == "json":
        rendered = render_json(entries)
    elif args.format == "narrative":
        rendered = render_narrative(entries, args.topic, show_dates=args.show_dates)
    else:
        rendered = render_list(entries, args.topic, show_dates=args.show_dates)

    if args.out:
        output_path = resolve_output_path(args.out, args.topic)
        output_path.write_text(rendered, encoding="utf-8")
        print(output_path)
    else:
        print(rendered, end="")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    if args.command == "query":
        return run_query(args)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
