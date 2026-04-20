#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional


STRATEGY_WEIGHTS = {
    "stubs": 0.8,
    "questions": 1.0,
    "people": 0.7,
    "threads": 0.9,
    "domains": 0.5,
}

ALLOWED_STUB_PREFIXES = (
    "domains/",
    "references/people/",
    "pages/",
)
EXCLUDED_STUB_PREFIXES = (
    "daily/",
    "inbox/",
    "archive/",
)

DOMAIN_QUESTION_MAP = {
    "health/nutrition": "What does a good eating day look like for you?",
    "health/sleep": "What's your current sleep pattern? What affects it?",
    "parenting": "What's something one of your kids did recently that you want to remember?",
    "garden": "What's the current state of the garden? What worked this season?",
}

DOMAIN_EXPECTED_RICHNESS = {
    "health/nutrition": 350.0,
    "health/sleep": 280.0,
    "parenting": 320.0,
    "parenting/milestones": 360.0,
    "garden": 250.0,
}

PATH_RE = re.compile(r"([A-Za-z0-9_./-]+\.[A-Za-z0-9]+)")
DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})(?:[ T](\d{2}:\d{2}(?::\d{2})?))?")


@dataclass
class GapEntry:
    strategy: str
    raw_score: float
    score: float
    setup: str
    prompt: str
    source: str
    metadata: str


def warn(message: str) -> None:
    print(f"Warning: {message}", file=sys.stderr)


def today() -> date:
    return date.today()


def slug_to_name(text: str) -> str:
    stem = Path(text).stem
    if stem.isupper():
        return stem
    parts = [part for part in stem.replace("_", "-").split("-") if part]
    if not parts:
        return stem
    return " ".join(part if part.islower() and len(part) <= 3 else part.capitalize() for part in parts)


def parse_iso_date(text: str) -> Optional[date]:
    match = DATE_RE.search(text)
    if not match:
        return None
    try:
        return datetime.fromisoformat(match.group(1)).date()
    except ValueError:
        return None


def days_since(target: date) -> int:
    return max((today() - target).days, 0)


def extract_path(text: str) -> Optional[str]:
    for match in PATH_RE.finditer(text):
        candidate = match.group(1).strip("`[]()")
        if "/" in candidate or candidate.endswith((".md", ".json")):
            return candidate
    return None


def extract_first_int(text: str, patterns: Iterable[str]) -> Optional[int]:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                continue
    return None


def parse_table_row(line: str) -> List[str]:
    if "|" not in line:
        return []
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    if len(cells) < 2:
        return []
    if all(set(cell) <= {"-", ":"} for cell in cells):
        return []
    return cells


def parse_stats(path: Path) -> List[Dict]:
    records: List[Dict] = []
    if not path.exists():
        warn(f"stats.md missing at {path}")
        return records

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        row = parse_table_row(line)
        if row:
            joined = " | ".join(row)
            file_path = extract_path(joined)
            if not file_path:
                continue
            line_count = extract_first_int(
                joined,
                [
                    r"\b(\d+)\s+lines?\b",
                    r"\b(\d+)\s+loc\b",
                    r"\b(\d+)\b",
                ],
            )
            modified = parse_iso_date(joined)
            records.append({"path": file_path, "lines": line_count or 0, "mtime": modified})
            continue

        file_path = extract_path(line)
        if not file_path:
            continue
        line_count = extract_first_int(
            line,
            [
                r"\b(\d+)\s+lines?\b",
                r"\((\d+)\s+lines?\)",
                r"\blines?:\s*(\d+)\b",
            ],
        )
        modified = parse_iso_date(line)
        records.append({"path": file_path, "lines": line_count or 0, "mtime": modified})

    deduped: Dict[str, Dict] = {}
    for record in records:
        deduped[record["path"]] = record
    return list(deduped.values())


