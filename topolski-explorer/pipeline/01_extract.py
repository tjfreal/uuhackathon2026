"""
01_extract.py — Topolski Collection Downloader

Downloads PDFs and metadata from the public UU digital collections site.
Adapted from pipeline/reference/extract_data.py.

Idempotent: skips items where the PDF already exists.
Respects MAX_ITEMS env var for partial runs.

Output per item in STAGED_DATA_DIR:
  {item_id}.pdf
  {item_id}.json   (metadata + item_url)
"""

import os
import json
import time
import logging
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

ITEM_DETAILS_BASE_URL = os.getenv("ITEM_DETAILS_BASE_URL")
COLLECTION_SEARCH_URL = os.getenv("COLLECTION_SEARCH_URL")
COLLECTION_FACET_SETNAME = os.getenv("COLLECTION_FACET_SETNAME")
STAGED_DATA_DIR = os.getenv("STAGED_DATA_DIR", "data/staged")
MAX_ITEMS = int(os.getenv("MAX_ITEMS")) if os.getenv("MAX_ITEMS") else None
REQUEST_DELAY = 1.0  # seconds between requests

parsed = urlparse(ITEM_DETAILS_BASE_URL)
BASE_SITE_URL = f"{parsed.scheme}://{parsed.netloc}"

os.makedirs(STAGED_DATA_DIR, exist_ok=True)

# --- Agent: implement get_item_urls_from_search_page, extract_item_data_and_download_pdf ---
# Reference implementation in pipeline/reference/extract_data.py
# Key changes from reference:
#   - Use STAGED_DATA_DIR (not hardcoded 'staged_data')
#   - Respect MAX_ITEMS
#   - Skip items where PDF already exists
#   - Log with logging module, not print()

def get_item_urls_from_search_page(page_url: str) -> list[str]:
    """Return unique item detail URLs from one search results page."""
    raise NotImplementedError("Agent A: implement this")


def extract_item_metadata(item_url: str) -> dict | None:
    """
    Fetch item detail page. Return dict with:
      item_id, item_url, pdf_download_url, metadata (dict of table fields)
    Return None on failure.
    """
    raise NotImplementedError("Agent A: implement this")


def download_pdf(pdf_url: str, dest_path: str) -> bool:
    """Stream-download PDF to dest_path. Return True on success."""
    raise NotImplementedError("Agent A: implement this")


def main():
    all_urls = []
    page = 1
    log.info("Scanning collection search pages...")

    while True:
        page_url = f"{COLLECTION_SEARCH_URL}{COLLECTION_FACET_SETNAME}&page={page}"
        urls = get_item_urls_from_search_page(page_url)
        new_urls = [u for u in urls if u not in all_urls and "id=" in u]
        if not new_urls:
            log.info(f"No new URLs on page {page}, stopping.")
            break
        all_urls.extend(new_urls)
        log.info(f"Page {page}: +{len(new_urls)} URLs, total {len(all_urls)}")
        if MAX_ITEMS and len(all_urls) >= MAX_ITEMS:
            all_urls = all_urls[:MAX_ITEMS]
            log.info(f"MAX_ITEMS={MAX_ITEMS} reached, stopping search traversal.")
            break
        page += 1
        time.sleep(REQUEST_DELAY)

    log.info(f"Processing {len(all_urls)} items...")
    processed = 0
    for item_url in all_urls:
        item_data = extract_item_metadata(item_url)
        if not item_data:
            continue

        item_id = item_data["item_id"]
        pdf_path = os.path.join(STAGED_DATA_DIR, f"{item_id}.pdf")
        json_path = os.path.join(STAGED_DATA_DIR, f"{item_id}.json")

        if os.path.exists(pdf_path):
            log.info(f"{item_id}: PDF exists, skipping download.")
        else:
            ok = download_pdf(item_data["pdf_download_url"], pdf_path)
            if not ok:
                log.warning(f"{item_id}: PDF download failed, skipping.")
                continue

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(item_data, f, indent=2, ensure_ascii=False)

        processed += 1
        log.info(f"{item_id}: done ({processed}/{len(all_urls)})")
        time.sleep(REQUEST_DELAY)

    log.info(f"Extraction complete. {processed} items processed.")


if __name__ == "__main__":
    main()
