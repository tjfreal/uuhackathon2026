
import os
import json
from dotenv import load_dotenv
import fitz  # PyMuPDF
import layoutparser as lp
import pytesseract
from PIL import Image

# Load environment variables
load_dotenv()
STAGING_DATA_DIR = os.getenv("STAGING_DATA_DIR")

if not os.path.exists(STAGING_DATA_DIR):
    print(f"Error: Staging directory '{STAGING_DATA_DIR}' not found.")
    exit()

def extract_existing_ocr(page):
    try:
        return page.get_text("text").strip()
    except Exception as e:
        print(f"Warning: Failed to extract existing OCR: {e}")
        return ""

def detect_text_blocks_with_layoutparser(image_path):
    # Placeholder for LayoutParser model call
    return []

def detect_sketch_regions(image_path):
    # Placeholder for future sketch region detection approach
    return []

print("Starting restructured metadata enrichment pipeline...")

for filename in os.listdir(STAGING_DATA_DIR):
    if not filename.endswith(".pdf"):
        continue

    item_id = os.path.splitext(filename)[0]
    pdf_path = os.path.join(STAGING_DATA_DIR, filename)
    json_path = os.path.join(STAGING_DATA_DIR, f"{item_id}.json")
    item_dir = os.path.join(STAGING_DATA_DIR, item_id)

    if not os.path.exists(json_path):
        print(f"No JSON metadata found for {item_id}. Skipping.")
        continue

    os.makedirs(item_dir, exist_ok=True)

    with open(json_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    if "enriched_data" not in metadata:
        metadata["enriched_data"] = {"pages": []}
    else:
        metadata["enriched_data"]["pages"].clear()

    doc = fitz.open(pdf_path)
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap(dpi=300)
        image_path = os.path.join(item_dir, f"page_{page_num+1:04d}.jpg")
        pix.save(image_path)

        existing_ocr = extract_existing_ocr(page)

        layout_blocks = detect_text_blocks_with_layoutparser(image_path)
        sketch_regions = detect_sketch_regions(image_path)

        metadata["enriched_data"]["pages"].append({
            "page_number": page_num + 1,
            "existing_ocr": existing_ocr,
            "layout_blocks": layout_blocks,
            "sketch_regions": sketch_regions,
            "image_path": image_path
        })

    doc.close()

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

print("Enrichment pipeline complete.")
