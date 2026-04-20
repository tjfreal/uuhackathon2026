#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Iterable, Sequence


SIGNAL_TYPES: tuple[str, ...] = (
    "observation",
    "decision",
    "question",
    "friction",
    "follow_up",
)

REVIEW_ORDER: tuple[str, ...] = SIGNAL_TYPES

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
LEADING_MARKER_RE = re.compile(r"^\s*(?:[-*+]\s+|\d+[.)]\s+|\[[ xX]\]\s+)+")


@dataclass(frozen=True)
class LineRecord:
    number: int
    raw_text: str
    heading: str | None


@dataclass(frozen=True)
class Signal:
    id: str
    type: str
    text: str
    source_file: str
    heading: str | None
    line_start: int
    line_end: int
    confidence: float


def companion_dir_for(note_path: Path) -> Path:
    return note_path.with_suffix("")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract structured signals from a single markdown note."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    extract_parser = subparsers.add_parser("extract", help="Extract signals from a note.")
    extract_parser.add_argument("note_path", help="Path to the markdown note.")
    extract_parser.add_argument(
        "--stdout-json",
        action="store_true",
        help="Print JSON to stdout in addition to writing files.",
    )
    extract_parser.add_argument(
        "--stdout-review",
        action="store_true",
        help="Print markdown review to stdout in addition to writing files.",
    )
    extract_parser.add_argument(
        "--no-create-dir",
        action="store_true",
        help="Fail instead of creating the companion directory.",
    )

    return parser.parse_args(argv)


def fail(message: str) -> int:
    print(message, file=sys.stderr)
    return 1


def validate_note_path(note_path: Path) -> Path | None:
    if not note_path.exists():
        fail(f"Error: note path does not exist: {note_path}")
        return None
    if not note_path.is_file() or note_path.suffix.lower() != ".md":
        fail(f"Error: expected a markdown file, got: {note_path}")
        return None
    return Path(os.path.abspath(note_path))


def ensure_companion_dir(note_path: Path, no_create_dir: bool) -> Path | None:
    companion_dir = companion_dir_for(note_path)
    if companion_dir.exists():
        if not companion_dir.is_dir():
            fail(f"Error: companion directory does not exist: {companion_dir}")
            return None
        return companion_dir
    if no_create_dir:
        fail(f"Error: companion directory does not exist: {companion_dir}")
        return None
    companion_dir.mkdir(parents=False, exist_ok=True)
    return companion_dir