def parse_people(path: Path) -> List[Dict]:
    records: List[Dict] = []
    if not path.exists():
        warn(f"people.md missing at {path}")
        return records

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        row = parse_table_row(line)
        joined = " | ".join(row) if row else line
        file_path = extract_path(joined)
        if not file_path and "people" not in joined.lower():
            continue
        if file_path and "people/" not in file_path:
            continue

        mention_count = extract_first_int(
            joined,
            [
                r"\b(\d+)\s+mentions?\b",
                r"\bmentions?:\s*(\d+)\b",
                r"\b(\d+)\b",
            ],
        )
        stub_lines = extract_first_int(
            joined,
            [
                r"\b(\d+)\s+lines?\b",
                r"\blines?:\s*(\d+)\b",
            ],
        )
        link_match = re.search(r"\[([^\]]+)\]\([^)]+\)", joined)
        name = link_match.group(1).strip() if link_match else None
        if not name and file_path:
            name = slug_to_name(file_path)
        if not file_path or not name:
            continue
        records.append(
            {
                "name": name,
                "path": file_path,
                "mention_count": mention_count or 0,
                "stub_lines": stub_lines,
            }
        )

    deduped: Dict[str, Dict] = {}
    for record in records:
        deduped[record["path"]] = record
    return list(deduped.values())


def parse_blockouts(path: Path) -> List[Dict]:
    records: List[Dict] = []
    if not path.exists():
        warn(f"blockouts.md missing at {path}")
        return records

    current: Optional[Dict] = None
    in_threads_section = False

    def flush_current() -> None:
        nonlocal current
        if current and current.get("threads"):
            records.append(current)
        current = None

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            continue

        file_path = extract_path(stripped)
        line_date = parse_iso_date(stripped)

        if file_path and ("daily/" in file_path or "synthesis" in stripped.lower() or "review" in stripped.lower()):
            flush_current()
            current = {
                "path": file_path,
                "date": line_date or parse_date_from_path(file_path),
                "threads": [],
            }
            in_threads_section = False
            if "threads to watch" in stripped.lower():
                in_threads_section = True
            continue

        if "threads to watch" in stripped.lower():
            if current is None:
                current = {"path": file_path or "", "date": line_date, "threads": []}
            in_threads_section = True
            continue

        if in_threads_section and re.match(r"^[-*]\s+", stripped):
            if current is None:
                current = {"path": "", "date": None, "threads": []}
            thread = re.sub(r"^[-*]\s+", "", stripped).strip()
            thread = thread.strip("`\"")
            if thread:
                current["threads"].append(thread)
            continue

        if stripped.startswith("##") or stripped.startswith("###"):
            in_threads_section = False

    flush_current()
    return records


def parse_date_from_path(path_text: str) -> Optional[date]:
    match = re.search(r"(\d{4}-\d{2}-\d{2})", path_text)
    if not match:
        return None
    try:
        return datetime.fromisoformat(match.group(1)).date()
    except ValueError:
        return None


def detect_stub_gaps(stats: List[Dict], min_age_days: int) -> List[GapEntry]:
    gaps: List[GapEntry] = []
    for record in stats:
        file_path = record.get("path", "")
        line_count = int(record.get("lines") or 0)
        modified = record.get("mtime")
        if not file_path.endswith(".md"):
            continue
        if not file_path.startswith(ALLOWED_STUB_PREFIXES):
            continue
        if file_path.startswith(EXCLUDED_STUB_PREFIXES):
            continue
        if line_count > 10 or modified is None:
            continue
        age_days = days_since(modified)
        if age_days <= 30 or age_days < min_age_days:
            continue
        display_name = slug_to_name(file_path)
        setup = f"The {Path(file_path).name} stub hasn't been updated in {age_days} days."
        prompt = f"What do you know about {display_name} now?"
        metadata = f"{line_count} lines, last modified {modified.isoformat()}, {age_days} days old"
        gaps.append(
            GapEntry(
                strategy="stubs",
                raw_score=min(age_days, 365),
                score=0.0,
                setup=setup,
                prompt=prompt,
                source=file_path,
                metadata=metadata,
            )
        )
    return gaps


