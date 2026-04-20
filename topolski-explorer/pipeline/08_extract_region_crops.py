"""
08_extract_region_crops.py — Extract Provisional Region Crops

Reads the staged corpus plus the layout manifest and generates local region crop
images for layout-aware experiments. The resulting crops are explicitly marked
as provisional because the current layout manifest does not contain measured
geometry.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from PIL import Image

load_dotenv()

STAGED_DATA_DIR = Path(os.getenv("STAGED_DATA_DIR", "data/staged"))
LAYOUT_MANIFEST_PATH = Path(os.getenv("LAYOUT_MANIFEST_PATH", "data/layout_manifest.json"))
REGION_OUTPUT_DIR = Path(os.getenv("REGION_OUTPUT_DIR", "data/regions"))
REGION_CROP_MANIFEST_PATH = Path(
    os.getenv("REGION_CROP_MANIFEST_PATH", "data/region_crop_manifest.json")
)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def normalize_relative_path(path: str) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return candidate


def staged_image_map() -> dict[tuple[str, int], dict[str, Any]]:
    image_index: dict[tuple[str, int], dict[str, Any]] = {}
    if not STAGED_DATA_DIR.exists():
        return image_index

    for metadata_path in sorted(STAGED_DATA_DIR.glob("*.json")):
        metadata = load_json(metadata_path)
        item_id = str(metadata.get("item_id") or metadata_path.stem)
        for page in metadata.get("page_images", []):
            try:
                page_number = int(page.get("page_number"))
            except (TypeError, ValueError):
                continue
            image_index[(item_id, page_number)] = page
    return image_index


def resolve_image_path(page_record: dict[str, Any]) -> Path:
    raw_path = str(page_record.get("filepath") or page_record.get("image_path") or "").strip()
    if not raw_path:
        raise FileNotFoundError("No source image path found in staged metadata.")

    candidate = normalize_relative_path(raw_path)
    if candidate.is_absolute() and candidate.exists():
        return candidate

    repo_relative = Path.cwd() / candidate
    if repo_relative.exists():
        return repo_relative

    staged_relative = STAGED_DATA_DIR.parent / candidate
    if staged_relative.exists():
        return staged_relative

    raise FileNotFoundError(f"Could not resolve source image path: {raw_path}")


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def bounds_to_box(bounds: dict[str, Any], width: int, height: int) -> dict[str, Any]:
    x = clamp(float(bounds.get("x", 0.0)), 0.0, 1.0)
    y = clamp(float(bounds.get("y", 0.0)), 0.0, 1.0)
    w = clamp(float(bounds.get("w", 1.0)), 0.0, 1.0)
    h = clamp(float(bounds.get("h", 1.0)), 0.0, 1.0)

    left = int(round(x * width))
    top = int(round(y * height))
    right = int(round(clamp(x + w, 0.0, 1.0) * width))
    bottom = int(round(clamp(y + h, 0.0, 1.0) * height))

    if right <= left:
        right = min(width, left + 1)
    if bottom <= top:
        bottom = min(height, top + 1)

    return {
        "left": left,
        "top": top,
        "right": right,
        "bottom": bottom,
        "pixel_width": right - left,
        "pixel_height": bottom - top,
    }


def crop_filename(page_number: int, region_index: int, region_type: str) -> str:
    safe_region_type = region_type.lower().replace(" ", "_")
    return f"page_{page_number:04d}_region_{region_index:02d}_{safe_region_type}_PROVISIONAL.jpg"


def extract_region_crops() -> dict[str, Any]:
    layout_manifest = load_json(LAYOUT_MANIFEST_PATH)
    page_images = staged_image_map()

    manifest_items: dict[str, Any] = {}
    total_pages = 0
    total_regions = 0
    total_crops = 0

    for item_id, item_data in sorted(layout_manifest.get("items", {}).items()):
        item_output_dir = REGION_OUTPUT_DIR / str(item_id)
        item_output_dir.mkdir(parents=True, exist_ok=True)

        item_pages: list[dict[str, Any]] = []
        for page in item_data.get("pages", []):
            try:
                page_number = int(page.get("page_number"))
            except (TypeError, ValueError):
                continue

            source_page = page_images.get((str(item_id), page_number))
            page_entry: dict[str, Any] = {
                "page_number": page_number,
                "layout_confidence": page.get("layout_confidence", "provisional"),
                "notes": list(page.get("notes", [])),
                "regions": [],
            }

            total_pages += 1
            if not source_page:
                page_entry["status"] = "missing_source_image"
                item_pages.append(page_entry)
                continue

            source_image_path = resolve_image_path(source_page)
            with Image.open(source_image_path) as image:
                image = image.convert("RGB")
                width, height = image.size

                for region_index, region in enumerate(page.get("regions", []), start=1):
                    total_regions += 1
                    region_type = str(region.get("region_type", "unknown")).strip() or "unknown"
                    bounds = region.get("bounds", {})
                    crop_box = bounds_to_box(bounds, width, height)
                    output_path = item_output_dir / crop_filename(page_number, region_index, region_type)

                    cropped = image.crop(
                        (
                            crop_box["left"],
                            crop_box["top"],
                            crop_box["right"],
                            crop_box["bottom"],
                        )
                    )
                    cropped.save(output_path, format="JPEG", quality=95)
                    total_crops += 1

                    page_entry["regions"].append(
                        {
                            "region_index": region_index,
                            "region_type": region_type,
                            "provisional_experimental": True,
                            "source_image_path": source_image_path.as_posix(),
                            "crop_path": output_path.as_posix(),
                            "source_image_size": {"width": width, "height": height},
                            "pixel_bounds": crop_box,
                            "provisional_bounds": {
                                "basis": "layout_manifest_fractional_guess",
                                **bounds,
                            },
                            "evidence": region.get("evidence", {}),
                        }
                    )

            page_entry["status"] = "cropped"
            item_pages.append(page_entry)

        manifest_items[str(item_id)] = {
            "page_count": len(item_pages),
            "pages": item_pages,
        }

    return {
        "schema_version": "2026-04-19-region-crop-manifest-v1",
        "source_layout_manifest": LAYOUT_MANIFEST_PATH.as_posix(),
        "output_root": REGION_OUTPUT_DIR.as_posix(),
        "provisional_experimental": True,
        "notes": [
            "These region crops are generated from provisional layout bounds.",
            "Crop geometry is experimental and should not be treated as measured page segmentation.",
            "Use this output to test region-aware extraction strategies, not to claim precise boundaries.",
        ],
        "corpus_summary": {
            "item_count": len(manifest_items),
            "page_count": total_pages,
            "region_count": total_regions,
            "crop_count": total_crops,
        },
        "items": manifest_items,
    }


def main() -> None:
    manifest = extract_region_crops()
    write_json(REGION_CROP_MANIFEST_PATH, manifest)
    print(f"Wrote region crop manifest to {REGION_CROP_MANIFEST_PATH}")
    print(
        f"Items: {manifest['corpus_summary']['item_count']} "
        f"Pages: {manifest['corpus_summary']['page_count']} "
        f"Regions: {manifest['corpus_summary']['region_count']} "
        f"Crops: {manifest['corpus_summary']['crop_count']}"
    )


if __name__ == "__main__":
    main()