def parse_markdown_lines(note_path: Path) -> list[LineRecord]:
    records: list[LineRecord] = []
    current_heading: str | None = None

    for line_number, raw_line in enumerate(
        note_path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        heading_match = HEADING_RE.match(raw_line)
        if heading_match:
            current_heading = heading_match.group(2).strip()
        records.append(
            LineRecord(number=line_number, raw_text=raw_line, heading=current_heading)
        )

    return records


def is_heading_line(text: str) -> bool:
    return bool(HEADING_RE.match(text))


def strip_leading_marker(text: str) -> str:
    return LEADING_MARKER_RE.sub("", text).strip()


def normalize_text(text: str) -> str:
    cleaned = strip_leading_marker(text)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def is_signal_candidate(record: LineRecord) -> bool:
    stripped = record.raw_text.strip()
    if not stripped:
        return False
    if is_heading_line(record.raw_text):
        return False
    if stripped.startswith(">"):
        return False
    return True


def collect_signal_span(records: Sequence[LineRecord], start_index: int) -> tuple[str, int]:
    first_record = records[start_index]
    first_text = first_record.raw_text.rstrip()
    span_lines = [first_text.strip()]
    end_index = start_index

    base_is_listish = bool(
        re.match(r"^\s*(?:[-*+]\s+|\d+[.)]\s+|\[[ xX]\]\s+)", first_text)
    )

    for idx in range(start_index + 1, len(records)):
        candidate = records[idx]
        stripped = candidate.raw_text.strip()
        if not stripped or is_heading_line(candidate.raw_text):
            break

        continuation = False
        if base_is_listish and candidate.raw_text[:1].isspace():
            continuation = True
        elif candidate.heading == first_record.heading and candidate.raw_text[:1].isspace():
            continuation = True

        if not continuation:
            break

        span_lines.append(stripped)
        end_index = idx

    span_text = " ".join(part for part in span_lines if part).strip()
    return normalize_text(span_text), end_index


def match_question(text: str) -> float | None:
    lowered = text.lower()
    if text.endswith("?"):
        return 0.97
    if lowered.startswith("q:"):
        return 0.95
    if re.match(r"^(what|why|how|should|could|can|where|when)\b", lowered):
        return 0.84
    return None


def match_decision(text: str) -> float | None:
    lowered = text.lower()
    if lowered.startswith("decision:"):
        return 0.98
    if any(
        phrase in lowered
        for phrase in (
            "i decided",
            "i'm going to",
            "i am going to",
            "i will ",
            "we will ",
            "decided to",
        )
    ):
        return 0.88
    return None


def match_friction(text: str) -> float | None:
    lowered = text.lower()
    phrases = (
        "blocked by",
        "stuck on",
        "keeps failing",
        "keep failing",
        "problem",
        "friction",
        "issue",
        "bottleneck",
    )
    if any(phrase in lowered for phrase in phrases):
        return 0.86
    return None


def match_follow_up(text: str) -> float | None:
    lowered = text.lower()
    if any(
        lowered.startswith(prefix)
        for prefix in ("todo:", "next:", "follow up:", "follow-up:", "action:")
    ):
        return 0.97
    if any(
        phrase in lowered
        for phrase in ("need to", "should try", "come back to", "follow up", "follow-up")
    ):
        return 0.85
    return None


def match_observation(text: str) -> float | None:
    lowered = text.lower()
    phrases = (
        "i noticed",
        "it seems",
        "the pattern is",
        "what keeps happening",
        "i keep noticing",
        "i'm noticing",
    )
    if any(phrase in lowered for phrase in phrases):
        return 0.82
    return None


def classify_signal(text: str) -> tuple[str, float] | None:
    checks: Iterable[tuple[str, Callable[[str], float | None]]] = (
        ("decision", match_decision),
        ("follow_up", match_follow_up),
        ("friction", match_friction),
        ("question", match_question),
        ("observation", match_observation),
    )
    for signal_type, matcher in checks:
        confidence = matcher(text)
        if confidence is not None:
            return signal_type, confidence
    return None


def extract_signals(records: Sequence[LineRecord], note_path: Path) -> list[Signal]:
    signals: list[Signal] = []
    next_id = 1
    index = 0

    while index < len(records):
        record = records[index]
        if not is_signal_candidate(record):
            index += 1
            continue

        text, end_index = collect_signal_span(records, index)
        if not text:
            index += 1
            continue

        match = classify_signal(text)
        if match is None:
            index += 1
            continue

        signal_type, confidence = match
        signals.append(
            Signal(
                id=f"sig-{next_id:04d}",
                type=signal_type,
                text=text,
                source_file=str(note_path),
                heading=record.heading,
                line_start=record.number,
                line_end=records[end_index].number,
                confidence=round(confidence, 2),
            )
        )
        next_id += 1
        index = end_index + 1

    return signals


def render_review(signals: Sequence[Signal], source_note: Path) -> str:
    lines = ["# Signals Review", "", f"Source: {source_note.name}", ""]

    if not signals:
        lines.append("No signals were found.")
        return "\n".join(lines) + "\n"

    for signal_type in REVIEW_ORDER:
        typed_signals = [signal for signal in signals if signal.type == signal_type]
        lines.append(f"## {signal_type}")
        lines.append("")
        if not typed_signals:
            lines.append("No signals found.")
            lines.append("")
            continue

        for signal in typed_signals:
            lines.append(f"- [{signal.id}] lines {signal.line_start}-{signal.line_end}")
            if signal.heading:
                lines.append(f"  Heading: {signal.heading}")
            lines.append(f"  {signal.text}")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_outputs(companion_dir: Path, signals: Sequence[Signal], review_text: str) -> None:
    json_path = companion_dir / "signals.json"
    review_path = companion_dir / "signals_review.md"

    json_payload = [asdict(signal) for signal in signals]
    json_path.write_text(json.dumps(json_payload, indent=2) + "\n", encoding="utf-8")
    review_path.write_text(review_text, encoding="utf-8")


def run_extract(args: argparse.Namespace) -> int:
    note_path_input = Path(args.note_path)
    note_path = validate_note_path(note_path_input)
    if note_path is None:
        return 1

    companion_dir = ensure_companion_dir(note_path, args.no_create_dir)
    if companion_dir is None:
        return 1

    records = parse_markdown_lines(note_path)
    signals = extract_signals(records, note_path)
    review_text = render_review(signals, note_path)

    write_outputs(companion_dir, signals, review_text)

    if args.stdout_json:
        print(json.dumps([asdict(signal) for signal in signals], indent=2))
    if args.stdout_review:
        if args.stdout_json:
            print()
        print(review_text, end="")

    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if args.command == "extract":
        return run_extract(args)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