def detect_question_gaps(corpus_root: Path, min_age_days: int = 0) -> List[GapEntry]:
    gaps: List[GapEntry] = []
    for json_path in sorted(corpus_root.glob("daily/*/*.json")):
        try:
            payload = json.loads(json_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        questions = payload.get("open_questions")
        if not isinstance(questions, list):
            continue
        question_date = parse_date_from_path(str(json_path))
        if question_date is None:
            continue
        age_days = days_since(question_date)
        if age_days < min_age_days:
            continue
        if age_days <= 30:
            raw_score = 100 - age_days
        elif age_days <= 90:
            raw_score = 70 - ((age_days - 30) * 0.5)
        else:
            raw_score = max(15.0, 40 - ((age_days - 90) * 0.1))

        for item in questions:
            if not isinstance(item, str):
                continue
            question = item.strip()
            if not question:
                continue
            setup = f"You left this question open {age_days} days ago."
            prompt = f'"{question}" — what\'s the current state?'
            metadata = f"from {question_date.isoformat()}, {age_days} days old"
            gaps.append(
                GapEntry(
                    strategy="questions",
                    raw_score=raw_score,
                    score=0.0,
                    setup=setup,
                    prompt=prompt,
                    source=str(json_path.relative_to(corpus_root)),
                    metadata=metadata,
                )
            )
    return gaps


def detect_people_gaps(people: List[Dict], corpus_root: Optional[Path]) -> List[GapEntry]:
    gaps: List[GapEntry] = []
    for person in people:
        mention_count = int(person.get("mention_count") or 0)
        if mention_count < 1 or mention_count > 3:
            continue

        stub_lines = person.get("stub_lines")
        if corpus_root and person.get("path"):
            stub_path = corpus_root / person["path"]
            try:
                stub_lines = len(stub_path.read_text(encoding="utf-8").splitlines())
            except OSError:
                stub_lines = stub_lines

        if stub_lines is None or int(stub_lines) >= 8:
            continue

        name = person["name"]
        source = person["path"]
        setup = f"{name} comes up in your notes but their stub is almost empty."
        prompt = f"What do you know about {name}? How did you meet?"
        metadata = f"{mention_count} mentions, {int(stub_lines)} lines"
        gaps.append(
            GapEntry(
                strategy="people",
                raw_score=float(mention_count),
                score=0.0,
                setup=setup,
                prompt=prompt,
                source=source,
                metadata=metadata,
            )
        )
    return gaps


def normalize_thread_tokens(text: str) -> List[str]:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return [token for token in tokens if len(token) > 3]


def detect_thread_gaps(blockouts: List[Dict], stats: List[Dict], min_age_days: int = 0) -> List[GapEntry]:
    gaps: List[GapEntry] = []
    stats_by_path = stats

    for blockout in blockouts:
        synth_date = blockout.get("date")
        source_path = blockout.get("path") or "blockouts.md"
        if synth_date is None:
            synth_date = parse_date_from_path(source_path)
        if synth_date is None:
            continue
        age_days = days_since(synth_date)
        if age_days < min_age_days:
            continue

        for thread in blockout.get("threads", []):
            tokens = normalize_thread_tokens(thread)
            thread_seen_since = False
            for record in stats_by_path:
                record_path = record.get("path", "")
                if not record_path.startswith("daily/"):
                    continue
                modified = record.get("mtime")
                if modified is None or modified <= synth_date:
                    continue
                lowered = record_path.lower()
                if any(token in lowered for token in tokens):
                    thread_seen_since = True
                    break
            if thread_seen_since:
                continue

            setup = f'"{thread}" was flagged as a thread to watch in your {synth_date.isoformat()} synthesis.'
            prompt = f"Where is that now?"
            metadata = f"flagged {age_days} days ago"
            gaps.append(
                GapEntry(
                    strategy="threads",
                    raw_score=float(age_days),
                    score=0.0,
                    setup=setup,
                    prompt=prompt,
                    source=source_path,
                    metadata=metadata,
                )
            )
    return gaps


def domain_key_for_path(path_text: str) -> Optional[str]:
    parts = Path(path_text).parts
    if not parts or parts[0] != "domains" or len(parts) < 2:
        return None
    if len(parts) >= 3:
        return "/".join(parts[1:3])
    return parts[1]


def domain_question(domain: str) -> str:
    for prefix, question in DOMAIN_QUESTION_MAP.items():
        if domain == prefix or domain.startswith(prefix):
            return question
    return f"What's missing from your {domain} notes right now?"


def expected_richness(domain: str) -> float:
    for prefix, weight in DOMAIN_EXPECTED_RICHNESS.items():
        if domain == prefix or domain.startswith(prefix):
            return weight
    return 180.0


def detect_domain_gaps(stats: List[Dict]) -> List[GapEntry]:
    grouped: Dict[str, Dict[str, float]] = defaultdict(lambda: {"files": 0, "lines": 0, "indicator_bonus": 0})
    for record in stats:
        file_path = record.get("path", "")
        domain = domain_key_for_path(file_path)
        if not domain:
            continue
        grouped[domain]["files"] += 1
        grouped[domain]["lines"] += int(record.get("lines") or 0)
        filename = Path(file_path).name
        if filename in {"learnings.md", "metrics.md"}:
            grouped[domain]["indicator_bonus"] += 40

    gaps: List[GapEntry] = []
    for domain, totals in grouped.items():
        file_count = int(totals["files"])
        line_count = int(totals["lines"])
        if file_count >= 5 and line_count >= 200:
            continue
        expected = expected_richness(domain)
        raw_score = (expected + totals["indicator_bonus"]) / max(line_count, 1)
        setup = f"Your {domain} notes are sparse."
        prompt = domain_question(domain)
        metadata = f"{file_count} files, {line_count} lines"
        gaps.append(
            GapEntry(
                strategy="domains",
                raw_score=raw_score,
                score=0.0,
                setup=setup,
                prompt=prompt,
                source=f"domains/{domain}",
                metadata=metadata,
            )
        )
    return gaps


def rank_gaps(all_gaps: List[GapEntry], n: int) -> List[GapEntry]:
    by_strategy: Dict[str, List[GapEntry]] = defaultdict(list)
    for gap in all_gaps:
        by_strategy[gap.strategy].append(gap)

    ranked: List[GapEntry] = []
    for strategy, gaps in by_strategy.items():
        raw_scores = [gap.raw_score for gap in gaps]
        minimum = min(raw_scores)
        maximum = max(raw_scores)
        weight = STRATEGY_WEIGHTS.get(strategy, 1.0)
        for gap in gaps:
            if maximum == minimum:
                normalized = 1.0
            else:
                normalized = (gap.raw_score - minimum) / (maximum - minimum)
            gap.score = normalized * weight
            ranked.append(gap)

    ranked.sort(key=lambda gap: (-gap.score, -gap.raw_score, gap.strategy, gap.source))
    return ranked[:n]


def render_text(gaps: List[GapEntry]) -> str:
    chunks = []
    for index, gap in enumerate(gaps, start=1):
        chunks.append(
            f"{index}. [{gap.strategy}] {gap.setup}\n"
            f"   \u2192 {gap.prompt}\n"
            f"   Source: {gap.source} ({gap.metadata})"
        )
    return "\n\n".join(chunks)


def render_json(gaps: List[GapEntry]) -> str:
    payload = []
    for index, gap in enumerate(gaps, start=1):
        item = {
            "rank": index,
            "strategy": gap.strategy,
            "score": round(gap.score, 4),
            "setup": gap.setup,
            "prompt": gap.prompt,
            "source": gap.source,
        }
        payload.append(item)
    return json.dumps(payload, indent=2)


def render_inbox(gaps: List[GapEntry]) -> str:
    lines = [
        f"# Askme — {today().isoformat()}",
        "",
        "Generated from gaps in the note-system index.",
        "",
        "---",
        "",
    ]
    for index, gap in enumerate(gaps, start=1):
        lines.extend(
            [
                f"{index}. {gap.setup}",
                f"**Prompt**: {gap.prompt}",
                f"Source: {gap.source}",
                "",
                "---",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def write_output(output: str, out_path: Optional[Path]) -> None:
    if out_path is None:
        print(output)
        return
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(output + ("" if output.endswith("\n") else "\n"), encoding="utf-8")


def enrich_people_with_stats(people: List[Dict], stats: List[Dict]) -> None:
    stats_by_path = {record["path"]: record for record in stats}
    for person in people:
        if person.get("stub_lines") is None:
            stat_record = stats_by_path.get(person["path"])
            if stat_record:
                person["stub_lines"] = stat_record.get("lines")


def gather_gaps(
    index_dir: Path,
    corpus_root: Optional[Path],
    gap_type: Optional[str],
    min_age_days: int,
) -> List[GapEntry]:
    stats = parse_stats(index_dir / "stats.md")
    people = parse_people(index_dir / "people.md")
    blockouts = parse_blockouts(index_dir / "blockouts.md")
    enrich_people_with_stats(people, stats)

    detectors = {
        "stubs": lambda: detect_stub_gaps(stats, min_age_days),
        "people": lambda: detect_people_gaps(people, corpus_root),
        "questions": lambda: detect_question_gaps(corpus_root, min_age_days) if corpus_root else [],
        "threads": lambda: detect_thread_gaps(blockouts, stats, min_age_days),
        "domains": lambda: detect_domain_gaps(stats),
    }

    if gap_type:
        gaps = detectors[gap_type]()
        if not gaps:
            print(f"No gaps detected in {gap_type}. Try --type to broaden the search.")
        return gaps

    all_gaps: List[GapEntry] = []
    for strategy, detector in detectors.items():
        strategy_gaps = detector()
        all_gaps.extend(strategy_gaps)
    if not all_gaps:
        print("The index looks complete — or the index files may need regenerating.")
    return all_gaps


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Detect knowledge gaps and generate prompts.")
    parser.add_argument("--index-dir", required=True, help="Path to .index/ directory")
    parser.add_argument("--corpus", help="Path to corpus root (enables corpus mode)")
    parser.add_argument(
        "--type",
        choices=["stubs", "people", "questions", "threads", "domains"],
        help="Filter to one strategy",
    )
    parser.add_argument("--n", type=int, default=5, help="Number of prompts to return")
    parser.add_argument(
        "--format",
        choices=["text", "json", "inbox"],
        default="text",
        help="Output format",
    )
    parser.add_argument("--out", help="Write output to file instead of stdout")
    parser.add_argument("--min-age", type=int, default=0, help="Only surface gaps older than N days")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    index_dir = Path(args.index_dir).expanduser()
    if not index_dir.is_dir():
        print(f"Error: index directory not found: {index_dir}")
        return 1

    corpus_root = Path(args.corpus).expanduser() if args.corpus else None
    if corpus_root is not None and not corpus_root.is_dir():
        print(f"Error: corpus directory not found: {corpus_root}")
        return 1

    gaps = gather_gaps(index_dir, corpus_root, args.type, args.min_age)
    if not gaps:
        return 0

    ranked = rank_gaps(gaps, max(args.n, 1))
    if args.format == "json":
        output = render_json(ranked)
    elif args.format == "inbox":
        output = render_inbox(ranked)
    else:
        output = render_text(ranked)
    write_output(output, Path(args.out).expanduser() if args.out else None)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
