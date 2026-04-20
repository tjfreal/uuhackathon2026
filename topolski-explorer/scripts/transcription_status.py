#!/usr/bin/env python3
"""
transcription_status.py

Quick local status view for the Topolski transcription run.
Shows how much of the staged corpus is complete and what item/page was most recently written.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
STAGED_DATA_DIR = BASE_DIR / "data" / "staged"


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> None:
    item_dirs = sorted(path for path in STAGED_DATA_DIR.iterdir() if path.is_dir()) if STAGED_DATA_DIR.exists() else []

    staged_items = 0
    staged_pages = 0
    transcribed_items = 0
    transcribed_pages = 0
    last_success: tuple[str, int, str] | None = None

    for item_dir in item_dirs:
        item_id = item_dir.name
        metadata_path = STAGED_DATA_DIR / f"{item_id}.json"
        transcription_path = item_dir / "transcription.json"

        staged_items += 1
        if metadata_path.exists():
            try:
                metadata = load_json(metadata_path)
                staged_pages += len(metadata.get("page_images", []))
            except Exception:
                pass

        if not transcription_path.exists():
            continue

        try:
            transcription = load_json(transcription_path)
        except Exception:
            continue

        pages = transcription.get("pages", [])
        if pages:
            transcribed_items += 1
            transcribed_pages += len(pages)

        for page in pages:
            page_number = page.get("page_number")
            transcribed_at = page.get("transcribed_at") or ""
            if isinstance(page_number, int) and transcribed_at:
                if last_success is None or transcribed_at > last_success[2]:
                    last_success = (item_id, page_number, transcribed_at)

    item_pct = (transcribed_items / staged_items * 100.0) if staged_items else 0.0
    page_pct = (transcribed_pages / staged_pages * 100.0) if staged_pages else 0.0

    print(f"staged_items={staged_items}")
    print(f"staged_pages={staged_pages}")
    print(f"transcribed_items={transcribed_items}")
    print(f"transcribed_pages={transcribed_pages}")
    print(f"item_completion_pct={item_pct:.1f}")
    print(f"page_completion_pct={page_pct:.1f}")

    if last_success:
        item_id, page_number, transcribed_at = last_success
        try:
            pretty = datetime.fromisoformat(transcribed_at.replace("Z", "+00:00")).isoformat()
        except Exception:
            pretty = transcribed_at
        print(f"last_success_item={item_id}")
        print(f"last_success_page={page_number}")
        print(f"last_success_at={pretty}")
    else:
        print("last_success_item=")
        print("last_success_page=")
        print("last_success_at=")


if __name__ == "__main__":
    main()
