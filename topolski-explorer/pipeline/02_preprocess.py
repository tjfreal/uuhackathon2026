"""
02_preprocess.py — Raw Corpus to Working Dataset

Builds a normalized local working layout from the raw Topolski corpus.

Input per item:
  {RAW_DATA_DIR}/{item_id}.pdf
  {RAW_DATA_DIR}/{item_id}.json

Output per item:
  {STAGED_DATA_DIR}/{item_id}.json
  {STAGED_DATA_DIR}/{item_id}/page_0001.jpg
  {STAGED_DATA_DIR}/{item_id}/page_0002.jpg
  ...

The script is idempotent and resume-safe:
  - existing page images are reused
  - normalized metadata is regenerated from raw metadata on each run
  - missing or partial items are skipped without breaking the run
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

RAW_DATA_DIR = Path(os.getenv("RAW_DATA_DIR", "staged_data_raw"))
STAGED_DATA_DIR = Path(os.getenv("STAGED_DATA_DIR", "data/staged"))
PAGE_IMAGE_LONG_EDGE = int(os.getenv("PAGE_IMAGE_LONG_EDGE", "1568"))
MAX_ITEMS = int(os.getenv("MAX_ITEMS", "0") or "0")
ITEM_ID_MIN = os.getenv("ITEM_ID_MIN", "").strip()
ITEM_ID_MAX = os.getenv("ITEM_ID_MAX", "").strip()
JPEG_QUALITY = 92


def to_posix_path(path: Path) -> str:
    return path.as_posix()


def normalize_value(value: Any, key: str | None = None) -> Any:
    if isinstance(value, dict):
        return {k: normalize_value(v, k) for k, v in value.items()}
    if isinstance(value, list):
        return [normalize_value(v, key) for v in value]
    if isinstance(value, str):
        if key and "path" in key.lower():
            return value.replace("\\", "/")
        return value
    return value


def discover_item_ids(raw_dir: Path) -> list[str]:
    pdf_ids = {path.stem for path in raw_dir.glob("*.pdf")}
    json_ids = {path.stem for path in raw_dir.glob("*.json")}
    return sorted(pdf_ids & json_ids)


def filter_item_ids(item_ids: list[str]) -> list[str]:
    filtered = item_ids
    if ITEM_ID_MIN:
        filtered = [item_id for item_id in filtered if item_id >= ITEM_ID_MIN]
    if ITEM_ID_MAX:
        filtered = [item_id for item_id in filtered if item_id <= ITEM_ID_MAX]
    if MAX_ITEMS > 0:
        filtered = filtered[:MAX_ITEMS]
    return filtered


def render_page_images(pdf_path: Path, item_dir: Path, item_id: str) -> list[dict[str, Any]]:
    item_dir.mkdir(parents=True, exist_ok=True)
    images: list[dict[str, Any]] = []

    with fitz.open(pdf_path) as doc:
        log.info("%s: %s pages", item_id, doc.page_count)

        for page_index in range(doc.page_count):
            page_number = page_index + 1
            filename = f"page_{page_number:04d}.jpg"
            image_path = item_dir / filename

            if image_path.exists():
                with Image.open(image_path) as image:
                    width, height = image.size
            else:
                page = doc.load_page(page_index)
                pixmap = page.get_pixmap(dpi=200)
                image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)

                width, height = image.size
                scale = PAGE_IMAGE_LONG_EDGE / max(width, height)
                if scale < 1.0:
                    image = image.resize(
                        (max(1, int(width * scale)), max(1, int(height * scale))),
                        Image.LANCZOS,
                    )
                    width, height = image.size

                image.save(image_path, "JPEG", quality=JPEG_QUALITY)
                log.info("%s: page %s -> %sx%s", item_id, page_number, width, height)

            images.append(
                {
                    "page_number": page_number,
                    "filename": filename,
                    "filepath": to_posix_path(image_path),
                    "width": width,
                    "height": height,
                }
            )

    return images


def build_normalized_metadata(
    item_id: str,
    raw_pdf_path: Path,
    raw_json_path: Path,
    page_images: list[dict[str, Any]],
) -> dict[str, Any]:
    raw_data = json.loads(raw_json_path.read_text(encoding="utf-8"))
    normalized = normalize_value(raw_data)

    normalized["item_id"] = item_id
    normalized["pdf_path"] = to_posix_path(raw_pdf_path)
    normalized["page_images"] = page_images

    return normalized


def process_item(raw_dir: Path, staged_dir: Path, item_id: str) -> None:
    raw_pdf_path = raw_dir / f"{item_id}.pdf"
    raw_json_path = raw_dir / f"{item_id}.json"
    staged_json_path = staged_dir / f"{item_id}.json"
    item_dir = staged_dir / item_id

    if not raw_pdf_path.exists() or not raw_json_path.exists():
        log.warning("%s: missing PDF or JSON, skipping.", item_id)
        return

    page_images = render_page_images(raw_pdf_path, item_dir, item_id)
    normalized = build_normalized_metadata(item_id, raw_pdf_path, raw_json_path, page_images)

    staged_dir.mkdir(parents=True, exist_ok=True)
    staged_json_path.write_text(
        json.dumps(normalized, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    log.info("%s: wrote %s page images and normalized metadata.", item_id, len(page_images))


def main() -> None:
    if not RAW_DATA_DIR.exists():
        raise FileNotFoundError(f"Raw data directory not found: {RAW_DATA_DIR}")

    item_ids = filter_item_ids(discover_item_ids(RAW_DATA_DIR))

    log.info("Found %s matched raw items in %s", len(item_ids), RAW_DATA_DIR)

    for index, item_id in enumerate(item_ids, start=1):
        log.info("[%s/%s] Processing %s", index, len(item_ids), item_id)
        process_item(RAW_DATA_DIR, STAGED_DATA_DIR, item_id)

    log.info("Preprocessing complete.")


if __name__ == "__main__":
    main()
